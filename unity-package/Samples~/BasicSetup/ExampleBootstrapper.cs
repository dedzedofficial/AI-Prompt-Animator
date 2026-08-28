using UnityEngine;
using RigAnimator.AI;

namespace RigAnimator.Samples
{
    /// <summary>
    /// Rig Animator v0.1 Beta — Created by FISHHWB
    ///
    /// Reference for wiring a prompt input (e.g. a UI InputField) to
    /// AIAnimationDriver, and for supplying an API key at runtime rather
    /// than pasting a real one into the AIProviderSettings asset. Not
    /// required for the system to work.
    /// </summary>
    public class ExampleBootstrapper : MonoBehaviour
    {
        [SerializeField] private AIProviderSettings aiSettings;
        [SerializeField] private AIAnimationDriver driver;

        private void Start()
        {
            // Example: pull the key from an environment variable at startup
            // instead of typing a real one into the settings asset. Works
            // the same regardless of which provider is configured.
            string key = System.Environment.GetEnvironmentVariable("RIG_ANIMATOR_API_KEY");
            if (!string.IsNullOrEmpty(key) && aiSettings != null)
                aiSettings.SetApiKeyAtRuntime(key);
        }

        // Wire this to a UI input field's OnSubmit, or call it from anywhere,
        // e.g. SendPrompt("wave hello and turn to face the camera").
        public void SendPrompt(string prompt)
        {
            if (driver == null)
            {
                Debug.LogWarning("ExampleBootstrapper: no AIAnimationDriver assigned.");
                return;
            }
            driver.RequestAnimation(prompt);
        }
    }
}
