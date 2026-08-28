# Rig Animator (Blender) — v0.1 Beta

**Created by FISHHWB**
**Discord: https://discord.gg/vCcsnX4HQP**

A Blender add-on for animating a rig or object, with an AI layer that turns
a typed prompt into animation — using **any AI provider's API key**, not
just one vendor. Point it at Anthropic, OpenAI, Google Gemini, a self-hosted
model, or any other API that takes a JSON prompt and returns JSON: the
endpoint, auth header, request body, and response parsing are all editable
templates, not hardcoded to one service.

This is a **Python port of the [Rig Animator Unity package](../)**, kept at
the same v0.1 Beta version on purpose so both sides stay directly
comparable while you're testing. Same three animation layers, same
`AnimationCommand` shape, same AI-provider-settings contract — just Blender
`bpy`/`mathutils` instead of Unity `MonoBehaviour`/`UnityEngine`.

> ⚠️ **Read [DISCLAIMER.md](./DISCLAIMER.md) before using this in anything
> beyond local testing.** Short version: this is beta software, AI output
> isn't guaranteed to be well-formed, third-party API usage is billed by and
> subject to that provider's own terms, and you're responsible for keeping
> your API key out of anything you ship or commit.

## What's included

| Layer | Module | What it does |
|---|---|---|
| Procedural | `procedural.py` | Analytic two-bone IK reaches and smoothed look-at, solved every runtime tick — no Actions involved. |
| Clip | `clip_player.py` | Plays/crossfades named Actions via NLA tracks, independent of any single "current action" slot. |
| Simple transform | `object_animator.py` | Eased move/rotate/scale tweens for plain objects — empties, props, cameras. |
| AI (any provider) | `ai/driver.py` + `ai/settings.py` | You type a prompt; it's sent to whichever AI provider you've configured, the JSON reply is parsed, and the resulting commands run through the same pipeline as hand-written code. |

One dataclass (`AnimationCommand`), one dispatcher (`core.execute` /
`core.execute_batch`) — hand-written code, the panel's test button, and the
AI driver all end up calling the exact same `core.execute(context, obj, command)`.

## Install

1. Zip the `rig_animator/` folder (or use the one you already have).
2. In Blender: `Edit ▸ Preferences ▸ Add-ons ▸ Install…`, pick the zip, then
   enable **"Rig Animator (Procedural + Clip + AI) — v0.1 Beta"**.
3. Open the 3D Viewport sidebar (`N`) — you'll get a **Rig Animator** tab.

## Scene setup

1. Select your rig (an Armature) or plain object, then open the **Rig
   Animator** sidebar tab.
2. Click **Start Runtime** — this is the one thing Blender needs that Unity
   doesn't: Unity's `Update()`/`LateUpdate()` run automatically every
   frame; Blender needs the tick loop switched on before IK/look-at/clip
   fades/tweens will animate live.
3. Under **Procedural (IK / Look-At)**: add named IK chains (root/mid/tip
   pose bones) and named look-at bones.
4. Under **Clip (Actions)**: add name → Action pairs.
5. Under **Simple Transform**: add name → Object pairs.
6. Drive it from Python, no AI required:

```python
import bpy
from rig_animator import core, runtime

obj = bpy.context.active_object
runtime.start()
core.execute(bpy.context, obj, core.AnimationCommand(
    layer=core.LAYER_CLIP, target="Wave", action="play",
    float_params={"fade": 0.2},
))
```

Or from the panel's **Prompt Tester**, use **Execute Command** for a
one-off test without touching Python.

## Plugging in an AI — any provider, any key

1. Open the **AI Provider (any vendor)** section of the sidebar.
2. Pick a **Preset** (Anthropic / OpenAI / Google Gemini) and click **Apply
   Preset** for a working starting point, or leave it on **Custom** and
   fill in the fields yourself for any other provider:
   - **Endpoint** — the full request URL (can include `{API_KEY}` or
     `{MODEL}` placeholders, e.g. for providers that put the key in the URL).
   - **Auth header** — header name + value template (e.g. `Authorization` /
     `Bearer {API_KEY}`), or leave empty if the key only goes in the URL.
   - **Request body template** — raw JSON with `{MODEL}`, `{MAX_TOKENS}`,
     `{SYSTEM_PROMPT}`, `{USER_PROMPT}` placeholders (the two prompt ones
     are auto-escaped for you).
   - **Response text path** — dot path to the reply text in the response
     JSON, e.g. `content.0.text` (Anthropic), `choices.0.message.content`
     (OpenAI), `candidates.0.content.parts.0.text` (Gemini).
3. Paste your key into **API Key** for local testing, **or** leave it empty
   and set the `RIG_ANIMATOR_API_KEY` environment variable before launching
   Blender instead.
4. Edit **Known Capabilities** to match your actual registered
   targets/actions so the AI only issues commands your rig understands.
5. Fire a prompt from the **Prompt Tester** panel: `Raise the right hand and
   look at the player.`

The driver builds the request from your template, sends it on a background
thread (so Blender's UI doesn't freeze), reads the reply via your response
path, parses the JSON command batch (tolerant of a few common formatting
variations between models), and runs it through `core.execute_batch(...)`
back on the main thread.

## Extending

- Add a new animation layer by writing a module with `can_execute(obj, command)`
  and `execute(context, obj, command)` functions, then wire it into
  `core._executors()` — no changes needed elsewhere.
- Point AI provider settings at literally any chat-completions-style API by
  filling in the Custom template fields; nothing in the driver assumes a
  specific vendor.

## Known limitations vs. the Unity version (v0.1 Beta, both sides)

- The two-bone IK solve assumes bones point down local **+Y** (Blender's
  default convention) and is an approximation, not a constraint-solver —
  same "computed, not guaranteed" caveat the Unity version carries.
- NLA-based clip crossfading is a simpler approximation of the Unity
  version's `PlayableGraph` mixer; multi-strip blending beyond two
  overlapping clips hasn't been stress-tested.
- The runtime tick loop uses `bpy.app.timers` at a fixed ~30Hz rather than
  Blender's per-frame `Depsgraph` evaluation, so timing precision is
  "good enough for testing," not frame-exact.

## License

MIT — see `LICENSE`.

## Disclaimer & support

See [DISCLAIMER.md](./DISCLAIMER.md). For questions, bugs, or feedback, join
the Discord: **https://discord.gg/vCcsnX4HQP**
