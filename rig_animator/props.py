"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB

props.py
--------
Blender PropertyGroups that hold the "scene setup" data. This is the
equivalent of what the Unity package configures in the Inspector on
ProceduralAnimator / ClipAnimationPlayer / SimpleObjectAnimator components:
named IK chains, named look-at bones, named clips (Actions), and named
transform targets, all living on the rig/root object under `obj.rig_animator`.
"""

import bpy
from bpy.props import (
    StringProperty, FloatProperty, IntProperty, PointerProperty,
    CollectionProperty, EnumProperty,
)


class RIGANIM_IKChain(bpy.types.PropertyGroup):
    """Two-bone IK chain: root -> mid -> tip (e.g. upper arm -> forearm -> hand)."""
    name: StringProperty(name="Name", description="Command target name, e.g. 'RightArm'")
    root_bone: StringProperty(name="Root Bone")
    mid_bone: StringProperty(name="Mid Bone")
    tip_bone: StringProperty(name="Tip Bone")
    weight: FloatProperty(name="Weight", default=1.0, min=0.0, max=1.0)
    # Live playback state (active/current target/blend speed) is NOT stored
    # here -- Blender PropertyGroup instances don't reliably hold plain
    # Python attributes, so procedural.py keeps a module-level runtime dict
    # keyed by (object name, chain name) instead. See procedural.py.


class RIGANIM_LookAtBone(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", description="Command target name, e.g. 'Head'")
    bone: StringProperty(name="Bone")
    weight: FloatProperty(name="Weight", default=1.0, min=0.0, max=1.0)
    # See note above -- runtime state lives in procedural.py's runtime dict.


class RIGANIM_ClipDef(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", description="Command target name, e.g. 'Wave'")
    action: PointerProperty(name="Action", type=bpy.types.Action)


class RIGANIM_TransformTarget(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", description="Command target name, e.g. 'Door'")
    target: PointerProperty(name="Object", type=bpy.types.Object)


class RigAnimatorObjectSettings(bpy.types.PropertyGroup):
    """Attached to any Object as `obj.rig_animator`. Groups everything the
    three layers need, same as the three MonoBehaviours in the Unity
    package living side by side on one rig root."""

    ik_chains: CollectionProperty(type=RIGANIM_IKChain)
    ik_chains_index: IntProperty(default=0)

    lookat_bones: CollectionProperty(type=RIGANIM_LookAtBone)
    lookat_bones_index: IntProperty(default=0)

    clips: CollectionProperty(type=RIGANIM_ClipDef)
    clips_index: IntProperty(default=0)
    default_fade_seconds: FloatProperty(name="Default Fade (s)", default=0.25, min=0.0)

    transform_targets: CollectionProperty(type=RIGANIM_TransformTarget)
    transform_targets_index: IntProperty(default=0)


classes = (
    RIGANIM_IKChain,
    RIGANIM_LookAtBone,
    RIGANIM_ClipDef,
    RIGANIM_TransformTarget,
    RigAnimatorObjectSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.rig_animator = PointerProperty(type=RigAnimatorObjectSettings)


def unregister():
    del bpy.types.Object.rig_animator
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
