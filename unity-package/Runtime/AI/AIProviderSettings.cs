using UnityEngine;

namespace RigAnimator.AI
{
    /// <summary>
    /// Rig Animator v0.1 Beta — Created by FISHHWB
    /// Discord: https://discord.gg/vCcsnX4HQP
    ///
    /// Connection settings for ANY AI provider's chat/completions-style API —
    /// Anthropic, OpenAI, Google Gemini, a local model server, or anything
    /// else that accepts a JSON POST and returns JSON. Nothing here is
    /// hardcoded to one vendor: endpoint, auth header, request body, and
    /// where to find the reply text are all editable templates. Presets just
    /// pre-fill sensible defaults you can then tweak or fully override.
    ///
    /// Kept as an asset (not a scene component) so a real key doesn't end up
    /// baked into a scene/prefab. Set it at runtime via SetApiKeyAtRuntime()
    /// instead of typing a real key into this asset if the project is under
    /// version control.
    /// </summary>
    [CreateAssetMenu(fileName = "AIProviderSettings", menuName = "Rig Animator/AI Provider Settings")]
    public class AIProviderSettings : ScriptableObject
    {
        public enum Preset { Anthropic, OpenAI, GoogleGemini, Custom }

        [Header("Preset (fills the fields below — edit freely afterward)")]
        public Preset preset = Preset.Custom;

        [Header("Connection (works with any provider)")]
        [Tooltip("Full request URL. Can contain {API_KEY} if your provider puts the key in the URL (e.g. Google Gemini).")]
        public string endpointTemplate = "";

        [Tooltip("Header name for auth, e.g. 'x-api-key' or 'Authorization'. Leave empty if the key only goes in the URL.")]
        public string authHeaderName = "";

        [Tooltip("Header value template, e.g. '{API_KEY}' or 'Bearer {API_KEY}'.")]
        public string authHeaderValueTemplate = "{API_KEY}";

        [Tooltip("Extra fixed headers this provider needs, one per line as 'Header-Name: value' (e.g. Anthropic needs 'anthropic-version: 2023-06-01').")]
        [TextArea(1, 4)]
        public string extraHeaders = "";

        [Header("Request body (raw JSON template)")]
        [Tooltip("Raw JSON sent as the POST body. Supports placeholders: {MODEL} {MAX_TOKENS} {SYSTEM_PROMPT} {USER_PROMPT} — the two prompt placeholders are auto JSON-escaped for you.")]
        [TextArea(4, 12)]
        public string requestBodyTemplate = "";

        [Header("Response parsing")]
        [Tooltip("Dot path to the reply text inside the JSON response, e.g. 'content.0.text' (Anthropic), 'choices.0.message.content' (OpenAI), 'candidates.0.content.parts.0.text' (Gemini).")]
        public string responseTextPath = "";

        [Header("Model")]
        public string model = "";
        public int maxTokens = 1024;

        [Tooltip("Leave empty and set at runtime via SetApiKeyAtRuntime() instead of committing a real key.")]
        [SerializeField] private string apiKey;

        public string ApiKey => apiKey;
        public void SetApiKeyAtRuntime(string key) => apiKey = key;

        public string ResolveEndpoint() => endpointTemplate
            .Replace("{API_KEY}", apiKey ?? "")
            .Replace("{MODEL}", model ?? "");

        /// <summary>Fills endpoint/auth/body/response-path defaults for a known provider. Custom leaves everything as-is.</summary>
        public void ApplyPreset()
        {
            switch (preset)
            {
                case Preset.Anthropic:
                    endpointTemplate = "https://api.anthropic.com/v1/messages";
                    authHeaderName = "x-api-key";
                    authHeaderValueTemplate = "{API_KEY}";
                    extraHeaders = "anthropic-version: 2023-06-01";
                    requestBodyTemplate =
                        "{\"model\":\"{MODEL}\",\"max_tokens\":{MAX_TOKENS},\"system\":\"{SYSTEM_PROMPT}\",\"messages\":[{\"role\":\"user\",\"content\":\"{USER_PROMPT}\"}]}";
                    responseTextPath = "content.0.text";
                    if (string.IsNullOrEmpty(model)) model = "claude-sonnet-4-6";
                    break;

                case Preset.OpenAI:
                    endpointTemplate = "https://api.openai.com/v1/chat/completions";
                    authHeaderName = "Authorization";
                    authHeaderValueTemplate = "Bearer {API_KEY}";
                    extraHeaders = "";
                    requestBodyTemplate =
                        "{\"model\":\"{MODEL}\",\"max_tokens\":{MAX_TOKENS},\"messages\":[{\"role\":\"system\",\"content\":\"{SYSTEM_PROMPT}\"},{\"role\":\"user\",\"content\":\"{USER_PROMPT}\"}]}";
                    responseTextPath = "choices.0.message.content";
                    if (string.IsNullOrEmpty(model)) model = "gpt-4o-mini";
                    break;

                case Preset.GoogleGemini:
                    endpointTemplate = "https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}";
                    authHeaderName = "";
                    authHeaderValueTemplate = "";
                    extraHeaders = "";
                    requestBodyTemplate =
                        "{\"contents\":[{\"role\":\"user\",\"parts\":[{\"text\":\"{SYSTEM_PROMPT}\\n\\n{USER_PROMPT}\"}]}]}";
                    responseTextPath = "candidates.0.content.parts.0.text";
                    if (string.IsNullOrEmpty(model)) model = "gemini-2.0-flash";
                    break;

                case Preset.Custom:
                default:
                    // Leave whatever the user has already entered untouched.
                    break;
            }
        }
    }
}
