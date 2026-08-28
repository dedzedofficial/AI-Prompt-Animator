"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB

runtime.py
----------
Unity's Update()/LateUpdate() run automatically every frame with no setup
needed. Blender has no equivalent for a plain Python add-on, so this module
provides a small timer-driven loop that calls into procedural.tick(),
clip_player.tick() and object_animator.tick() every ~1/30s while it's
running -- start it from the Rig Animator panel (or RIGANIM_OT_toggle_runtime)
before sending ik_reach/look_at/play/move_to commands so they animate live.
"""

import time
import bpy
from . import procedural, clip_player, object_animator

_INTERVAL = 1.0 / 30.0
_running = False
_last_tick = None


def is_running() -> bool:
    return _running


def _tick():
    global _last_tick
    if not _running:
        return None  # unregisters the timer

    now = time.time()
    dt = _INTERVAL if _last_tick is None else max(0.0, min(0.25, now - _last_tick))
    _last_tick = now

    context = bpy.context
    procedural.tick(context, dt)
    clip_player.tick(context, dt)
    object_animator.tick(context, dt)

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    return _INTERVAL


def start():
    global _running, _last_tick
    if _running:
        return
    _running = True
    _last_tick = None
    bpy.app.timers.register(_tick, first_interval=_INTERVAL)


def stop():
    global _running
    _running = False


def clear_all():
    """Drops all in-flight playback state (does not touch scene data)."""
    procedural.clear_all_runtime()
    clip_player.clear_all_runtime()
    object_animator.clear_all_runtime()
