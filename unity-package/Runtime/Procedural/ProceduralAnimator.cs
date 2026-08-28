using System.Collections.Generic;
using UnityEngine;
using RigAnimator.Core;

namespace RigAnimator.Procedural
{
    /// <summary>
    /// Drives bones/objects directly every frame: two-bone IK reaches and
    /// smoothed look-at constraints. No AnimationClips involved — this is
    /// for runtime-computed motion (reaching for a point, aiming, tracking).
    ///
    /// Supported actions:
    ///   "ik_reach"  target=<chain name>   floatParams: x,y,z (world target), duration, weight
    ///   "look_at"   target=<bone name>    floatParams: x,y,z (world target), speed
    ///   "stop"      target=<chain or bone name>
    /// </summary>
    [AddComponentMenu("Rig Animator/Procedural Animator")]
    public class ProceduralAnimator : MonoBehaviour, IAnimationExecutor
    {
        [System.Serializable]
        public class IKChain
        {
            public string name;
            public Transform root;   // e.g. upper arm
            public Transform mid;    // e.g. forearm
            public Transform tip;    // e.g. hand
            [Range(0f, 1f)] public float weight = 1f;
            [HideInInspector] public Vector3 targetPosition;
            [HideInInspector] public bool active;
            [HideInInspector] public float blendSpeed = 4f;
            [HideInInspector] public float currentWeight;
        }

        [System.Serializable]
        public class LookAtBone
        {
            public string name;
            public Transform bone;
            [Range(0f, 1f)] public float weight = 1f;
            [HideInInspector] public Vector3 targetPosition;
            [HideInInspector] public bool active;
            [HideInInspector] public float turnSpeedDegPerSec = 180f;
        }

        [SerializeField] private List<IKChain> ikChains = new List<IKChain>();
        [SerializeField] private List<LookAtBone> lookAtBones = new List<LookAtBone>();

        public AnimationLayer Layer => AnimationLayer.Procedural;

        public bool CanExecute(AnimationCommand command)
        {
            switch (command.action)
            {
                case "ik_reach": return FindChain(command.target) != null;
                case "look_at": return FindLookAt(command.target) != null;
                case "stop": return FindChain(command.target) != null || FindLookAt(command.target) != null;
                default: return false;
            }
        }

        public void Execute(AnimationCommand command)
        {
            switch (command.action)
            {
                case "ik_reach":
                {
                    var chain = FindChain(command.target);
                    if (chain == null) return;
                    chain.targetPosition = new Vector3(
                        command.GetFloat("x"), command.GetFloat("y"), command.GetFloat("z"));
                    chain.weight = Mathf.Clamp01(command.GetFloat("weight", 1f));
                    float duration = Mathf.Max(0.01f, command.GetFloat("duration", 0.25f));
                    chain.blendSpeed = 1f / duration;
                    chain.active = true;
                    break;
                }
                case "look_at":
                {
                    var look = FindLookAt(command.target);
                    if (look == null) return;
                    look.targetPosition = new Vector3(
                        command.GetFloat("x"), command.GetFloat("y"), command.GetFloat("z"));
                    look.turnSpeedDegPerSec = command.GetFloat("speed", 180f);
                    look.weight = Mathf.Clamp01(command.GetFloat("weight", 1f));
                    look.active = true;
                    break;
                }
                case "stop":
                {
                    var chain = FindChain(command.target);
                    if (chain != null) chain.active = false;
                    var look = FindLookAt(command.target);
                    if (look != null) look.active = false;
                    break;
                }
            }
        }

        private IKChain FindChain(string name) => ikChains.Find(c => c.name == name);
        private LookAtBone FindLookAt(string name) => lookAtBones.Find(l => l.name == name);

        private void LateUpdate()
        {
            foreach (var chain in ikChains)
            {
                if (!chain.active || chain.root == null || chain.mid == null || chain.tip == null) continue;

                chain.currentWeight = Mathf.MoveTowards(chain.currentWeight, chain.weight, chain.blendSpeed * Time.deltaTime);
                if (chain.currentWeight <= 0f) continue;

                SolveTwoBoneIK(chain.root, chain.mid, chain.tip, chain.targetPosition, chain.currentWeight);
            }

            foreach (var look in lookAtBones)
            {
                if (!look.active || look.bone == null) continue;

                Vector3 dir = (look.targetPosition - look.bone.position);
                if (dir.sqrMagnitude < 0.0001f) continue;

                Quaternion desired = Quaternion.LookRotation(dir.normalized, Vector3.up);
                Quaternion desiredBlended = Quaternion.Slerp(look.bone.rotation, desired, look.weight);
                look.bone.rotation = Quaternion.RotateTowards(
                    look.bone.rotation, desiredBlended, look.turnSpeedDegPerSec * Time.deltaTime);
            }
        }

        /// <summary>
        /// Classic analytic two-bone IK (law of cosines). Rotates root and mid
        /// so tip reaches as close to targetPos as the chain's total length allows,
        /// blended by weight so it composes cleanly with underlying animation.
        /// </summary>
        private static void SolveTwoBoneIK(Transform root, Transform mid, Transform tip, Vector3 targetPos, float weight)
        {
            float upperLen = Vector3.Distance(root.position, mid.position);
            float lowerLen = Vector3.Distance(mid.position, tip.position);
            float maxReach = upperLen + lowerLen;

            Vector3 toTarget = targetPos - root.position;
            float targetDist = Mathf.Clamp(toTarget.magnitude, 0.0001f, maxReach - 0.0001f);

            float cosAngle = Mathf.Clamp(
                (upperLen * upperLen + targetDist * targetDist - lowerLen * lowerLen) / (2f * upperLen * targetDist),
                -1f, 1f);
            float rootAngle = Mathf.Acos(cosAngle) * Mathf.Rad2Deg;

            float cosMid = Mathf.Clamp(
                (upperLen * upperLen + lowerLen * lowerLen - targetDist * targetDist) / (2f * upperLen * lowerLen),
                -1f, 1f);
            float midAngle = Mathf.Acos(cosMid) * Mathf.Rad2Deg;

            Vector3 poleAxis = Vector3.Cross(toTarget.normalized, root.up).normalized;
            if (poleAxis.sqrMagnitude < 0.0001f) poleAxis = root.right;

            Quaternion rootLook = Quaternion.LookRotation(toTarget.normalized, root.up);
            Quaternion rootTarget = Quaternion.AngleAxis(-rootAngle, poleAxis) * rootLook;
            Quaternion midTarget = Quaternion.AngleAxis(180f - midAngle, poleAxis) * rootLook;

            root.rotation = Quaternion.Slerp(root.rotation, rootTarget, weight);
            mid.rotation = Quaternion.Slerp(mid.rotation, midTarget, weight);
        }
    }
}
