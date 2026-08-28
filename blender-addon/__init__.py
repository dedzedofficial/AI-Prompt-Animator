"""
Rig Animator (Blender) -- v0.1 Beta
Created by FISHHWB
Discord: https://discord.gg/vCcsnX4HQP

Blender add-on port of the "Rig Animator" Unity package (com.fishhwb.rig-
animator), kept at the same v0.1 Beta version so the two stay directly
comparable while both are being tested. See README.md / DISCLAIMER.md.

A Blender system for animating a rig or object, with an AI layer that turns
a typed prompt into animation -- using ANY AI provider's API key, not just
one vendor. Point it at Anthropic, OpenAI, Google Gemini, a self-hosted
model, or any other API that takes a JSON prompt and returns JSON: the
endpoint, auth header, request body, and response parsing are all editable
templates, not hardcoded to one service.

Three animation layers (Procedural / Clip / SimpleTransform) share one
command shape and one dispatcher (core.execute / core.execute_batch), same
as the Unity package's AnimationCommand + IAnimationExecutor +
RigAnimatorController -- hand-written code and the AI driver both end up
calling the exact same core.execute(context, obj, command).
"""

bl_info = {
    "name": "Rig Animator (Procedural + Clip + AI) -- v0.1 Beta",
    "author": "FISHHWB",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Rig Animator",
    "description": (
        "Unified system for animating rigs and objects: procedural bone/IK "
        "animation, clip-based playback/crossfade via NLA, simple transform "
        "tweening, and an AI driver that turns natural-language prompts "
        "into animation commands using any AI provider's API key. "
        "v0.1 Beta. Discord: https://discord.gg/vCcsnX4HQP"
    ),
    "category": "Animation",
    "doc_url": "https://discord.gg/vCcsnX4HQP",
}

from . import props
from . import operators
from . import ui
from . import runtime
from .ai import settings as ai_settings
from .ai import driver as ai_driver

_modules = (props, ai_settings, ai_driver, operators, ui)


def register():
    for module in _modules:
        module.register()


def unregister():
    runtime.stop()
    for module in reversed(_modules):
        module.unregister()


if __name__ == "__main__":
    register()
