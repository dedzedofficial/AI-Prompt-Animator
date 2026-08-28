"""
Rig Animator (Blender) -- v0.1 Beta
Created by FISHHWB
Discord: https://discord.gg/vCcsnX4HQP

core.py
-------
Blender port of RigAnimator.Core (AnimationCommand.cs, IAnimationExecutor.cs,
RigAnimatorController.cs) from the original Unity package. Kept at the same
v0.1 Beta version/behaviour so it stays a like-for-like reference while both
sides are tested.

A single dataclass (AnimationCommand) is the common currency between
hand-written code, the UI operators, and the AI driver -- exactly like the
Unity version. execute()/execute_batch() route a command to whichever layer
module (procedural / clip_player / object_animator) can handle it.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

LAYER_PROCEDURAL = 'PROCEDURAL'
LAYER_CLIP = 'CLIP'
LAYER_SIMPLE_TRANSFORM = 'SIMPLE_TRANSFORM'

LAYER_ITEMS = [
    (LAYER_PROCEDURAL, "Procedural", "Two-bone IK reaches / look-at, solved every tick"),
    (LAYER_CLIP, "Clip", "Named Action playback/crossfade via NLA tracks"),
    (LAYER_SIMPLE_TRANSFORM, "Simple Transform", "Eased move/rotate/scale tweens for plain objects"),
]

# Accepts the same free-form spelling the Unity enum used, case-insensitively.
_LAYER_ALIASES = {
    'procedural': LAYER_PROCEDURAL,
    'clip': LAYER_CLIP,
    'simpletransform': LAYER_SIMPLE_TRANSFORM,
    'simple_transform': LAYER_SIMPLE_TRANSFORM,
}


def normalize_layer(raw: str) -> Optional[str]:
    if not raw:
        return None
    return _LAYER_ALIASES.get(raw.strip().lower().replace(' ', ''), None)


@dataclass
class AnimationCommand:
    """A single, serializable animation instruction -- target/action pair
    plus free-form numeric and string parameters. Filled in by hand-written
    code or parsed from the AI's JSON reply."""
    layer: str
    target: str
    action: str
    float_params: Dict[str, float] = field(default_factory=dict)
    string_params: Dict[str, str] = field(default_factory=dict)

    def get_float(self, key: str, fallback: float = 0.0) -> float:
        return self.float_params.get(key, fallback)

    def get_string(self, key: str, fallback: Optional[str] = None) -> Optional[str]:
        return self.string_params.get(key, fallback)


def _executors():
    # Local import to avoid a circular import at module load time.
    from . import procedural, clip_player, object_animator
    return {
        LAYER_PROCEDURAL: procedural,
        LAYER_CLIP: clip_player,
        LAYER_SIMPLE_TRANSFORM: object_animator,
    }


def execute(context, obj, command: AnimationCommand) -> bool:
    """Routes a single command to whichever layer module matches
    command.layer, mirroring RigAnimatorController.Execute()."""
    if command is None or obj is None:
        return False

    module = _executors().get(command.layer)
    if module is None:
        print(f"Rig Animator: unknown layer '{command.layer}'")
        return False

    if not module.can_execute(obj, command):
        print(
            f"Rig Animator: no executor could handle layer={command.layer}, "
            f"target='{command.target}', action='{command.action}' on '{obj.name}'."
        )
        return False

    module.execute(context, obj, command)
    return True


def execute_batch(context, obj, commands: List[AnimationCommand]) -> None:
    """Routes a batch of commands (e.g. everything the AI returned for one
    prompt), mirroring RigAnimatorController.ExecuteBatch()."""
    if not commands:
        return
    for command in commands:
        execute(context, obj, command)
