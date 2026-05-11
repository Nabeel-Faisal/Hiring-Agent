"""Robust JSON extraction from LLM responses that may contain extra text."""
import json
import re


def _collapse_newlines_in_strings(text: str) -> str:
    """Replace literal newlines/tabs inside JSON string values with escaped versions."""
    out = []
    in_str = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '\\' and in_str:
            # escaped char — copy both bytes verbatim
            out.append(ch)
            i += 1
            if i < len(text):
                out.append(text[i])
            i += 1
            continue
        if ch == '"':
            in_str = not in_str
            out.append(ch)
            i += 1
            continue
        if in_str and ch == '\n':
            out.append('\\n')
            i += 1
            continue
        if in_str and ch == '\r':
            out.append('\\r')
            i += 1
            continue
        if in_str and ch == '\t':
            out.append('\\t')
            i += 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def extract_json(text: str):
    """Extract the first valid JSON object or array from LLM output."""
    text = text.strip()

    candidates = [text]

    # Strip markdown code fences
    if '```' in text:
        for part in text.split('```'):
            part = part.strip()
            if part.startswith('json'):
                part = part[4:].strip()
            if part.startswith('{') or part.startswith('['):
                candidates.append(part)

    # Also add newline-collapsed version of original text
    candidates.append(_collapse_newlines_in_strings(text))

    for t in candidates:
        # Direct parse
        try:
            return json.loads(t)
        except Exception:
            pass

        # Collapse newlines in this candidate too
        t_clean = _collapse_newlines_in_strings(t)
        try:
            return json.loads(t_clean)
        except Exception:
            pass

        # Find first JSON object/array using JSONDecoder
        for start_char in ('{', '['):
            start = t_clean.find(start_char)
            if start == -1:
                continue
            for strict in (True, False):
                try:
                    obj, _ = json.JSONDecoder(strict=strict).raw_decode(t_clean, start)
                    return obj
                except Exception:
                    pass

        # Try without newline collapsing as well
        for start_char in ('{', '['):
            start = t.find(start_char)
            if start == -1:
                continue
            for strict in (True, False):
                try:
                    obj, _ = json.JSONDecoder(strict=strict).raw_decode(t, start)
                    return obj
                except Exception:
                    pass

    raise ValueError(f"No valid JSON found in LLM response: {text[:300]}")
