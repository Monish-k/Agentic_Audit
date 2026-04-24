from __future__ import annotations

import gradio as gr

from .config import AppConfig
from .modeling import ReceiptAuditModel


_demo_model: ReceiptAuditModel | None = None


def get_demo_model(config: AppConfig) -> ReceiptAuditModel:
    global _demo_model
    if _demo_model is None:
        _demo_model = ReceiptAuditModel(
            model_id=config.base_model_id,
            adapter_source=config.adapter_source,
            max_new_tokens=config.max_new_tokens,
        )
    return _demo_model


def build_demo(config: AppConfig) -> gr.Blocks:
    demo_model = get_demo_model(config)

    with gr.Blocks(title="Agentic Receipt Audit") as demo:
        gr.Markdown("# Agentic Receipt Audit")
        gr.Markdown("Upload a receipt image to extract compact JSON and run audit checks.")
        gr.Markdown(
            "**Note:** This demo may feel slow because it is running on CPU-only free cloud hardware in some environments."
        )

        with gr.Row():
            image_input = gr.Image(type="pil", label="Receipt image")
            with gr.Column():
                decision_text = gr.Textbox(label="Final decision")
                parsed_output = gr.Code(label="Parsed JSON", language="json")
                decision_output = gr.Code(label="Audit report", language="json")

        raw_output = gr.Textbox(label="Raw model output", lines=10)
        run_btn = gr.Button("Run audit")
        run_btn.click(
            fn=demo_model.predict,
            inputs=[image_input],
            outputs=[raw_output, parsed_output, decision_output, decision_text],
        )

    return demo
