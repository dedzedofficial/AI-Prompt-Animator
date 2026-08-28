using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using RigAnimator.Core;

namespace RigAnimator.AI
{
    /// <summary>
    /// ==================================================================
    ///  Rig Animator — v0.1 Beta
    ///  Created by FISHHWB
    ///  Discord: https://discord.gg/vCcsnX4HQP
    /// ==================================================================
    ///
    /// Turns a typed prompt into animation commands using ANY AI provider's
    /// API key — Anthropic, OpenAI, Gemini, a self-hosted model, anything
    /// that accepts a JSON POST and returns JSON. See AIProviderSettings for
    /// the connection template. Nothing about this class is vendor-specific;
    /// swapping providers means changing the settings asset, not the code.
    ///
    /// DISCLAIMER: This is beta software (v0.1). AI responses are not
    /// guaranteed to be well-formed, safe, or correct — always sanity-check
    /// commands before relying on this in a shipped product. Calling a
    /// third-party AI API from this driver sends your prompt (and whatever
    /// capability description you configure) to that provider, is subject to
    /// that provider's own terms, pricing, and rate limits, and calling
    /// directly from a client build embeds your API key in that build. See
    /// the README/DISCLAIMER.md included with this package before shipping
    /// anything built on this tool.
    /// </summary>
    [RequireComponent(typeof(RigAnimatorController))]
    [AddComponentMenu("Rig Animator/AI Animation Driver")]
    public class AIAnimationDriver : MonoBehaviour
    {
        [SerializeField] private AIProviderSettings settings;

        [TextArea(3, 8)]
        [SerializeField]
        private string systemPromptTemplate =
            "You control animation for a Unity character/object rig by returning ONLY JSON, no prose, no markdown fences.\n" +
            "Schema:\n" +
            "{ \"commands\": [ { \"layer\": \"Procedural|Clip|SimpleTransform\", \"target\": string, \"action\": string, " +
            "\"floatParams\": {\"x\":number,...}, \"stringParams\": {\"ease\":string,...} } ] }\n" +
            "Known targets and actions:\n{0}\n" +
            "Only reference targets/actions from that list. Respond with the JSON object and nothing else.";

        [Tooltip("Human-readable description of available targets/actions injected into the system prompt so the AI only issues valid commands.")]
        [TextArea(3, 8)]
        [SerializeField] private string knownCapabilitiesDescription =
            "Procedural: ik_reach(target=<chain>, x,y,z, duration, weight), look_at(target=<bone>, x,y,z, speed, weight), stop(target)\n" +
            "Clip: play(target=<clip name>, fade, speed, loopCount), stop(target=<clip name or \"*\">, fade)\n" +
            "SimpleTransform: move_to/rotate_to/scale_to(target=<object name>, x,y,z, duration, ease), stop(target)";

        private RigAnimatorController _controller;

        public event Action<string> OnRawResponse;
        public event Action<Exception> OnError;

        private void Awake()
        {
            _controller = GetComponent<RigAnimatorController>();
        }

        /// <summary>Fire-and-forget: sends the prompt and executes whatever commands come back.</summary>
        public void RequestAnimation(string naturalLanguagePrompt)
        {
            StartCoroutine(RequestAnimationRoutine(naturalLanguagePrompt, null));
        }

        /// <summary>Same as RequestAnimation but invokes a callback with the parsed commands before executing them, so callers can inspect/veto.</summary>
        public void RequestAnimation(string naturalLanguagePrompt, Action<System.Collections.Generic.List<AnimationCommand>> onParsed)
        {
            StartCoroutine(RequestAnimationRoutine(naturalLanguagePrompt, onParsed));
        }

        private IEnumerator RequestAnimationRoutine(string prompt, Action<System.Collections.Generic.List<AnimationCommand>> onParsed)
        {
            if (settings == null)
            {
                Fail(new InvalidOperationException("AIAnimationDriver: no AIProviderSettings assigned."));
                yield break;
            }

            if (string.IsNullOrEmpty(settings.ApiKey))
            {
                Fail(new InvalidOperationException(
                    "AIAnimationDriver: AIProviderSettings.ApiKey is empty. Paste a key into the asset for local testing, " +
                    "or call settings.SetApiKeyAtRuntime(key) to supply it from an env var / your own server instead."));
                yield break;
            }

            if (string.IsNullOrEmpty(settings.endpointTemplate) || string.IsNullOrEmpty(settings.requestBodyTemplate))
            {
                Fail(new InvalidOperationException(
                    "AIAnimationDriver: AIProviderSettings is missing an endpoint or request body template. Pick a Preset and click Apply Preset, or fill in a Custom template."));
                yield break;
            }

            string systemPrompt = string.Format(systemPromptTemplate, knownCapabilitiesDescription);
            string endpoint = settings.ResolveEndpoint();
            string body = BuildBody(settings, systemPrompt, prompt);

            using var request = new UnityWebRequest(endpoint, "POST");
            byte[] payload = Encoding.UTF8.GetBytes(body);
            request.uploadHandler = new UploadHandlerRaw(payload);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            if (!string.IsNullOrEmpty(settings.authHeaderName))
            {
                string headerValue = settings.authHeaderValueTemplate.Replace("{API_KEY}", settings.ApiKey);
                request.SetRequestHeader(settings.authHeaderName, headerValue);
            }

            foreach (var line in SplitLines(settings.extraHeaders))
            {
                int colon = line.IndexOf(':');
                if (colon <= 0) continue;
                request.SetRequestHeader(line.Substring(0, colon).Trim(), line.Substring(colon + 1).Trim());
            }

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Fail(new Exception($"AIAnimationDriver: request failed ({request.result}): {request.error}\n{request.downloadHandler?.text}"));
                yield break;
            }

            string responseText = request.downloadHandler.text;
            OnRawResponse?.Invoke(responseText);

            string modelText;
            try
            {
                object parsedResponse = MiniJson.Parse(responseText);
                object extracted = MiniJson.GetPath(parsedResponse, settings.responseTextPath);
                if (extracted == null)
                    throw new FormatException($"Response path '{settings.responseTextPath}' did not resolve to anything in the response.");
                modelText = extracted.ToString();
            }
            catch (Exception e)
            {
                Fail(new Exception($"AIAnimationDriver: could not read reply text from response using path '{settings.responseTextPath}' — {e.Message}\nRaw response: {responseText}"));
                yield break;
            }

            System.Collections.Generic.List<AnimationCommand> commands;
            try
            {
                commands = CommandJsonParser.Parse(modelText);
                if (commands.Count == 0)
                    Debug.LogWarning($"AIAnimationDriver: parsed zero commands from the AI's reply. Raw reply: {modelText}", this);
            }
            catch (Exception e)
            {
                Fail(new Exception($"AIAnimationDriver: AI reply was not valid command JSON — {e.Message}\nRaw reply: {modelText}"));
                yield break;
            }

            onParsed?.Invoke(commands);
            _controller.ExecuteBatch(commands);
        }

        private static string BuildBody(AIProviderSettings settings, string systemPrompt, string userPrompt)
        {
            return settings.requestBodyTemplate
                .Replace("{MODEL}", settings.model)
                .Replace("{MAX_TOKENS}", settings.maxTokens.ToString())
                .Replace("{SYSTEM_PROMPT}", MiniJson.Escape(systemPrompt))
                .Replace("{USER_PROMPT}", MiniJson.Escape(userPrompt));
        }

        private static System.Collections.Generic.IEnumerable<string> SplitLines(string text)
        {
            if (string.IsNullOrEmpty(text)) yield break;
            foreach (var line in text.Split('\n'))
            {
                var trimmed = line.Trim();
                if (trimmed.Length > 0) yield return trimmed;
            }
        }

        private void Fail(Exception e)
        {
            Debug.LogError(e.Message, this);
            OnError?.Invoke(e);
        }
    }
}
