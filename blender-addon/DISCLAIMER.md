# Disclaimer

**Rig Animator (Blender) — v0.1 Beta — Created by FISHHWB**
Discord: https://discord.gg/vCcsnX4HQP

This is early beta software (v0.1), and a direct Python port of the Rig
Animator Unity package kept at a matching version for side-by-side testing.
Please read before using it in anything beyond local testing.

1. **No warranty.** This software is provided "as is," without warranty of
   any kind, express or implied, including but not limited to fitness for a
   particular purpose. Use it at your own risk. See `LICENSE` (MIT).

2. **Third-party AI providers.** The AI-driven animation feature sends your
   prompt (and the capability description you configure) to whichever AI
   provider you connect — Anthropic, OpenAI, Google, or any other API you
   point it at. That provider's own terms of service, privacy policy,
   pricing, and rate limits apply. This project is not affiliated with,
   endorsed by, or sponsored by any AI provider. You are responsible for
   any costs incurred by API usage under your own key.

3. **API keys are your responsibility.** Never commit a real API key into
   version control or a shared `.blend` file. Prefer leaving the **API Key**
   field empty and setting the `RIG_ANIMATOR_API_KEY` environment variable
   before launching Blender instead, so the key never ends up saved into a
   file you might share.

4. **AI output is not guaranteed.** Language models can return malformed,
   unexpected, or incorrect JSON, or issue commands that don't make sense
   for your rig. This add-on includes defensive parsing, but you should
   still review and test AI-driven behavior before relying on it.

5. **Beta status, and a Python port.** As v0.1 Beta, APIs, defaults, and
   behavior in this add-on may change in future versions without full
   backward compatibility. The procedural IK/look-at solve, the NLA-based
   clip crossfading, and the runtime tick loop are Blender-specific
   approximations of the Unity version's equivalent systems — see
   "Known limitations" in `README.md`. Pin a specific version/commit if you
   need stability.

6. **Not affiliated with the Blender Foundation.** "Blender" refers to the
   Blender 3D creation suite; this is a third-party add-on for use with it
   and is not made or endorsed by the Blender Foundation.

7. **Network access.** Sending a prompt makes an outbound HTTPS request
   from Blender to whichever endpoint you've configured, on a background
   thread. No request is made unless you explicitly trigger one (there is
   no automatic or background polling).

Questions, bugs, or feedback: join the Discord above.
