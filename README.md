# Rig Animator — v0.1 Beta (Unity + Blender)

**Created by FISHHWB**
**Discord: https://discord.gg/vCcsnX4HQP**

This single package contains **both** versions of Rig Animator, kept at the
same v0.1 Beta version so they stay directly comparable while both are
being tested:

| Folder | What it is | Install |
|---|---|---|
| [`unity-package/`](./unity-package) | The original Unity package (`com.fishhwb.rig-animator`) | `Window ▸ Package Manager ▸ + ▸ Add package from disk…` and point at `unity-package/package.json`, **or** copy the folder into `YourProject/Packages/com.fishhwb.rig-animator` |
| [`blender-addon/`](./blender-addon) | A from-scratch Python port for Blender, same architecture | Zip the `blender-addon/` folder, then in Blender: `Edit ▸ Preferences ▸ Add-ons ▸ Install…` |

Both sides share the same design:

- One command shape (`AnimationCommand` / dataclass) routed through one
  dispatcher (`RigAnimatorController.Execute` in Unity, `core.execute` in
  Blender).
- Three animation layers: **Procedural** (two-bone IK reach + look-at),
  **Clip** (named clip/Action playback & crossfade), **Simple Transform**
  (eased move/rotate/scale tweens).
- An **AI driver** that turns a typed prompt into a batch of those same
  commands, using *any* AI provider's API key (Anthropic/OpenAI/Google
  Gemini presets, or fully custom endpoint/auth/body/response-path
  templates) — nothing is hardcoded to one vendor on either side.

Each folder has its own `README.md` and `DISCLAIMER.md` with full setup
instructions and side-specific notes — read the one for whichever engine
you're using. The Blender port's README also lists the known differences
from the Unity original (bone-forward-axis assumption for look-at, NLA vs.
`PlayableGraph` crossfading, timer-driven tick loop instead of automatic
per-frame `Update()`).

> ⚠️ Both are v0.1 **beta** software. Read the `DISCLAIMER.md` in each
> folder before using either beyond local testing — short version: AI
> output isn't guaranteed to be well-formed, third-party API usage is
> billed by and subject to that provider's own terms, and you're
> responsible for keeping your API key out of anything you ship or commit.

## License

MIT, both sides — see `LICENSE` in each folder.

## Support

Questions, bugs, or feedback: join the Discord — **https://discord.gg/vCcsnX4HQP**
