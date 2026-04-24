from __future__ import annotations

MINIMAL_SCHEMA_JSON = (
    '{"document_type":"receipt","line_items":[{"name":"","amount":""}],'
    '"subtotal":"","tax":"","total":""}'
)

SYSTEM_PROMPT = (
    "You extract receipt fields. "
    "Return exactly one JSON object. "
    "Do not use markdown. "
    "Do not wrap the JSON in triple backticks. "
    "Do not add any explanation before or after the JSON. "
    "If a field is missing, use an empty string. "
    f"Schema: {MINIMAL_SCHEMA_JSON}"
)

USER_PROMPT = "Extract this receipt into the JSON schema."
