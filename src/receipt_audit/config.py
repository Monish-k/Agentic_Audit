from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class AppConfig:
    base_model_id: str = os.getenv("RECEIPT_AUDIT_BASE_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
    adapter_source: str = os.getenv("RECEIPT_AUDIT_ADAPTER", "")
    host: str = os.getenv("RECEIPT_AUDIT_HOST", "0.0.0.0")
    port: int = int(os.getenv("RECEIPT_AUDIT_PORT", "7860"))
    max_new_tokens: int = int(os.getenv("RECEIPT_AUDIT_MAX_NEW_TOKENS", "256"))

    def validate(self) -> None:
        if not self.adapter_source:
            raise ValueError(
                "RECEIPT_AUDIT_ADAPTER is not set. Point it to a local adapter path or a Hugging Face model repo."
            )
