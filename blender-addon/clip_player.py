"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB

clip_player.py
---------------
Blender port of Runtime/ClipBased/ClipAnimationPlayer.cs. Plays/crossfades
named Actions through NLA tracks, independent of any single "current
action" slot -- good for AI-driven or ad-hoc clip playback where you don't
want to hand-author transitions.

Supported actions (identical contract to the Unity version):
    "play"  target=<clip name>              floatParams: fade (seconds), speed
    "stop"  target=<clip name or "*">       floatParams: fade (seconds)

Each active strip's influence is tweened toward 0 or 1 every runtime tick
(see runtime.py), same as the Unity version's per-frame MoveTowards on
mixer input weight, then normalized so concurrent strips sum to <= 1.
"""

import bpy
from . import core

# runtime[obj_name] = [ {name, track, strip, target_weight, fade_speed, fading_out}, ... ]
_runtime = {}


def _state(obj_name):
    return _runtime.setdefault(obj_name, [])


def _find_clip_def(obj, name):
    settings = getattr(obj, "rig_animator", None)
    if not settings:
        return None
    for c in settings.clips:
        if c.name == name:
            return c
    return None


def can_execute(obj, command: 'core.AnimationCommand') -> bool:
    if command.action == 'stop':
        return True  # "*" is always valid, same as the Unity version
    return _find_clip_def(obj, command.target) is not None


def execute(context, obj, command: 'core.AnimationCommand') -> None:
    settings = getattr(obj, "rig_animator", None)
    default_fade = settings.default_fade_seconds if settings else 0.25

    if command.action == 'play':
        _play(obj, command.target,
              fade_seconds=command.get_float('fade', default_fade),
              speed=command.get_float('speed', 1.0))
    elif command.action == 'stop':
        _stop(obj, command.target, command.get_float('fade', default_fade))


def _play(obj, clip_name, fade_seconds, speed=1.0):
    clip_def = _find_clip_def(obj, clip_name)
    if clip_def is None or clip_def.action is None:
        print(f"Rig Animator: no clip registered under name '{clip_name}' on '{obj.name}'.")
        return

    if obj.animation_data is None:
        obj.animation_data_create()

    active = _state(obj.name)

    # Fade out anything currently playing (same as the Unity version).
    for existing in active:
        if not existing['fading_out']:
            existing['fading_out'] = True
            existing['target_weight'] = 0.0
            existing['fade_speed'] = (1.0 / fade_seconds) if fade_seconds > 0 else 999.0

    track = obj.animation_data.nla_tracks.new()
    track.name = f"RigAnimator_{clip_name}"
    start_frame = bpy.context.scene.frame_current
    strip = track.strips.new(clip_name, start_frame, clip_def.action)
    strip.blend_type = 'REPLACE'
    strip.use_animated_influence = False
    strip.influence = 0.0
    strip.use_sync_length = False
    strip.scale = speed if speed > 0 else 1.0
    strip.extrapolation = 'HOLD'

    active.append({
        'name': clip_name,
        'track': track,
        'strip': strip,
        'target_weight': 1.0,
        'fade_speed': (1.0 / fade_seconds) if fade_seconds > 0 else 999.0,
        'fading_out': False,
    })


def _stop(obj, clip_name, fade_seconds):
    for existing in _state(obj.name):
        if clip_name == '*' or existing['name'] == clip_name:
            existing['fading_out'] = True
            existing['target_weight'] = 0.0
            existing['fade_speed'] = (1.0 / fade_seconds) if fade_seconds > 0 else 999.0


def _move_towards(current, target, max_delta):
    if abs(target - current) <= max_delta:
        return target
    return current + (max_delta if target > current else -max_delta)


def tick(context, dt: float) -> None:
    """Equivalent of ClipAnimationPlayer's per-frame Update(): steps every
    active strip's influence toward its target, removes fully-faded-out
    strips/tracks, then normalizes so concurrent strips don't exceed 1.0
    combined influence."""
    for obj_name, active in list(_runtime.items()):
        obj = bpy.data.objects.get(obj_name)
        if obj is None or obj.animation_data is None:
            _runtime.pop(obj_name, None)
            continue

        to_remove = []
        for entry in active:
            strip = entry['strip']
            try:
                current = strip.influence
            except ReferenceError:
                to_remove.append(entry)
                continue

            next_val = _move_towards(current, entry['target_weight'], entry['fade_speed'] * dt)
            strip.influence = next_val
            strip.use_influence = True

            if entry['fading_out'] and next_val <= 0.0:
                to_remove.append(entry)

        for entry in to_remove:
            active.remove(entry)
            try:
                obj.animation_data.nla_tracks.remove(entry['track'])
            except (ReferenceError, RuntimeError):
                pass

        total = sum(e['strip'].influence for e in active if e['strip'])
        if total > 1.0 and total > 0.0001:
            for e in active:
                e['strip'].influence = e['strip'].influence / total

        if not active:
            _runtime.pop(obj_name, None)


def clear_runtime_for_object(obj_name: str) -> None:
    _runtime.pop(obj_name, None)


def clear_all_runtime() -> None:
    _runtime.clear()
