"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB
Discord: https://discord.gg/vCcsnX4HQP

ui.py
-----
3D Viewport sidebar (N-panel), "Rig Animator" tab. Mirrors the Unity
Inspector layout: scene setup (named IK chains / look-at bones / clips /
transform targets) on the active object, AI provider settings + preset
button, and a play-mode-style prompt tester.
"""

import bpy
from . import runtime


class RIGANIM_PT_main(bpy.types.Panel):
    bl_label = "Rig Animator -- v0.1 Beta"
    bl_idname = "RIGANIM_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig Animator"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Created by FISHHWB", icon='INFO')
        row = layout.row()
        row.prop(context.scene, "rig_animator_target")

        row = layout.row()
        if runtime.is_running():
            row.operator("rig_animator.toggle_runtime", text="Stop Runtime", icon='PAUSE')
        else:
            row.operator("rig_animator.toggle_runtime", text="Start Runtime", icon='PLAY')

        layout.label(text="Start the runtime before sending commands so IK,", icon='NONE')
        layout.label(text="look-at, clip fades, and tweens animate live.")


def _target_settings(context):
    obj = context.scene.rig_animator_target or context.active_object
    if obj is None:
        return None, None
    return obj, getattr(obj, "rig_animator", None)


class RIGANIM_PT_procedural(bpy.types.Panel):
    bl_label = "Procedural (IK / Look-At)"
    bl_idname = "RIGANIM_PT_procedural"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig Animator"
    bl_parent_id = "RIGANIM_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj, settings = _target_settings(context)
        if settings is None:
            layout.label(text="Select an object.", icon='ERROR')
            return
        if obj.type != 'ARMATURE':
            layout.label(text="IK chains / look-at need an Armature.", icon='ERROR')

        layout.label(text="IK Chains")
        row = layout.row()
        row.template_list("UI_UL_list", "riganim_ik", settings, "ik_chains",
                           settings, "ik_chains_index", rows=3)
        col = row.column(align=True)
        col.operator("rig_animator.add_ik_chain", text="", icon='ADD')
        col.operator("rig_animator.remove_ik_chain", text="", icon='REMOVE')

        if 0 <= settings.ik_chains_index < len(settings.ik_chains):
            chain = settings.ik_chains[settings.ik_chains_index]
            box = layout.box()
            box.prop(chain, "name")
            if obj.type == 'ARMATURE':
                box.prop_search(chain, "root_bone", obj.pose, "bones", text="Root")
                box.prop_search(chain, "mid_bone", obj.pose, "bones", text="Mid")
                box.prop_search(chain, "tip_bone", obj.pose, "bones", text="Tip")
            box.prop(chain, "weight")

        layout.separator()
        layout.label(text="Look-At Bones")
        row = layout.row()
        row.template_list("UI_UL_list", "riganim_lookat", settings, "lookat_bones",
                           settings, "lookat_bones_index", rows=3)
        col = row.column(align=True)
        col.operator("rig_animator.add_lookat_bone", text="", icon='ADD')
        col.operator("rig_animator.remove_lookat_bone", text="", icon='REMOVE')

        if 0 <= settings.lookat_bones_index < len(settings.lookat_bones):
            look = settings.lookat_bones[settings.lookat_bones_index]
            box = layout.box()
            box.prop(look, "name")
            if obj.type == 'ARMATURE':
                box.prop_search(look, "bone", obj.pose, "bones", text="Bone")
            box.prop(look, "weight")


class RIGANIM_PT_clips(bpy.types.Panel):
    bl_label = "Clip (Actions)"
    bl_idname = "RIGANIM_PT_clips"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig Animator"
    bl_parent_id = "RIGANIM_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj, settings = _target_settings(context)
        if settings is None:
            layout.label(text="Select an object.", icon='ERROR')
            return

        layout.prop(settings, "default_fade_seconds")
        row = layout.row()
        row.template_list("UI_UL_list", "riganim_clips", settings, "clips",
                           settings, "clips_index", rows=3)
        col = row.column(align=True)
        col.operator("rig_animator.add_clip", text="", icon='ADD')
        col.operator("rig_animator.remove_clip", text="", icon='REMOVE')

        if 0 <= settings.clips_index < len(settings.clips):
            clip = settings.clips[settings.clips_index]
            box = layout.box()
            box.prop(clip, "name")
            box.prop(clip, "action")


class RIGANIM_PT_transforms(bpy.types.Panel):
    bl_label = "Simple Transform"
    bl_idname = "RIGANIM_PT_transforms"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig Animator"
    bl_parent_id = "RIGANIM_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj, settings = _target_settings(context)
        if settings is None:
            layout.label(text="Select an object.", icon='ERROR')
            return

        row = layout.row()
        row.template_list("UI_UL_list", "riganim_targets", settings, "transform_targets",
                           settings, "transform_targets_index", rows=3)
        col = row.column(align=True)
        col.operator("rig_animator.add_transform_target", text="", icon='ADD')
        col.operator("rig_animator.remove_transform_target", text="", icon='REMOVE')

        if 0 <= settings.transform_targets_index < len(settings.transform_targets):
            t = settings.transform_targets[settings.transform_targets_index]
            box = layout.box()
            box.prop(t, "name")
            box.prop(t, "target")


class RIGANIM_PT_ai(bpy.types.Panel):
    bl_label = "AI Provider (any vendor)"
    bl_idname = "RIGANIM_PT_ai"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig Animator"
    bl_parent_id = "RIGANIM_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.rig_animator_ai

        layout.label(text="Works with ANY provider -- pick a preset for a", icon='INFO')
        layout.label(text="starting point, or fill in Custom fields yourself.")

        layout.prop(settings, "preset")
        layout.operator("rig_animator.apply_ai_preset")

        col = layout.column(align=True)
        col.prop(settings, "endpoint_template")
        col.prop(settings, "auth_header_name")
        col.prop(settings, "auth_header_value_template")
        col.prop(settings, "extra_headers")
        col.prop(settings, "request_body_template")
        col.prop(settings, "response_text_path")
        col.prop(settings, "model")
        col.prop(settings, "max_tokens")

        layout.separator()
        layout.prop(settings, "api_key")
        layout.label(text="Prefer the RIG_ANIMATOR_API_KEY env var over pasting a", icon='ERROR')
        layout.label(text="real key here if this file is under version control.")

        layout.separator()
        layout.prop(settings, "known_capabilities_description")


class RIGANIM_PT_prompt(bpy.types.Panel):
    bl_label = "Prompt Tester"
    bl_idname = "RIGANIM_PT_prompt"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig Animator"
    bl_parent_id = "RIGANIM_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Sends a prompt to the configured provider and", icon='INFO')
        layout.label(text="executes whatever commands come back.")
        layout.prop(context.scene, "rig_animator_prompt", text="")
        op = layout.operator("rig_animator.request_animation")
        op.prompt = context.scene.rig_animator_prompt


classes = (
    RIGANIM_PT_main,
    RIGANIM_PT_procedural,
    RIGANIM_PT_clips,
    RIGANIM_PT_transforms,
    RIGANIM_PT_ai,
    RIGANIM_PT_prompt,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
