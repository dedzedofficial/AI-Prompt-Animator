using System.Collections.Generic;
using RigAnimator.Core;

namespace RigAnimator.AI
{
    /// <summary>
    /// Rig Animator v0.1 Beta — Created by FISHHWB
    ///
    /// Different AI providers/models don't always format JSON identically
    /// (some nest params as arrays of {key,value}, some as a flat object,
    /// some wrap a single command instead of a batch). This reads the
    /// generic MiniJson object graph defensively rather than requiring one
    /// exact schema, so "any AI" is more than a slogan.
    /// </summary>
    public static class CommandJsonParser
    {
        public static List<AnimationCommand> Parse(string modelText)
        {
            var result = new List<AnimationCommand>();
            string json = StripMarkdownFences(modelText).Trim();

            object root = MiniJson.Parse(json);
            if (root == null) return result;

            List<object> commandList;

            if (root is Dictionary<string, object> rootDict && rootDict.TryGetValue("commands", out var commandsObj) && commandsObj is List<object> list)
                commandList = list;
            else if (root is List<object> topLevelList)
                commandList = topLevelList; // model returned a bare array instead of {"commands":[...]}
            else if (root is Dictionary<string, object>)
                commandList = new List<object> { root }; // model returned a single command object, not a batch
            else
                return result;

            foreach (var entry in commandList)
            {
                if (entry is Dictionary<string, object> dict)
                {
                    var cmd = ParseSingle(dict);
                    if (cmd != null) result.Add(cmd);
                }
            }

            return result;
        }

        private static AnimationCommand ParseSingle(Dictionary<string, object> dict)
        {
            string layerStr = GetString(dict, "layer");
            if (string.IsNullOrEmpty(layerStr) || !System.Enum.TryParse<AnimationLayer>(layerStr, true, out var layer))
                return null;

            var cmd = new AnimationCommand
            {
                layer = layer,
                target = GetString(dict, "target"),
                action = GetString(dict, "action")
            };

            ReadParams(dict, "floatParams", cmd.floatParams);
            ReadParams(dict, "stringParams", cmd.stringParams);

            return cmd;
        }

        private static void ReadParams(Dictionary<string, object> dict, string key, Dictionary<string, float> target)
        {
            if (!dict.TryGetValue(key, out var raw)) return;

            if (raw is List<object> pairList)
            {
                // [{"key":"x","value":1.2}, ...]
                foreach (var item in pairList)
                {
                    if (item is Dictionary<string, object> pair &&
                        pair.TryGetValue("key", out var k) &&
                        pair.TryGetValue("value", out var v))
                    {
                        target[k.ToString()] = System.Convert.ToSingle(v);
                    }
                }
            }
            else if (raw is Dictionary<string, object> flatDict)
            {
                // {"x": 1.2, "y": 0.5}
                foreach (var kvp in flatDict)
                {
                    if (kvp.Value is double d) target[kvp.Key] = (float)d;
                    else if (float.TryParse(kvp.Value?.ToString(), out var f)) target[kvp.Key] = f;
                }
            }
        }

        private static void ReadParams(Dictionary<string, object> dict, string key, Dictionary<string, string> target)
        {
            if (!dict.TryGetValue(key, out var raw)) return;

            if (raw is List<object> pairList)
            {
                foreach (var item in pairList)
                {
                    if (item is Dictionary<string, object> pair &&
                        pair.TryGetValue("key", out var k) &&
                        pair.TryGetValue("value", out var v))
                    {
                        target[k.ToString()] = v?.ToString();
                    }
                }
            }
            else if (raw is Dictionary<string, object> flatDict)
            {
                foreach (var kvp in flatDict)
                    target[kvp.Key] = kvp.Value?.ToString();
            }
        }

        private static string GetString(Dictionary<string, object> dict, string key)
            => dict.TryGetValue(key, out var v) ? v?.ToString() : null;

        private static string StripMarkdownFences(string text)
        {
            text = text.Trim();
            if (text.StartsWith("```"))
            {
                int firstNewline = text.IndexOf('\n');
                if (firstNewline >= 0) text = text.Substring(firstNewline + 1);
                int lastFence = text.LastIndexOf("```", System.StringComparison.Ordinal);
                if (lastFence >= 0) text = text.Substring(0, lastFence);
            }
            return text;
        }
    }
}
