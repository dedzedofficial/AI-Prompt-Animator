using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace RigAnimator.AI
{
    /// <summary>
    /// Rig Animator v0.1 Beta — Created by FISHHWB
    ///
    /// Small, dependency-free JSON reader. Unity's built-in JsonUtility can't
    /// handle arbitrary/unknown shapes, and different AI providers (and even
    /// different models) format their JSON slightly differently. This parses
    /// into plain object graphs (Dictionary&lt;string,object&gt;, List&lt;object&gt;,
    /// double, string, bool, null) so the rest of the system can navigate any
    /// response defensively instead of requiring an exact schema match.
    /// </summary>
    public static class MiniJson
    {
        public static object Parse(string json)
        {
            int i = 0;
            var result = ParseValue(json, ref i);
            return result;
        }

        private static object ParseValue(string s, ref int i)
        {
            SkipWhitespace(s, ref i);
            if (i >= s.Length) return null;

            switch (s[i])
            {
                case '{': return ParseObject(s, ref i);
                case '[': return ParseArray(s, ref i);
                case '"': return ParseString(s, ref i);
                case 't':
                    i += 4; return true;
                case 'f':
                    i += 5; return false;
                case 'n':
                    i += 4; return null;
                default:
                    return ParseNumber(s, ref i);
            }
        }

        private static Dictionary<string, object> ParseObject(string s, ref int i)
        {
            var dict = new Dictionary<string, object>();
            i++; // {
            SkipWhitespace(s, ref i);
            if (i < s.Length && s[i] == '}') { i++; return dict; }

            while (i < s.Length)
            {
                SkipWhitespace(s, ref i);
                string key = ParseString(s, ref i);
                SkipWhitespace(s, ref i);
                i++; // :
                object value = ParseValue(s, ref i);
                dict[key] = value;
                SkipWhitespace(s, ref i);
                if (i < s.Length && s[i] == ',') { i++; continue; }
                if (i < s.Length && s[i] == '}') { i++; break; }
                break;
            }
            return dict;
        }

        private static List<object> ParseArray(string s, ref int i)
        {
            var list = new List<object>();
            i++; // [
            SkipWhitespace(s, ref i);
            if (i < s.Length && s[i] == ']') { i++; return list; }

            while (i < s.Length)
            {
                object value = ParseValue(s, ref i);
                list.Add(value);
                SkipWhitespace(s, ref i);
                if (i < s.Length && s[i] == ',') { i++; continue; }
                if (i < s.Length && s[i] == ']') { i++; break; }
                break;
            }
            return list;
        }

        private static string ParseString(string s, ref int i)
        {
            var sb = new StringBuilder();
            i++; // opening quote
            while (i < s.Length && s[i] != '"')
            {
                char c = s[i];
                if (c == '\\' && i + 1 < s.Length)
                {
                    i++;
                    char next = s[i];
                    switch (next)
                    {
                        case 'n': sb.Append('\n'); break;
                        case 't': sb.Append('\t'); break;
                        case 'r': sb.Append('\r'); break;
                        case 'b': sb.Append('\b'); break;
                        case 'f': sb.Append('\f'); break;
                        case '"': sb.Append('"'); break;
                        case '\\': sb.Append('\\'); break;
                        case '/': sb.Append('/'); break;
                        case 'u':
                            if (i + 4 < s.Length)
                            {
                                string hex = s.Substring(i + 1, 4);
                                sb.Append((char)int.Parse(hex, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                                i += 4;
                            }
                            break;
                        default: sb.Append(next); break;
                    }
                }
                else
                {
                    sb.Append(c);
                }
                i++;
            }
            i++; // closing quote
            return sb.ToString();
        }

        private static double ParseNumber(string s, ref int i)
        {
            int start = i;
            while (i < s.Length && (char.IsDigit(s[i]) || s[i] == '-' || s[i] == '+' || s[i] == '.' || s[i] == 'e' || s[i] == 'E'))
                i++;
            string numStr = s.Substring(start, i - start);
            double.TryParse(numStr, NumberStyles.Float, CultureInfo.InvariantCulture, out double result);
            return result;
        }

        private static void SkipWhitespace(string s, ref int i)
        {
            while (i < s.Length && char.IsWhiteSpace(s[i])) i++;
        }

        /// <summary>
        /// Navigates a parsed object graph using a dot path, e.g. "content.0.text"
        /// or "choices.0.message.content" or "candidates.0.content.parts.0.text".
        /// Numeric segments index into arrays. Returns null if any segment is missing.
        /// </summary>
        public static object GetPath(object root, string dotPath)
        {
            if (string.IsNullOrEmpty(dotPath)) return root;
            object current = root;
            foreach (var segment in dotPath.Split('.'))
            {
                if (current == null) return null;

                if (int.TryParse(segment, out int index))
                {
                    if (current is List<object> list && index >= 0 && index < list.Count)
                        current = list[index];
                    else
                        return null;
                }
                else
                {
                    if (current is Dictionary<string, object> dict && dict.TryGetValue(segment, out var value))
                        current = value;
                    else
                        return null;
                }
            }
            return current;
        }

        /// <summary>JSON-escapes a raw string for safe embedding into a hand-built JSON template.</summary>
        public static string Escape(string raw)
        {
            if (raw == null) return "";
            var sb = new StringBuilder();
            foreach (char c in raw)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            return sb.ToString();
        }
    }
}
