from __future__ import annotations

import re
from typing import Any, Optional


def money_to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        return None
    try:
        return float(text)
    except Exception:
        return None


def line_item_sum_amounts(obj: dict[str, Any]) -> Optional[float]:
    values: list[float] = []
    for item in obj.get("line_items", []):
        amount = money_to_float(item.get("amount", ""))
        if amount is not None:
            values.append(amount)
    if not values:
        return None
    return round(sum(values), 2)


def arithmetic_audit(obj: Optional[dict[str, Any]]) -> dict[str, Any]:
    if obj is None:
        return {"is_valid": False, "issues": ["No parsed JSON available."], "details": {}}

    issues: list[str] = []
    subtotal = money_to_float(obj.get("subtotal", ""))
    tax = money_to_float(obj.get("tax", ""))
    total = money_to_float(obj.get("total", ""))

    line_sum = line_item_sum_amounts(obj)
    details: dict[str, Any] = {"line_item_sum": line_sum}

    if subtotal is not None and line_sum is not None and round(subtotal, 2) != round(line_sum, 2):
        issues.append(f"Subtotal mismatch: subtotal={subtotal} vs line_item_sum={line_sum}")

    if subtotal is not None and tax is not None and total is not None:
        expected_total = round(subtotal + tax, 2)
        details["expected_total"] = expected_total
        if round(expected_total, 2) != round(total, 2):
            issues.append(f"Total mismatch: expected={expected_total} vs total={total}")

    return {"is_valid": len(issues) == 0, "issues": issues, "details": details}


def schema_check(obj: Optional[dict[str, Any]]) -> dict[str, Any]:
    required = ["document_type", "line_items", "subtotal", "tax", "total"]
    if obj is None:
        return {"ok": False, "missing": required, "issues": ["No parsed JSON available."]}
    missing = [key for key in required if key not in obj]
    issues: list[str] = []
    if not isinstance(obj.get("line_items", []), list):
        issues.append("line_items is not a list")
    return {"ok": len(missing) == 0 and len(issues) == 0, "missing": missing, "issues": issues}


def final_decision(parsed: Optional[dict[str, Any]]) -> dict[str, Any]:
    schema = schema_check(parsed)
    arithmetic = arithmetic_audit(parsed)

    issues: list[str] = []
    if not schema["ok"]:
        issues.extend(schema["missing"])
        issues.extend(schema["issues"])
    if not arithmetic["is_valid"]:
        issues.extend(arithmetic["issues"])

    if parsed is None:
        decision = "needs_review"
        rationale = "The model output could not be parsed into JSON."
    elif issues:
        decision = "needs_review"
        rationale = "The extraction completed, but audit checks found issues."
    else:
        decision = "approved"
        rationale = "The extraction passed schema and arithmetic checks."

    return {
        "decision": decision,
        "rationale": rationale,
        "issues": issues,
        "schema": schema,
        "arithmetic": arithmetic,
    }
