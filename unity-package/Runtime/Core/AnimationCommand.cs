using System;
using System.Collections.Generic;

namespace RigAnimator.Core
{
    /// <summary>
    /// The three animation layers a command can be routed to.
    /// </summary>
    public enum AnimationLayer
    {
        Procedural,
        Clip,
        SimpleTransform
    }

    /// <summary>
    /// A single, serializable animation instruction. This is the common
    /// currency between hand-written code, timeline-driven calls, and the
    /// AI driver (which fills these in from a parsed JSON response).
    /// </summary>
    [Serializable]
    public class AnimationCommand
    {
        public AnimationLayer layer;

        /// <summary>Name of the target (bone, object, or clip identifier). Resolved by RigAnimatorController.</summary>
        public string target;

        /// <summary>Verb describing what to do, e.g. "look_at", "play", "move_to", "ik_reach".</summary>
        public string action;

        /// <summary>Free-form numeric parameters (position, duration, weight, speed, etc).</summary>
        public Dictionary<string, float> floatParams = new Dictionary<string, float>();

        /// <summary>Free-form string parameters (clip name, easing type, loop mode, etc).</summary>
        public Dictionary<string, string> stringParams = new Dictionary<string, string>();

        public float GetFloat(string key, float fallback = 0f)
            => floatParams != null && floatParams.TryGetValue(key, out var v) ? v : fallback;

        public string GetString(string key, string fallback = null)
            => stringParams != null && stringParams.TryGetValue(key, out var v) ? v : fallback;
    }
}
