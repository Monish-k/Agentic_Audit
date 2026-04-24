from __future__ import annotations

from typing import TypedDict, List


class LineItem(TypedDict, total=False):
    name: str
    amount: str


class ReceiptSchema(TypedDict, total=False):
    document_type: str
    line_items: List[LineItem]
    subtotal: str
    tax: str
    total: str
