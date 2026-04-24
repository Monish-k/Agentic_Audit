from __future__ import annotations

import json
from typing import Any

import torch
from PIL import Image
from peft import PeftModel
from transformers import AutoProcessor, BitsAndBytesConfig, Qwen3VLForConditionalGeneration

from .audit import final_decision
from .parsing import parse_model_json
from .prompts import SYSTEM_PROMPT, USER_PROMPT


class ReceiptAuditModel:
    def __init__(self, model_id: str, adapter_source: str, max_new_tokens: int = 256) -> None:
        self.model_id = model_id
        self.adapter_source = adapter_source
        self.max_new_tokens = max_new_tokens

        use_cuda = torch.cuda.is_available()
        bnb_config = None
        if use_cuda:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

        self.processor = AutoProcessor.from_pretrained(model_id)
        if self.processor.tokenizer.pad_token is None:
            self.processor.tokenizer.pad_token = self.processor.tokenizer.eos_token
        self.processor.tokenizer.padding_side = "right"
        self.processor.image_processor.size = {
            "longest_edge": 192 * 32 * 32,
            "shortest_edge": 96 * 32 * 32,
        }

        base_model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            torch_dtype=torch.float16 if use_cuda else torch.float32,
            device_map="auto" if use_cuda else None,
            attn_implementation="sdpa",
        )
        self.model = PeftModel.from_pretrained(base_model, adapter_source)
        self.model.eval()

    def generate_raw_text(self, image: Image.Image) -> str:
        image = image.convert("RGB")
        messages = [
            {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": USER_PROMPT},
                ],
            },
        ]
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        if torch.cuda.is_available():
            inputs = inputs.to(self.model.device)

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )

        trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        return self.processor.batch_decode(
            trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

    def predict(self, image: Image.Image) -> tuple[str, str, str, str]:
        raw = self.generate_raw_text(image)
        parsed, error = parse_model_json(raw)
        decision = final_decision(parsed)

        parsed_json = (
            json.dumps(parsed, indent=2, ensure_ascii=False)
            if parsed
            else json.dumps({"error": error}, indent=2, ensure_ascii=False)
        )
        decision_json = json.dumps(decision, indent=2, ensure_ascii=False)
        return raw, parsed_json, decision_json, decision["decision"]
