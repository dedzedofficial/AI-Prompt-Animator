using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Playables;
using UnityEngine.Animations;
using RigAnimator.Core;

namespace RigAnimator.ClipBased
{
    /// <summary>
    /// Plays and cross-fades named AnimationClips through a PlayableGraph,
    /// independent of any Animator Controller state machine. Good for
    /// AI-driven or ad-hoc clip playback where you don't want to author
    /// transitions in advance.
    ///
    /// Supported actions:
    ///   "play"  target=<clip name>   floatParams: fade (seconds), speed, loopCount (0 = loop forever)
    ///   "stop"  target=<clip name or "*"> floatParams: fade (seconds)
    /// </summary>
    [RequireComponent(typeof(Animator))]
    [AddComponentMenu("Rig Animator/Clip Animation Player")]
    public class ClipAnimationPlayer : MonoBehaviour, IAnimationExecutor
    {
        [System.Serializable]
        public class NamedClip
        {
            public string name;
            public AnimationClip clip;
        }

        [SerializeField] private List<NamedClip> clips = new List<NamedClip>();
        [SerializeField] private float defaultFadeSeconds = 0.25f;

        private PlayableGraph _graph;
        private AnimationMixerPlayable _mixer;
        private Animator _animator;

        private class ActiveClip
        {
            public string name;
            public AnimationClipPlayable playable;
            public int mixerPort;
            public float targetWeight;
            public float fadeSpeed; // weight units per second
            public bool fadingOut;
        }

        private readonly List<ActiveClip> _active = new List<ActiveClip>();

        public AnimationLayer Layer => AnimationLayer.Clip;

        private void Awake()
        {
            _animator = GetComponent<Animator>();
            _graph = PlayableGraph.Create($"{name}_ClipGraph");
            _graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);

            _mixer = AnimationMixerPlayable.Create(_graph, 0, true);
            var output = AnimationPlayableOutput.Create(_graph, "RigAnimatorOutput", _animator);
            output.SetSourcePlayable(_mixer);

            _graph.Play();
        }

        private void OnDestroy()
        {
            if (_graph.IsValid())
                _graph.Destroy();
        }

        public bool CanExecute(AnimationCommand command)
        {
            if (command.action == "stop") return true; // "*" always valid
            return FindClipDef(command.target) != null;
        }

        public void Execute(AnimationCommand command)
        {
            switch (command.action)
            {
                case "play":
                    Play(command.target,
                        fadeSeconds: command.GetFloat("fade", defaultFadeSeconds),
                        speed: command.GetFloat("speed", 1f),
                        loopCount: Mathf.RoundToInt(command.GetFloat("loopCount", 0f)));
                    break;

                case "stop":
                    Stop(command.target, command.GetFloat("fade", defaultFadeSeconds));
                    break;
            }
        }

        private NamedClip FindClipDef(string clipName) => clips.Find(c => c.name == clipName);

        public void Play(string clipName, float fadeSeconds, float speed = 1f, int loopCount = 0)
        {
            var def = FindClipDef(clipName);
            if (def == null || def.clip == null)
            {
                Debug.LogWarning($"ClipAnimationPlayer: no clip registered under name '{clipName}'.", this);
                return;
            }

            // Fade out anything currently playing.
            foreach (var existing in _active)
            {
                if (!existing.fadingOut)
                {
                    existing.fadingOut = true;
                    existing.targetWeight = 0f;
                    existing.fadeSpeed = fadeSeconds > 0f ? 1f / fadeSeconds : 999f;
                }
            }

            int port = _mixer.GetInputCount();
            _mixer.SetInputCount(port + 1);

            var playable = AnimationClipPlayable.Create(_graph, def.clip);
            playable.SetSpeed(speed);
            playable.SetApplyFootIK(false);

            if (loopCount <= 0)
            {
                // Unity handles wrap mode via the clip's own settings for looping;
                // for explicit infinite loop we simply never remove it until stopped.
            }

            _graph.Connect(playable, 0, _mixer, port);
            _mixer.SetInputWeight(port, 0f);

            _active.Add(new ActiveClip
            {
                name = clipName,
                playable = playable,
                mixerPort = port,
                targetWeight = 1f,
                fadeSpeed = fadeSeconds > 0f ? 1f / fadeSeconds : 999f,
                fadingOut = false
            });
        }

        public void Stop(string clipName, float fadeSeconds)
        {
            foreach (var existing in _active)
            {
                if (clipName == "*" || existing.name == clipName)
                {
                    existing.fadingOut = true;
                    existing.targetWeight = 0f;
                    existing.fadeSpeed = fadeSeconds > 0f ? 1f / fadeSeconds : 999f;
                }
            }
        }

        private void Update()
        {
            for (int i = _active.Count - 1; i >= 0; i--)
            {
                var a = _active[i];
                float current = _mixer.GetInputWeight(a.mixerPort);
                float next = Mathf.MoveTowards(current, a.targetWeight, a.fadeSpeed * Time.deltaTime);
                _mixer.SetInputWeight(a.mixerPort, next);

                if (a.fadingOut && next <= 0f)
                {
                    if (a.playable.IsValid())
                        a.playable.Destroy();
                    _active.RemoveAt(i);
                }
            }

            NormalizeWeights();
        }

        private void NormalizeWeights()
        {
            float total = 0f;
            foreach (var a in _active) total += _mixer.GetInputWeight(a.mixerPort);
            if (total <= 1f || total <= 0.0001f) return;

            foreach (var a in _active)
                _mixer.SetInputWeight(a.mixerPort, _mixer.GetInputWeight(a.mixerPort) / total);
        }
    }
}
