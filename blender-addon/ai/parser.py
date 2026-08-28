"""
Rig Animator (Blender) -- v0.1 Beta -- Created by FISHHWB

ai/parser.py
-------------
Blender port of Runtime/AI/CommandJsonParser.cs. Different AI providers/
models don't always format JSON identically (some nest params as arrays of
{key,value}, some as a flat object, some wrap a single command instead of a
batch). This reads the parsed JSON defensively rather than requiring one
exact schema, so "any AI" is more than a slogan -- same tolerance as the
Unity version. (Blender's Python has a built-in `json` module, so unlike
the Unity package there's no need for a hand-rolled MiniJson parser here.)
"""

import json
from typing import List
from ..core import AnimationCommand, normalize_layer


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline >= 0:
            text = text[first_newline + 1:]
        last_fence = text.rfind("```")
        if last_fence >= 0:
            text = text[:last_fence]
    return text.strip()


def _read_float_params(entry: dict, key: str) -> dict:
    raw = entry.get(key)
    result = {}
    if raw is None:
        return result
    if isinstance(raw, list):
        # [{"key": "x", "value": 1.2}, ...]
        for item in raw:
            if isinstance(item, dict) and 'key' in item and 'value' in item:
                try:
                    result[str(item['key'])] = float(item['value'])
                except (TypeError, ValueError):
                    pass
    elif isinstance(raw, dict):
        for k, v in raw.items():
            try:
                result[k] = float(v)
            except (TypeError, ValueError):
                pass
    return result


def _read_string_params(entry: dict, key: str) -> dict:
    raw = entry.get(key)
    result = {}
    if raw is None:
        return result
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and 'key' in item and 'value' in item:
                result[str(item['key'])] = None if item['value'] is None else str(item['value'])
    elif isinstance(raw, dict):
        for k, v in raw.items():
            result[k] = None if v is None else str(v)
    return result


def _parse_single(entry: dict):
    layer = normalize_layer(entry.get('layer'))
    if layer is None:
        return None
    target = entry.get('target')
    action = entry.get('action')
    return AnimationCommand(
        layer=layer,
        target=str(target) if target is not None else None,
        action=str(action) if action is not None else None,
        float_params=_read_float_params(entry, 'floatParams'),
        string_params=_read_string_params(entry, 'stringParams'),
    )


def parse(model_text: str) -> List[AnimationCommand]:
    """Parses the AI's raw reply text into a list of AnimationCommands.
    Tolerates a {"commands": [...]} wrapper, a bare top-level array, or a
    single command object -- same as CommandJsonParser.Parse()."""
    result: List[AnimationCommand] = []
    text = _strip_markdown_fences(model_text)
    if not text:
        return result

    try:
        root = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI reply was not valid JSON: {e}") from e

    if isinstance(root, dict) and isinstance(root.get('commands'), list):
        command_list = root['commands']
    elif isinstance(root, list):
        command_list = root  # model returned a bare array instead of {"commands":[...]}
    elif isinstance(root, dict):
        command_list = [root]  # model returned a single command object, not a batch
    else:
        return result

    for entry in command_list:
        if isinstance(entry, dict):
            cmd = _parse_single(entry)
            if cmd is not None:
                result.append(cmd)

    return result
