using System.Collections.Generic;
using UnityEngine;
using RigAnimator.Core;

namespace RigAnimator.ObjectAnimator
{
    /// <summary>
    /// Transform-level tweening for plain objects — no rig, no clips.
    /// Multiple named targets can live under one controller (e.g. a prop,
    /// a door, a camera rig): register them in the inspector by name and
    /// drive them with commands.
    ///
    /// Supported actions:
    ///   "move_to"    target=<object name>  floatParams: x,y,z, duration   stringParams: ease, space ("world"/"local")
    ///   "rotate_to"  target=<object name>  floatParams: x,y,z, duration   stringParams: ease (euler degrees)
    ///   "scale_to"   target=<object name>  floatParams: x,y,z, duration   stringParams: ease
    ///   "stop"       target=<object name or "*">
    /// </summary>
    [AddComponentMenu("Rig Animator/Simple Object Animator")]
    public class SimpleObjectAnimator : MonoBehaviour, IAnimationExecutor
    {
        [System.Serializable]
        public class NamedTarget
        {
            public string name;
            public Transform transform;
        }

        [SerializeField] private List<NamedTarget> targets = new List<NamedTarget>();

        private class Tween
        {
            public Transform transform;
            public string kind; // "move" | "rotate" | "scale"
            public Vector3 from;
            public Vector3 to;
            public float duration;
            public float elapsed;
            public EaseType ease;
            public bool worldSpace;
        }

        private readonly Dictionary<Transform, List<Tween>> _tweensByTransform = new Dictionary<Transform, List<Tween>>();

        public AnimationLayer Layer => AnimationLayer.SimpleTransform;

        public bool CanExecute(AnimationCommand command)
        {
            if (command.action == "stop") return true; // "*" is always valid
            return FindTarget(command.target) != null;
        }

        public void Execute(AnimationCommand command)
        {
            switch (command.action)
            {
                case "move_to": StartTween(command, "move"); break;
                case "rotate_to": StartTween(command, "rotate"); break;
                case "scale_to": StartTween(command, "scale"); break;
                case "stop": Stop(command.target); break;
            }
        }

        private Transform FindTarget(string targetName)
        {
            var def = targets.Find(t => t.name == targetName);
            return def?.transform;
        }

        private void StartTween(AnimationCommand command, string kind)
        {
            var t = FindTarget(command.target);
            if (t == null)
            {
                Debug.LogWarning($"SimpleObjectAnimator: no target registered under name '{command.target}'.", this);
                return;
            }

            bool worldSpace = command.GetString("space", "world") != "local";
            Vector3 to = new Vector3(command.GetFloat("x"), command.GetFloat("y"), command.GetFloat("z"));
            float duration = Mathf.Max(0.0001f, command.GetFloat("duration", 0.5f));

            EasingFunctions.TryParse(command.GetString("ease", "EaseInOutQuad"), out var ease);

            Vector3 from = kind switch
            {
                "move" => worldSpace ? t.position : t.localPosition,
                "rotate" => worldSpace ? t.eulerAngles : t.localEulerAngles,
                "scale" => t.localScale,
                _ => Vector3.zero
            };

            var tween = new Tween
            {
                transform = t,
                kind = kind,
                from = from,
                to = to,
                duration = duration,
                elapsed = 0f,
                ease = ease,
                worldSpace = worldSpace
            };

            if (!_tweensByTransform.TryGetValue(t, out var list))
            {
                list = new List<Tween>();
                _tweensByTransform[t] = list;
            }
            // Only one active tween per kind per transform, so a new move_to
            // cleanly replaces an in-flight one instead of fighting it.
            list.RemoveAll(existing => existing.kind == kind);
            list.Add(tween);
        }

        public void Stop(string targetName)
        {
            if (targetName == "*")
            {
                _tweensByTransform.Clear();
                return;
            }

            var t = FindTarget(targetName);
            if (t != null) _tweensByTransform.Remove(t);
        }

        private void Update()
        {
            List<Transform> toRemove = null;

            foreach (var kvp in _tweensByTransform)
            {
                var list = kvp.Value;
                for (int i = list.Count - 1; i >= 0; i--)
                {
                    var tw = list[i];
                    tw.elapsed += Time.deltaTime;
                    float t01 = Mathf.Clamp01(tw.elapsed / tw.duration);
                    float eased = EasingFunctions.Evaluate(tw.ease, t01);
                    Vector3 value = Vector3.LerpUnclamped(tw.from, tw.to, eased);

                    switch (tw.kind)
                    {
                        case "move":
                            if (tw.worldSpace) tw.transform.position = value; else tw.transform.localPosition = value;
                            break;
                        case "rotate":
                            if (tw.worldSpace) tw.transform.eulerAngles = value; else tw.transform.localEulerAngles = value;
                            break;
                        case "scale":
                            tw.transform.localScale = value;
                            break;
                    }

                    if (t01 >= 1f) list.RemoveAt(i);
                }

                if (list.Count == 0)
                {
                    toRemove ??= new List<Transform>();
                    toRemove.Add(kvp.Key);
                }
            }

            if (toRemove != null)
                foreach (var t in toRemove) _tweensByTransform.Remove(t);
        }
    }
}
