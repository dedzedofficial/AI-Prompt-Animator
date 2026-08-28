namespace RigAnimator.Core
{
    /// <summary>
    /// Implemented by each animation layer (procedural, clip-based, simple
    /// transform). RigAnimatorController routes commands to whichever
    /// executor matches AnimationCommand.layer.
    /// </summary>
    public interface IAnimationExecutor
    {
        AnimationLayer Layer { get; }

        /// <summary>True if this executor recognizes the target/action pair.</summary>
        bool CanExecute(AnimationCommand command);

        /// <summary>Fire-and-forget execution. Implementations manage their own coroutines/updates.</summary>
        void Execute(AnimationCommand command);
    }
}
