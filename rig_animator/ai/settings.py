"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB
Discord: https://discord.gg/vCcsnX4HQP

ai/settings.py
---------------
Blender port of Runtime/AI/AIProviderSettings.cs. Connection settings for
ANY AI provider's chat/completions-style API -- Anthropic, OpenAI, Google
Gemini, a local model server, or anything else that accepts a JSON POST and
returns JSON. Nothing here is hardcoded to one vendor: endpoint, auth
header, request body, and where to find the reply text are all editable
templates. Presets just pre-fill sensible defaults you can then tweak or
fully override -- identical field-for-field to the Unity version.

Stored on the Scene (bpy.types.Scene.rig_animator_ai) rather than baked
into an object, same reasoning as the Unity version keeping it as a
ScriptableObject asset: keep a real key out of anything you'd commit.
Prefer leaving api_key empty and setting the RIG_ANIMATOR_API_KEY
environment variable instead -- see ai/driver.py.
"""

import os
import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty

PRESET_ITEMS = [
    ('ANTHROPIC', "Anthropic", "Claude models via api.anthropic.com"),
    ('OPENAI', "OpenAI", "GPT models via api.openai.com"),
    ('GOOGLE_GEMINI', "Google Gemini", "Gemini models via generativelanguage.googleapis.com"),
    ('CUSTOM', "Custom", "Any other chat-completions-style JSON API"),
]

_PRESET_DEFAULTS = {
    'ANTHROPIC': dict(
        endpoint_template="https://api.anthropic.com/v1/messages",
        auth_header_name="x-api-key",
        auth_header_value_template="{API_KEY}",
        extra_headers="anthropic-version: 2023-06-01",
        request_body_template=(
            '{"model":"{MODEL}","max_tokens":{MAX_TOKENS},'
            '"system":"{SYSTEM_PROMPT}","messages":[{"role":"user","content":"{USER_PROMPT}"}]}'
        ),
        response_text_path="content.0.text",
        default_model="claude-sonnet-4-6",
    ),
    'OPENAI': dict(
        endpoint_template="https://api.openai.com/v1/chat/completions",
        auth_header_name="Authorization",
        auth_header_value_template="Bearer {API_KEY}",
        extra_headers="",
        request_body_template=(
            '{"model":"{MODEL}","max_tokens":{MAX_TOKENS},"messages":['
            '{"role":"system","content":"{SYSTEM_PROMPT}"},'
            '{"role":"user","content":"{USER_PROMPT}"}]}'
        ),
        response_text_path="choices.0.message.content",
        default_model="gpt-4o-mini",
    ),
    'GOOGLE_GEMINI': dict(
        endpoint_template="https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}",
        auth_header_name="",
        auth_header_value_template="",
        extra_headers="",
        request_body_template=(
            '{"contents":[{"role":"user","parts":[{"text":"{SYSTEM_PROMPT}\\n\\n{USER_PROMPT}"}]}]}'
        ),
        response_text_path="candidates.0.content.parts.0.text",
        default_model="gemini-2.0-flash",
    ),
}

DEFAULT_SYSTEM_PROMPT_TEMPLATE = (
    "You control animation for a Blender character/object rig by returning ONLY JSON, "
    "no prose, no markdown fences.\n"
    "Schema:\n"
    '{{ "commands": [ {{ "layer": "PROCEDURAL|CLIP|SIMPLE_TRANSFORM", "target": string, '
    '"action": string, "floatParams": {{"x":number,...}}, "stringParams": {{"ease":string,...}} }} ] }}\n'
    "Known targets and actions:\n{0}\n"
    "Only reference targets/actions from that list. Respond with the JSON object and nothing else."
)

DEFAULT_CAPABILITIES_DESCRIPTION = (
    "Procedural: ik_reach(target=<chain>, x,y,z, duration, weight), "
    "look_at(target=<bone>, x,y,z, speed, weight), stop(target)\n"
    "Clip: play(target=<clip name>, fade, speed), stop(target=<clip name or \"*\">, fade)\n"
    "SimpleTransform: move_to/rotate_to/scale_to(target=<object name>, x,y,z, duration, ease), stop(target)"
)


class RigAnimatorAIProviderSettings(bpy.types.PropertyGroup):
    preset: EnumProperty(name="Preset", items=PRESET_ITEMS, default='CUSTOM')

    endpoint_template: StringProperty(
        name="Endpoint",
        description="Full request URL. Can contain {API_KEY}/{MODEL} placeholders "
                    "for providers that put them in the URL (e.g. Google Gemini).",
        default="",
    )
    auth_header_name: StringProperty(
        name="Auth Header",
        description="Header name for auth, e.g. 'x-api-key' or 'Authorization'. "
                    "Leave empty if the key only goes in the URL.",
        default="",
    )
    auth_header_value_template: StringProperty(
        name="Auth Header Value",
        description="Header value template, e.g. '{API_KEY}' or 'Bearer {API_KEY}'.",
        default="{API_KEY}",
    )
    extra_headers: StringProperty(
        name="Extra Headers",
        description="Extra fixed headers this provider needs, one per line as "
                    "'Header-Name: value' (e.g. Anthropic needs 'anthropic-version: 2023-06-01').",
        default="",
    )
    request_body_template: StringProperty(
        name="Request Body Template",
        description="Raw JSON POST body. Supports {MODEL} {MAX_TOKENS} {SYSTEM_PROMPT} "
                    "{USER_PROMPT} placeholders -- the two prompt placeholders are "
                    "auto JSON-escaped for you.",
        default="",
    )
    response_text_path: StringProperty(
        name="Response Text Path",
        description="Dot path to the reply text inside the JSON response, e.g. "
                    "'content.0.text' (Anthropic), 'choices.0.message.content' (OpenAI), "
                    "'candidates.0.content.parts.0.text' (Gemini).",
        default="",
    )
    model: StringProperty(name="Model", default="")
    max_tokens: IntProperty(name="Max Tokens", default=1024, min=1)

    api_key: StringProperty(
        name="API Key",
        description="Leave empty and set the RIG_ANIMATOR_API_KEY environment variable "
                    "instead of committing a real key with your .blend file.",
        default="",
        subtype='PASSWORD',
    )

    system_prompt_template: StringProperty(
        name="System Prompt Template",
        default=DEFAULT_SYSTEM_PROMPT_TEMPLATE,
    )
    known_capabilities_description: StringProperty(
        name="Known Capabilities",
        description="Human-readable description of available targets/actions injected "
                    "into the system prompt so the AI only issues valid commands.",
        default=DEFAULT_CAPABILITIES_DESCRIPTION,
    )

    def resolve_api_key(self) -> str:
        return self.api_key or os.environ.get("RIG_ANIMATOR_API_KEY", "")

    def resolve_endpoint(self) -> str:
        key = self.resolve_api_key()
        return (self.endpoint_template or "").replace("{API_KEY}", key).replace("{MODEL}", self.model or "")

    def apply_preset(self):
        if self.preset == 'CUSTOM':
            return
        defaults = _PRESET_DEFAULTS.get(self.preset)
        if not defaults:
            return
        self.endpoint_template = defaults['endpoint_template']
        self.auth_header_name = defaults['auth_header_name']
        self.auth_header_value_template = defaults['auth_header_value_template']
        self.extra_headers = defaults['extra_headers']
        self.request_body_template = defaults['request_body_template']
        self.response_text_path = defaults['response_text_path']
        if not self.model:
            self.model = defaults['default_model']


class RIGANIM_OT_apply_ai_preset(bpy.types.Operator):
    bl_idname = "rig_animator.apply_ai_preset"
    bl_label = "Apply Preset"
    bl_description = "Fill endpoint/auth/body/response-path defaults for the selected preset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.rig_animator_ai.apply_preset()
        return {'FINISHED'}


classes = (
    RigAnimatorAIProviderSettings,
    RIGANIM_OT_apply_ai_preset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rig_animator_ai = bpy.props.PointerProperty(type=RigAnimatorAIProviderSettings)


def unregister():
    del bpy.types.Scene.rig_animator_ai
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
