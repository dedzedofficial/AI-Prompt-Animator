using UnityEditor;
using UnityEngine;
using RigAnimator.AI;

namespace RigAnimator.Editor
{
    [CustomEditor(typeof(AIAnimationDriver))]
    public class AIAnimationDriverEditor : UnityEditor.Editor
    {
        private string _testPrompt = "Raise the right hand and look at the player.";

        public override void OnInspectorGUI()
        {
            EditorGUILayout.HelpBox(
                "Rig Animator v0.1 Beta — Created by FISHHWB\n" +
                "This sends your prompt to whatever AI provider is configured in the assigned Provider Settings asset. " +
                "Beta software: verify AI output before shipping. See DISCLAIMER.md.",
                MessageType.Info);

            DrawDefaultInspector();

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Play Mode Test", EditorStyles.boldLabel);

            if (!Application.isPlaying)
            {
                EditorGUILayout.HelpBox("Enter Play Mode to test a prompt against the live rig.", MessageType.Info);
                return;
            }

            _testPrompt = EditorGUILayout.TextField("Prompt", _testPrompt);

            if (GUILayout.Button("Send Test Prompt"))
            {
                var driver = (AIAnimationDriver)target;
                driver.RequestAnimation(_testPrompt);
            }
        }
    }

    [CustomEditor(typeof(AIProviderSettings))]
    public class AIProviderSettingsEditor : UnityEditor.Editor
    {
        public override void OnInspectorGUI()
        {
            EditorGUILayout.HelpBox(
                "Works with ANY AI provider — paste in that provider's API key and adjust the endpoint/body/response " +
                "path templates to match its API. Pick a Preset and click 'Apply Preset' for a working starting point " +
                "for Anthropic, OpenAI, or Google Gemini, then edit freely.",
                MessageType.Info);

            DrawDefaultInspector();

            EditorGUILayout.Space();
            if (GUILayout.Button("Apply Preset"))
            {
                var settings = (AIProviderSettings)target;
                Undo.RecordObject(settings, "Apply AI Provider Preset");
                settings.ApplyPreset();
                EditorUtility.SetDirty(settings);
            }

            EditorGUILayout.Space();
            EditorGUILayout.HelpBox(
                "Avoid committing a real API key into this asset if the project is under version control. " +
                "Prefer leaving the key field empty and calling SetApiKeyAtRuntime() from code instead.",
                MessageType.Warning);
        }
    }
}
