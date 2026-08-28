using UnityEngine;

namespace RigAnimator.ObjectAnimator
{
    public enum EaseType
    {
        Linear,
        EaseInQuad,
        EaseOutQuad,
        EaseInOutQuad,
        EaseOutBack,
        EaseOutBounce
    }

    public static class EasingFunctions
    {
        public static float Evaluate(EaseType type, float t)
        {
            t = Mathf.Clamp01(t);
            switch (type)
            {
                case EaseType.EaseInQuad: return t * t;
                case EaseType.EaseOutQuad: return 1f - (1f - t) * (1f - t);
                case EaseType.EaseInOutQuad: return t < 0.5f ? 2f * t * t : 1f - Mathf.Pow(-2f * t + 2f, 2f) / 2f;
                case EaseType.EaseOutBack:
                {
                    const float c1 = 1.70158f;
                    const float c3 = c1 + 1f;
                    return 1f + c3 * Mathf.Pow(t - 1f, 3f) + c1 * Mathf.Pow(t - 1f, 2f);
                }
                case EaseType.EaseOutBounce:
                {
                    const float n1 = 7.5625f;
                    const float d1 = 2.75f;
                    if (t < 1f / d1) return n1 * t * t;
                    if (t < 2f / d1) { t -= 1.5f / d1; return n1 * t * t + 0.75f; }
                    if (t < 2.5f / d1) { t -= 2.25f / d1; return n1 * t * t + 0.9375f; }
                    t -= 2.625f / d1; return n1 * t * t + 0.984375f;
                }
                default: return t;
            }
        }

        public static bool TryParse(string name, out EaseType type)
        {
            return System.Enum.TryParse(name, true, out type);
        }
    }
}
