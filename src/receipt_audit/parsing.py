from __future__ import annotations

import json
import re
from typing import Any, Optional


def clean_model_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_first_json_object(text: str) -> Optional[str]:
    text = clean_model_text(text)
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None


def parse_model_json(text: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    candidate = extract_first_json_object(text)
    if candidate is None:
        return None, "No JSON object found in model output."
    try:
        return json.loads(candidate), None
    except Exception as exc:  # pragma: no cover
        return None, str(exc)
