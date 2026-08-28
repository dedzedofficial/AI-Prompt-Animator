# Disclaimer

**Rig Animator — v0.1 Beta — Created by FISHHWB**
Discord: https://discord.gg/vCcsnX4HQP

This is early beta software (v0.1). Please read before using it in anything
beyond local testing.

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
   version control or a shared project asset. Calling a provider's API
   directly from a built game client embeds your key in that build — for
   anything you intend to ship or distribute, proxy the request through
   your own backend instead so the key never exists in the client.

4. **AI output is not guaranteed.** Language models can return malformed,
   unexpected, or incorrect JSON, or issue commands that don't make sense
   for your rig. This package includes defensive parsing, but you should
   still review and test AI-driven behavior before relying on it, especially
   in anything user-facing or shipped.

5. **Beta status.** As v0.1 Beta, APIs, defaults, and behavior in this
   package may change in future versions without full backward
   compatibility. Pin a specific commit/tag if you need stability.

6. **Not affiliated with Unity Technologies.** "Unity" refers to the Unity
   game engine; this is a third-party tool for use with it and is not made
   or endorsed by Unity Technologies.

Questions, bugs, or feedback: join the Discord above.
