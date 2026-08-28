"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB

object_animator.py
-------------------
Blender port of Runtime/ObjectAnimator/SimpleObjectAnimator.cs and
EasingFunctions.cs. Transform-level tweening for plain objects -- no rig,
no clips. Named targets are registered on obj.rig_animator.transform_targets
and driven by name, same as the Unity version.

Supported actions (identical contract to the Unity version):
    "move_to"    target=<name>  floatParams: x,y,z, duration   stringParams: ease, space ("world"/"local")
    "rotate_to"  target=<name>  floatParams: x,y,z, duration   stringParams: ease (euler degrees)
    "scale_to"   target=<name>  floatParams: x,y,z, duration   stringParams: ease
    "stop"       target=<name or "*">
"""

import math
import bpy
from mathutils import Vector
from . import core

# runtime[obj_name] = { transform_name: [ {kind, from, to, duration, elapsed, ease, world_space}, ... ] }
_runtime = {}


def _find_target(obj, name):
    settings = getattr(obj, "rig_animator", None)
    if not settings:
        return None, None
    for t in settings.transform_targets:
        if t.name == name:
            return t.name, t.target
    return None, None


def can_execute(obj, command: 'core.AnimationCommand') -> bool:
    if command.action == 'stop':
        return True  # "*" is always valid, same as the Unity version
    _, target = _find_target(obj, command.target)
    return target is not None


def execute(context, obj, command: 'core.AnimationCommand') -> None:
    if command.action == 'move_to':
        _start_tween(obj, command, 'move')
    elif command.action == 'rotate_to':
        _start_tween(obj, command, 'rotate')
    elif command.action == 'scale_to':
        _start_tween(obj, command, 'scale')
    elif command.action == 'stop':
        _stop(obj, command.target)


def _start_tween(obj, command, kind):
    name, target = _find_target(obj, command.target)
    if target is None:
        print(f"Rig Animator: no target registered under name '{command.target}' on '{obj.name}'.")
        return

    world_space = command.get_string('space', 'world') != 'local'
    to = Vector((command.get_float('x'), command.get_float('y'), command.get_float('z')))
    duration = max(0.0001, command.get_float('duration', 0.5))
    ease = command.get_string('ease', 'EaseInOutQuad')

    if kind == 'move':
        frm = Vector(target.matrix_world.translation) if world_space else Vector(target.location)
    elif kind == 'rotate':
        frm = Vector(target.matrix_world.to_euler()) if world_space else Vector(target.rotation_euler)
    else:  # scale
        frm = Vector(target.scale)

    tween = {
        'kind': kind, 'from': frm, 'to': to, 'duration': duration,
        'elapsed': 0.0, 'ease': ease, 'world_space': world_space,
    }

    per_obj = _runtime.setdefault(obj.name, {})
    tweens = per_obj.setdefault(command.target, [])
    # Only one active tween per kind per target -- a new move_to cleanly
    # replaces an in-flight one instead of fighting it (same as Unity).
    per_obj[command.target] = [t for t in tweens if t['kind'] != kind] + [tween]


def _stop(obj, target_name):
    per_obj = _runtime.get(obj.name)
    if per_obj is None:
        return
    if target_name == '*':
        per_obj.clear()
    else:
        per_obj.pop(target_name, None)


def ease_evaluate(ease_name: str, t: float) -> float:
    t = max(0.0, min(1.0, t))
    name = (ease_name or 'Linear').strip()
    if name == 'EaseInQuad':
        return t * t
    if name == 'EaseOutQuad':
        return 1.0 - (1.0 - t) * (1.0 - t)
    if name == 'EaseInOutQuad':
        return 2.0 * t * t if t < 0.5 else 1.0 - ((-2.0 * t + 2.0) ** 2) / 2.0
    if name == 'EaseOutBack':
        c1 = 1.70158
        c3 = c1 + 1.0
        return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2
    if name == 'EaseOutBounce':
        n1, d1 = 7.5625, 2.75
        if t < 1.0 / d1:
            return n1 * t * t
        if t < 2.0 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        if t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        t -= 2.625 / d1
        return n1 * t * t + 0.984375
    return t  # Linear / unrecognized


def tick(context, dt: float) -> None:
    """Equivalent of SimpleObjectAnimator's per-frame Update(): advances
    every active tween and applies the eased value to the target."""
    for obj_name, per_obj in list(_runtime.items()):
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            _runtime.pop(obj_name, None)
            continue

        empty_targets = []
        for target_name, tweens in per_obj.items():
            _, target = _find_target(obj, target_name)
            if target is None:
                empty_targets.append(target_name)
                continue

            remaining = []
            for tw in tweens:
                tw['elapsed'] += dt
                t01 = max(0.0, min(1.0, tw['elapsed'] / tw['duration']))
                eased = ease_evaluate(tw['ease'], t01)
                value = tw['from'].lerp(tw['to'], eased)

                if tw['kind'] == 'move':
                    if tw['world_space']:
                        mat = target.matrix_world.copy()
                        mat.translation = value
                        target.matrix_world = mat
                    else:
                        target.location = value
                elif tw['kind'] == 'rotate':
                    if tw['world_space']:
                        euler = target.matrix_world.to_euler()
                        euler[:] = value
                        loc, _, scale = target.matrix_world.decompose()
                        mat = euler.to_matrix().to_4x4()
                        mat.translation = loc
                        target.matrix_world = mat
                    else:
                        target.rotation_euler = value
                elif tw['kind'] == 'scale':
                    target.scale = value

                if t01 < 1.0:
                    remaining.append(tw)

            if remaining:
                per_obj[target_name] = remaining
            else:
                empty_targets.append(target_name)

        for name in empty_targets:
            per_obj.pop(name, None)

        if not per_obj:
            _runtime.pop(obj_name, None)


def clear_runtime_for_object(obj_name: str) -> None:
    _runtime.pop(obj_name, None)


def clear_all_runtime() -> None:
    _runtime.clear()
