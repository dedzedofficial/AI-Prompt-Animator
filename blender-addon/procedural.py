"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB

procedural.py
-------------
Blender port of Runtime/Procedural/ProceduralAnimator.cs. Drives pose bones
directly every tick: an analytic two-bone IK reach (law-of-cosines, same
approach as the Unity version) and a smoothed look-at. No Actions/NLA
involved -- this is for runtime-computed motion.

Supported actions (identical contract to the Unity version):
    "ik_reach"  target=<chain name>  floatParams: x, y, z (world target), duration, weight
    "look_at"   target=<bone name>   floatParams: x, y, z (world target), speed, weight
    "stop"      target=<chain or bone name>

Bones are assumed to point down local +Y (Blender's default bone
convention) for the look-at solve. Runtime playback state (active flag,
current target, blend speed) is kept in a module-level dict rather than on
the PropertyGroup, since PropertyGroup instances don't reliably hold plain
Python attributes.
"""

import math
import bpy
from mathutils import Vector, Quaternion
from . import core

# runtime[obj_name] = {
#   'ik': {chain_name: {'active','target','weight','blend_speed','current_weight'}},
#   'lookat': {bone_name: {'active','target','weight','turn_speed'}},
# }
_runtime = {}


def _state(obj):
    return _runtime.setdefault(obj.name, {'ik': {}, 'lookat': {}})


def _find_chain(obj, name):
    settings = getattr(obj, "rig_animator", None)
    if not settings:
        return None
    for c in settings.ik_chains:
        if c.name == name:
            return c
    return None


def _find_lookat(obj, name):
    settings = getattr(obj, "rig_animator", None)
    if not settings:
        return None
    for l in settings.lookat_bones:
        if l.name == name:
            return l
    return None


def can_execute(obj, command: 'core.AnimationCommand') -> bool:
    if command.action == 'ik_reach':
        return _find_chain(obj, command.target) is not None
    if command.action == 'look_at':
        return _find_lookat(obj, command.target) is not None
    if command.action == 'stop':
        return _find_chain(obj, command.target) is not None or _find_lookat(obj, command.target) is not None
    return False


def execute(context, obj, command: 'core.AnimationCommand') -> None:
    st = _state(obj)

    if command.action == 'ik_reach':
        chain = _find_chain(obj, command.target)
        if chain is None:
            return
        duration = max(0.01, command.get_float('duration', 0.25))
        st['ik'][command.target] = {
            'active': True,
            'target': Vector((command.get_float('x'), command.get_float('y'), command.get_float('z'))),
            'weight': max(0.0, min(1.0, command.get_float('weight', 1.0))),
            'blend_speed': 1.0 / duration,
            'current_weight': st['ik'].get(command.target, {}).get('current_weight', 0.0),
        }

    elif command.action == 'look_at':
        look = _find_lookat(obj, command.target)
        if look is None:
            return
        st['lookat'][command.target] = {
            'active': True,
            'target': Vector((command.get_float('x'), command.get_float('y'), command.get_float('z'))),
            'weight': max(0.0, min(1.0, command.get_float('weight', 1.0))),
            'turn_speed': command.get_float('speed', 180.0),
        }

    elif command.action == 'stop':
        if command.target in st['ik']:
            st['ik'][command.target]['active'] = False
        if command.target in st['lookat']:
            st['lookat'][command.target]['active'] = False


def _move_towards(current, target, max_delta):
    if abs(target - current) <= max_delta:
        return target
    return current + math.copysign(max_delta, target - current)


def _solve_two_bone_ik(root_pb, mid_pb, tip_pb, target_pos_world, weight):
    """Classic analytic two-bone IK (law of cosines), ported from
    ProceduralAnimator.SolveTwoBoneIK. Operates in world (armature-object)
    space and writes back via pose_bone.matrix, which Blender re-decomposes
    into matrix_basis automatically."""
    root_head = root_pb.matrix.translation
    mid_head = mid_pb.matrix.translation
    tip_head = tip_pb.matrix.translation

    upper_len = (mid_head - root_head).length
    lower_len = (tip_head - mid_head).length
    max_reach = upper_len + lower_len
    if upper_len < 1e-6 or lower_len < 1e-6:
        return

    to_target = target_pos_world - root_head
    target_dist = max(0.0001, min(to_target.length, max_reach - 0.0001))

    cos_root = max(-1.0, min(1.0, (upper_len ** 2 + target_dist ** 2 - lower_len ** 2) / (2 * upper_len * target_dist)))
    root_angle = math.acos(cos_root)

    cos_mid = max(-1.0, min(1.0, (upper_len ** 2 + lower_len ** 2 - target_dist ** 2) / (2 * upper_len * lower_len)))
    mid_angle = math.acos(cos_mid)

    to_target_n = to_target.normalized()
    up_ref = Vector((0.0, 0.0, 1.0))
    pole_axis = to_target_n.cross(up_ref)
    if pole_axis.length < 1e-4:
        pole_axis = Vector((1.0, 0.0, 0.0))
    else:
        pole_axis.normalize()

    # Bone-forward is local +Y (Blender convention). Build a "look rotation"
    # pointing +Y at the target, then swing root/mid around the pole axis
    # by the law-of-cosines angles -- same construction as the C# version's
    # Quaternion.LookRotation + AngleAxis composition.
    root_look = to_target_n.to_track_quat('Y', 'Z')
    root_target_rot = Quaternion(pole_axis, -root_angle) @ root_look
    mid_target_rot = Quaternion(pole_axis, math.pi - mid_angle) @ root_look

    root_current_rot = root_pb.matrix.to_quaternion()
    mid_current_rot = mid_pb.matrix.to_quaternion()

    root_final = root_current_rot.slerp(root_target_rot, weight)
    mid_final = mid_current_rot.slerp(mid_target_rot, weight)

    root_mat = root_pb.matrix.copy()
    root_mat = root_final.to_matrix().to_4x4()
    root_mat.translation = root_pb.matrix.translation
    root_pb.matrix = root_mat

    bpy.context.view_layer.update()

    mid_mat = mid_final.to_matrix().to_4x4()
    mid_mat.translation = mid_pb.matrix.translation
    mid_pb.matrix = mid_mat


def _resolve_pose_bones(obj, chain):
    if obj.type != 'ARMATURE' or obj.pose is None:
        return None, None, None
    root_pb = obj.pose.bones.get(chain.root_bone)
    mid_pb = obj.pose.bones.get(chain.mid_bone)
    tip_pb = obj.pose.bones.get(chain.tip_bone)
    return root_pb, mid_pb, tip_pb


def tick(context, dt: float) -> None:
    """Called every runtime tick (see runtime.py) for every object that has
    active IK chains or look-at bones -- equivalent of ProceduralAnimator's
    per-frame LateUpdate()."""
    for obj_name, st in list(_runtime.items()):
        obj = bpy.data.objects.get(obj_name)
        if obj is None or obj.type != 'ARMATURE':
            continue
        settings = getattr(obj, "rig_animator", None)
        if settings is None:
            continue

        world_to_local = obj.matrix_world.inverted()

        for chain_name, ik_state in st['ik'].items():
            if not ik_state['active']:
                continue
            chain = _find_chain(obj, chain_name)
            if chain is None:
                continue
            root_pb, mid_pb, tip_pb = _resolve_pose_bones(obj, chain)
            if root_pb is None or mid_pb is None or tip_pb is None:
                continue

            ik_state['current_weight'] = _move_towards(
                ik_state['current_weight'], ik_state['weight'], ik_state['blend_speed'] * dt)
            if ik_state['current_weight'] <= 0.0:
                continue

            local_target = world_to_local @ ik_state['target']
            _solve_two_bone_ik(root_pb, mid_pb, tip_pb, local_target, ik_state['current_weight'])

        for bone_name, look_state in st['lookat'].items():
            if not look_state['active']:
                continue
            look = _find_lookat(obj, bone_name)
            if look is None:
                continue
            pb = obj.pose.bones.get(look.bone) if obj.pose else None
            if pb is None:
                continue

            local_target = world_to_local @ look_state['target']
            direction = local_target - pb.matrix.translation
            if direction.length < 0.01:
                continue

            desired = direction.normalized().to_track_quat('Y', 'Z')
            current = pb.matrix.to_quaternion()
            desired_blended = current.slerp(desired, look_state['weight'])

            max_step = math.radians(look_state['turn_speed'] * dt)
            angle = current.rotation_difference(desired_blended).angle
            t = 1.0 if angle <= 1e-6 else min(1.0, max_step / angle)
            stepped = current.slerp(desired_blended, t)

            mat = stepped.to_matrix().to_4x4()
            mat.translation = pb.matrix.translation
            pb.matrix = mat

        bpy.context.view_layer.update()


def clear_runtime_for_object(obj_name: str) -> None:
    _runtime.pop(obj_name, None)


def clear_all_runtime() -> None:
    _runtime.clear()
