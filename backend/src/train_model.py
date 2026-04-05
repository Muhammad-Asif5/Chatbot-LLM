"""
Fine-tune a HuggingFace model on your FAQ dataset.
Base model: google/flan-t5-base (small, fast, multilingual-friendly)
Strategy: LoRA / PEFT for efficient fine-tuning on limited hardware
"""

import os
import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
from peft import get_peft_model, LoraConfig, TaskType
from src.data_loader import load_faqs
from config import GOOGLE_BASE_MODEL, MODEL_OUTPUT_PATH

# ── CONFIG ───────────────────────────────────────────────
BASE_MODEL = GOOGLE_BASE_MODEL       # ~250MB, fast training
MODEL_OUTPUT = MODEL_OUTPUT_PATH
MAX_INPUT_LEN = 256
MAX_TARGET_LEN = 128
BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 5e-4

def prepare_dataset(df: pd.DataFrame, tokenizer) -> Dataset:
    """Convert FAQ DataFrame to HuggingFace Dataset with tokenization."""
    
    def preprocess(examples):
        # Prefix prompting improves T5 fine-tuning
        inputs = ["answer question: " + q for q in examples["question"]]
        targets = examples["answer"]

        model_inputs = tokenizer(
            inputs,
            max_length=MAX_INPUT_LEN,
            truncation=True,
            padding="max_length"
        )
        labels = tokenizer(
            targets,
            max_length=MAX_TARGET_LEN,
            truncation=True,
            padding="max_length"
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    dataset = Dataset.from_pandas(df[["question", "answer"]])
    dataset = dataset.map(preprocess, batched=True, remove_columns=["question", "answer"])
    return dataset

def train():
    """Full fine-tuning pipeline."""
    print("[Train] Loading FAQ data...")
    df = load_faqs()

    print(f"[Train] Loading base model: {BASE_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)

    # ── Apply LoRA for efficient fine-tuning ─────────────
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=16,                    # LoRA rank
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q", "v"]  # T5 attention layers
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ── Prepare Data ─────────────────────────────────────
    dataset = prepare_dataset(df, tokenizer)
    split = dataset.train_test_split(test_size=0.1)
    train_ds, eval_ds = split["train"], split["test"]

    # ── Training Arguments ───────────────────────────────
    args = Seq2SeqTrainingArguments(
        output_dir=MODEL_OUTPUT,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        warmup_steps=50,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        predict_with_generate=True,
        logging_dir="./logs",
        logging_steps=10,
        fp16=torch.cuda.is_available(),  # Use FP16 if GPU available
        report_to="none"
    )

    # ── Trainer ──────────────────────────────────────────
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    )

    print("[Train] Starting fine-tuning...")
    trainer.train()

    # ── Save Final Model ─────────────────────────────────
    os.makedirs(MODEL_OUTPUT, exist_ok=True)
    model.save_pretrained(MODEL_OUTPUT)
    tokenizer.save_pretrained(MODEL_OUTPUT)
    print(f"[Train] Model saved to {MODEL_OUTPUT}")

if __name__ == "__main__":
    train()