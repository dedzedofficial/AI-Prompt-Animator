"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB

operators.py
------------
List-management operators for the four named-target collections (mirrors
adding rows to the List<> fields in the Unity Inspector), the runtime
start/stop toggle, and a manual "send one command" tester for driving the
system from code/UI without the AI, same as the Unity README's
controller.Execute(new AnimationCommand{...}) example.
"""

import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty
from . import core, runtime


def _settings(context):
    obj = context.active_object
    if obj is None:
        return None
    return getattr(obj, "rig_animator", None)


class RIGANIM_OT_add_ik_chain(bpy.types.Operator):
    bl_idname = "rig_animator.add_ik_chain"
    bl_label = "Add IK Chain"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            self.report({'ERROR'}, "Select an armature first.")
            return {'CANCELLED'}
        item = settings.ik_chains.add()
        item.name = f"Chain{len(settings.ik_chains)}"
        return {'FINISHED'}


class RIGANIM_OT_remove_ik_chain(bpy.types.Operator):
    bl_idname = "rig_animator.remove_ik_chain"
    bl_label = "Remove IK Chain"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings and 0 <= settings.ik_chains_index < len(settings.ik_chains):
            settings.ik_chains.remove(settings.ik_chains_index)
            settings.ik_chains_index = max(0, settings.ik_chains_index - 1)
        return {'FINISHED'}


class RIGANIM_OT_add_lookat_bone(bpy.types.Operator):
    bl_idname = "rig_animator.add_lookat_bone"
    bl_label = "Add Look-At Bone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            self.report({'ERROR'}, "Select an armature first.")
            return {'CANCELLED'}
        item = settings.lookat_bones.add()
        item.name = f"LookAt{len(settings.lookat_bones)}"
        return {'FINISHED'}


class RIGANIM_OT_remove_lookat_bone(bpy.types.Operator):
    bl_idname = "rig_animator.remove_lookat_bone"
    bl_label = "Remove Look-At Bone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings and 0 <= settings.lookat_bones_index < len(settings.lookat_bones):
            settings.lookat_bones.remove(settings.lookat_bones_index)
            settings.lookat_bones_index = max(0, settings.lookat_bones_index - 1)
        return {'FINISHED'}


class RIGANIM_OT_add_clip(bpy.types.Operator):
    bl_idname = "rig_animator.add_clip"
    bl_label = "Add Clip"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            self.report({'ERROR'}, "Select an object first.")
            return {'CANCELLED'}
        item = settings.clips.add()
        item.name = f"Clip{len(settings.clips)}"
        return {'FINISHED'}


class RIGANIM_OT_remove_clip(bpy.types.Operator):
    bl_idname = "rig_animator.remove_clip"
    bl_label = "Remove Clip"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings and 0 <= settings.clips_index < len(settings.clips):
            settings.clips.remove(settings.clips_index)
            settings.clips_index = max(0, settings.clips_index - 1)
        return {'FINISHED'}


class RIGANIM_OT_add_transform_target(bpy.types.Operator):
    bl_idname = "rig_animator.add_transform_target"
    bl_label = "Add Transform Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            self.report({'ERROR'}, "Select an object first.")
            return {'CANCELLED'}
        item = settings.transform_targets.add()
        item.name = f"Target{len(settings.transform_targets)}"
        return {'FINISHED'}


class RIGANIM_OT_remove_transform_target(bpy.types.Operator):
    bl_idname = "rig_animator.remove_transform_target"
    bl_label = "Remove Transform Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = _settings(context)
        if settings and 0 <= settings.transform_targets_index < len(settings.transform_targets):
            settings.transform_targets.remove(settings.transform_targets_index)
            settings.transform_targets_index = max(0, settings.transform_targets_index - 1)
        return {'FINISHED'}


class RIGANIM_OT_toggle_runtime(bpy.types.Operator):
    """Starts/stops the tick loop that drives IK/look-at/clip-fade/tweens
    live -- Unity does this automatically every frame; Blender needs it
    switched on."""
    bl_idname = "rig_animator.toggle_runtime"
    bl_label = "Toggle Rig Animator Runtime"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if runtime.is_running():
            runtime.stop()
            self.report({'INFO'}, "Rig Animator: runtime stopped.")
        else:
            runtime.start()
            self.report({'INFO'}, "Rig Animator: runtime started.")
        return {'FINISHED'}


class RIGANIM_OT_execute_test_command(bpy.types.Operator):
    """Manually fires a single AnimationCommand at the active object, for
    testing a layer without going through the AI -- equivalent of the
    README's controller.Execute(new AnimationCommand{...}) example."""
    bl_idname = "rig_animator.execute_test_command"
    bl_label = "Execute Command"
    bl_options = {'REGISTER', 'UNDO'}

    layer: EnumProperty(name="Layer", items=core.LAYER_ITEMS, default=core.LAYER_SIMPLE_TRANSFORM)
    target: StringProperty(name="Target")
    action: StringProperty(name="Action", default="move_to")
    x: FloatProperty(name="X", default=0.0)
    y: FloatProperty(name="Y", default=0.0)
    z: FloatProperty(name="Z", default=0.0)
    duration: FloatProperty(name="Duration", default=0.5, min=0.0)

    def execute(self, context):
        obj = context.scene.rig_animator_target or context.active_object
        if obj is None:
            self.report({'ERROR'}, "No target object.")
            return {'CANCELLED'}

        command = core.AnimationCommand(
            layer=self.layer, target=self.target, action=self.action,
            float_params={'x': self.x, 'y': self.y, 'z': self.z, 'duration': self.duration},
            string_params={},
        )
        if not runtime.is_running():
            runtime.start()
        ok = core.execute(context, obj, command)
        if not ok:
            self.report({'WARNING'}, "No executor could handle that command -- check target name.")
        return {'FINISHED'}


classes = (
    RIGANIM_OT_add_ik_chain,
    RIGANIM_OT_remove_ik_chain,
    RIGANIM_OT_add_lookat_bone,
    RIGANIM_OT_remove_lookat_bone,
    RIGANIM_OT_add_clip,
    RIGANIM_OT_remove_clip,
    RIGANIM_OT_add_transform_target,
    RIGANIM_OT_remove_transform_target,
    RIGANIM_OT_toggle_runtime,
    RIGANIM_OT_execute_test_command,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rig_animator_target = bpy.props.PointerProperty(
        name="Target", type=bpy.types.Object,
        description="Object/armature the panel's test controls and AI prompts drive. "
                    "Falls back to the active object if left empty.")
    bpy.types.Scene.rig_animator_prompt = StringProperty(
        name="Prompt", default="Raise the right hand and look at the player.",
        description="Natural-language prompt sent to the configured AI provider.")


def unregister():
    del bpy.types.Scene.rig_animator_prompt
    del bpy.types.Scene.rig_animator_target
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
