"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB
Discord: https://discord.gg/vCcsnX4HQP

ai/driver.py
-------------
Blender port of Runtime/AI/AIAnimationDriver.cs. Turns a typed prompt into
animation commands using ANY AI provider's API key -- Anthropic, OpenAI,
Gemini, a self-hosted model, anything that accepts a JSON POST and returns
JSON. See ai/settings.py for the connection template. Nothing about this
class is vendor-specific; swapping providers means changing the settings,
not the code.

DISCLAIMER: this is beta software (v0.1). AI responses are not guaranteed
to be well-formed, safe, or correct -- always sanity-check commands before
relying on this in a finished project. Calling a third-party AI API from
this driver sends your prompt (and whatever capability description you
configure) to that provider, subject to that provider's own terms,
pricing, and rate limits. See README.md / DISCLAIMER.md before shipping
anything built on this tool.

Network calls are made on a background thread (Blender's UI must not
block), then handed back to the main thread via bpy.app.timers so the
actual scene/pose edits happen safely.
"""

import json
import threading
import urllib.request
import urllib.error

import bpy
from bpy.props import StringProperty

from .. import core
from . import parser as command_parser


def _json_escape(raw: str) -> str:
    """Mirrors MiniJson.Escape: JSON-escapes a raw string for embedding into
    a hand-built JSON template (as opposed to json.dumps(), which would
    also add surrounding quotes we don't want here)."""
    if raw is None:
        return ""
    return json.dumps(raw)[1:-1]


def _get_path(root, dot_path: str):
    """Mirrors MiniJson.GetPath: navigates a parsed JSON object graph using
    a dot path, e.g. 'content.0.text' or 'choices.0.message.content'.
    Numeric segments index into lists. Returns None if any segment is
    missing."""
    if not dot_path:
        return root
    current = root
    for segment in dot_path.split('.'):
        if current is None:
            return None
        if segment.lstrip('-').isdigit():
            index = int(segment)
            if isinstance(current, list) and -len(current) <= index < len(current):
                current = current[index]
            else:
                return None
        else:
            if isinstance(current, dict) and segment in current:
                current = current[segment]
            else:
                return None
    return current


def _build_body(settings, system_prompt: str, user_prompt: str) -> str:
    return (settings.request_body_template
            .replace('{MODEL}', settings.model or '')
            .replace('{MAX_TOKENS}', str(settings.max_tokens))
            .replace('{SYSTEM_PROMPT}', _json_escape(system_prompt))
            .replace('{USER_PROMPT}', _json_escape(user_prompt)))


def _split_header_lines(text: str):
    if not text:
        return
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        colon = line.find(':')
        if colon > 0:
            yield line[:colon].strip(), line[colon + 1:].strip()


class RIGANIM_OT_request_animation(bpy.types.Operator):
    """Sends prompt to the configured AI provider and executes whatever
    animation commands come back, equivalent of
    AIAnimationDriver.RequestAnimation()."""
    bl_idname = "rig_animator.request_animation"
    bl_label = "Send Prompt"
    bl_description = "Send this prompt to the configured AI provider and animate the target object"
    bl_options = {'REGISTER'}

    prompt: StringProperty(name="Prompt", default="Raise the right hand and look at the player.")

    def execute(self, context):
        settings = context.scene.rig_animator_ai
        obj = context.scene.rig_animator_target or context.active_object

        if obj is None:
            self.report({'ERROR'}, "Rig Animator: no target object set/selected.")
            return {'CANCELLED'}

        api_key = settings.resolve_api_key()
        if not api_key:
            self.report({'ERROR'}, "Rig Animator: no API key. Fill it in (local testing only) "
                                    "or set the RIG_ANIMATOR_API_KEY environment variable.")
            return {'CANCELLED'}

        if not settings.endpoint_template or not settings.request_body_template:
            self.report({'ERROR'}, "Rig Animator: missing endpoint or request body template. "
                                    "Pick a Preset and click 'Apply Preset', or fill in Custom fields.")
            return {'CANCELLED'}

        system_prompt = settings.system_prompt_template.replace(
            '{0}', settings.known_capabilities_description)
        endpoint = settings.resolve_endpoint()
        body = _build_body(settings, system_prompt, self.prompt)

        headers = {'Content-Type': 'application/json'}
        if settings.auth_header_name:
            headers[settings.auth_header_name] = settings.auth_header_value_template.replace(
                '{API_KEY}', api_key)
        for name, value in _split_header_lines(settings.extra_headers):
            headers[name] = value

        response_text_path = settings.response_text_path
        obj_name = obj.name

        def worker():
            try:
                req = urllib.request.Request(
                    endpoint, data=body.encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=60) as resp:
                    raw = resp.read().decode('utf-8')
                bpy.app.timers.register(lambda: _on_success(raw, response_text_path, obj_name))
            except urllib.error.HTTPError as e:
                raw = e.read().decode('utf-8', errors='replace')
                msg = f"Rig Animator: request failed ({e.code}): {raw}"
                bpy.app.timers.register(lambda: _on_error(msg))
            except Exception as e:
                msg = f"Rig Animator: request failed: {e}"
                bpy.app.timers.register(lambda: _on_error(msg))

        threading.Thread(target=worker, daemon=True).start()
        self.report({'INFO'}, "Rig Animator: prompt sent...")
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


def _on_error(message: str):
    print(message)
    return None  # unregister the timer


def _on_success(raw_response: str, response_text_path: str, obj_name: str):
    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError as e:
        print(f"Rig Animator: response was not valid JSON: {e}\nRaw response: {raw_response}")
        return None

    extracted = _get_path(parsed_response, response_text_path)
    if extracted is None:
        print(f"Rig Animator: response path '{response_text_path}' did not resolve to "
              f"anything in the response.\nRaw response: {raw_response}")
        return None

    model_text = str(extracted)

    try:
        commands = command_parser.parse(model_text)
    except Exception as e:
        print(f"Rig Animator: AI reply was not valid command JSON -- {e}\nRaw reply: {model_text}")
        return None

    if not commands:
        print(f"Rig Animator: parsed zero commands from the AI's reply. Raw reply: {model_text}")

    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"Rig Animator: target object '{obj_name}' no longer exists.")
        return None

    from .. import runtime
    if not runtime.is_running():
        runtime.start()

    core.execute_batch(bpy.context, obj, commands)
    return None  # unregister the timer


classes = (
    RIGANIM_OT_request_animation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
