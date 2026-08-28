using System.Collections.Generic;
using UnityEngine;

namespace RigAnimator.Core
{
    /// <summary>
    /// Single entry point for the whole system. Drop this on your rig root,
    /// wire up the three layer components (or let it find them in children),
    /// and call Execute()/ExecuteBatch() from gameplay code, Timeline signals,
    /// or the AI driver.
    /// </summary>
    [DisallowMultipleComponent]
    [AddComponentMenu("Rig Animator/Rig Animator Controller")]
    public class RigAnimatorController : MonoBehaviour
    {
        [Tooltip("If left empty, executors are auto-discovered on this object and its children on Awake.")]
        [SerializeField] private List<MonoBehaviour> explicitExecutors = new List<MonoBehaviour>();

        private readonly List<IAnimationExecutor> _executors = new List<IAnimationExecutor>();

        public IReadOnlyList<IAnimationExecutor> Executors => _executors;

        private void Awake()
        {
            _executors.Clear();

            if (explicitExecutors != null && explicitExecutors.Count > 0)
            {
                foreach (var mb in explicitExecutors)
                {
                    if (mb is IAnimationExecutor exec)
                        _executors.Add(exec);
                    else if (mb != null)
                        Debug.LogWarning($"RigAnimatorController: '{mb.name}' does not implement IAnimationExecutor and was skipped.", this);
                }
            }
            else
            {
                foreach (var mb in GetComponentsInChildren<MonoBehaviour>(true))
                {
                    if (mb is IAnimationExecutor exec)
                        _executors.Add(exec);
                }
            }

            if (_executors.Count == 0)
                Debug.LogWarning("RigAnimatorController: no IAnimationExecutor components found. Add a ProceduralAnimator, ClipAnimationPlayer, and/or SimpleObjectAnimator.", this);
        }

        /// <summary>Register an executor at runtime (e.g. one created procedurally).</summary>
        public void RegisterExecutor(IAnimationExecutor executor)
        {
            if (executor != null && !_executors.Contains(executor))
                _executors.Add(executor);
        }

        /// <summary>Routes a single command to the first matching executor.</summary>
        public bool Execute(AnimationCommand command)
        {
            if (command == null) return false;

            foreach (var executor in _executors)
            {
                if (executor.Layer == command.layer && executor.CanExecute(command))
                {
                    executor.Execute(command);
                    return true;
                }
            }

            Debug.LogWarning($"RigAnimatorController: no executor could handle layer={command.layer}, target='{command.target}', action='{command.action}'.", this);
            return false;
        }

        /// <summary>Routes a batch of commands (e.g. everything the AI returned for one prompt).</summary>
        public void ExecuteBatch(IEnumerable<AnimationCommand> commands)
        {
            if (commands == null) return;
            foreach (var command in commands)
                Execute(command);
        }
    }
}
