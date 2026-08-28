# Rig Animator — v0.1 Beta

**Created by FISHHWB**
**Discord: https://discord.gg/vCcsnX4HQP**

A Unity system for animating a rig or object, with an AI layer that turns a
typed prompt into animation — using **any AI provider's API key**, not just
one vendor. Point it at Anthropic, OpenAI, Google Gemini, a self-hosted
model, or any other API that takes a JSON prompt and returns JSON: the
endpoint, auth header, request body, and response parsing are all editable
templates, not hardcoded to one service.

> ⚠️ **Read [DISCLAIMER.md](./DISCLAIMER.md) before using this in anything
> beyond local testing.** Short version: this is beta software, AI output
> isn't guaranteed to be well-formed, third-party API usage is billed by and
> subject to that provider's own terms, and you're responsible for keeping
> your API key out of anything you ship or commit.

## What's included

| Layer | Component | What it does |
|---|---|---|
| Procedural | `ProceduralAnimator` | Two-bone IK reaches and smoothed look-at constraints, computed every frame — no clips involved. |
| Clip-based | `ClipAnimationPlayer` | Plays/cross-fades named `AnimationClip`s via a `PlayableGraph`, independent of an Animator Controller state machine. |
| Simple transform | `SimpleObjectAnimator` | Eased move/rotate/scale tweens for plain objects — doors, props, cameras, UI. |
| AI (any provider) | `AIAnimationDriver` + `AIProviderSettings` | You type a prompt; it's sent to whichever AI provider you've configured, the JSON reply is parsed, and the resulting commands run through the same pipeline as hand-written code. |

One struct (`AnimationCommand`), one interface (`IAnimationExecutor`), one
router (`RigAnimatorController`) — hand-written gameplay code and the AI
driver both end up calling the exact same `controller.Execute(command)`.

## Install

**Option A — Package Manager (git URL), once this is on GitHub:**
1. Push this repo to GitHub (see below).
2. In Unity: `Window ▸ Package Manager ▸ + ▸ Add package from git URL…`
3. Enter `https://github.com/<you>/<repo>.git`

**Option B — local package:**
Copy this folder into `YourProject/Packages/com.fishhwb.rig-animator`.

## Scene setup

1. Add `RigAnimatorController` to your rig's root object.
2. Add whichever of `ProceduralAnimator`, `ClipAnimationPlayer`,
   `SimpleObjectAnimator` you need — `RigAnimatorController` auto-discovers
   them on `Awake`.
3. Register named targets in each:
   - `ProceduralAnimator`: IK chains (root/mid/tip transforms) and look-at bones.
   - `ClipAnimationPlayer`: name → `AnimationClip` pairs.
   - `SimpleObjectAnimator`: name → `Transform` pairs.
4. Drive it from code, no AI required:

```csharp
controller.Execute(new AnimationCommand {
    layer = AnimationLayer.Clip,
    target = "Wave",
    action = "play",
    floatParams = { { "fade", 0.2f } }
});
```

## Plugging in an AI — any provider, any key

1. `Assets ▸ Create ▸ Rig Animator ▸ AI Provider Settings`.
2. Pick a **Preset** (Anthropic / OpenAI / Google Gemini) and click
   **Apply Preset** for a working starting point, or leave it on **Custom**
   and fill in the fields yourself for any other provider:
   - **Endpoint** — the full request URL (can include `{API_KEY}` or
     `{MODEL}` placeholders, e.g. for providers that put the key in the URL).
   - **Auth header** — header name + value template (e.g. `Authorization` /
     `Bearer {API_KEY}`), or leave empty if the key only goes in the URL.
   - **Request body template** — raw JSON with `{MODEL}`, `{MAX_TOKENS}`,
     `{SYSTEM_PROMPT}`, `{USER_PROMPT}` placeholders (the two prompt ones are
     auto-escaped for you).
   - **Response text path** — dot path to the reply text in the response
     JSON, e.g. `content.0.text` (Anthropic), `choices.0.message.content`
     (OpenAI), `candidates.0.content.parts.0.text` (Gemini).
3. Paste your key into the asset for local testing, **or** leave it empty
   and call `settings.SetApiKeyAtRuntime(key)` from code to supply it from
   an environment variable or your own server instead — see
   `Samples~/BasicSetup/ExampleBootstrapper.cs`.
4. Add `AIAnimationDriver` next to `RigAnimatorController`, assign the
   settings asset, and edit `knownCapabilitiesDescription` to match your
   actual registered targets/actions so the AI only issues commands your
   rig understands.
5. Fire a prompt:

```csharp
driver.RequestAnimation("Raise the right hand and look at the player.");
```

The driver builds the request from your template, sends it, reads the reply
via your response path, parses the JSON command batch (tolerant of a few
common formatting variations between models), and calls
`controller.ExecuteBatch(...)` for you.

## Push this to GitHub

```bash
cd com.fishhwb.rig-animator
git init
git add .
git commit -m "Rig Animator v0.1 Beta"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

## Extending

- Add a new animation layer by implementing `IAnimationExecutor` — no
  changes needed to `RigAnimatorController`.
- Point `AIProviderSettings` at literally any chat-completions-style API by
  filling in the Custom template fields; nothing in the driver assumes a
  specific vendor.

## License

MIT — see `LICENSE`.

## Disclaimer & support

See [DISCLAIMER.md](./DISCLAIMER.md). For questions, bugs, or feedback, join
the Discord: **https://discord.gg/vCcsnX4HQP**
