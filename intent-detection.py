
import json
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, TaskType
from trl.trainer.sft_trainer import SFTTrainer


with open("insurance_dataset_500.json", "r", encoding="utf-8") as f:
    data = json.load(f)

dataset = Dataset.from_list(data)

def format_example(example):
    return {
        "text": (
            "<s>[INST] "
            f"{example['instruction']} "
            "[/INST]\n"
            f"{example['output']}"
            "</s>"
        )
    }

dataset = dataset.map(format_example)

# Keep only text column
dataset = dataset.remove_columns(
    [c for c in dataset.column_names if c != "text"]
)


MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.model_max_length = 1024

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    torch_dtype=torch.float16,
    load_in_4bit=True   
)

model.config.use_cache = False

# -----------------------------
# 3. LoRA Configuration
# -----------------------------
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj",
        "o_proj", "gate_proj",
        "up_proj", "down_proj"
    ],
    bias="none"
)

# -----------------------------
# 4. Training Arguments
# -----------------------------
training_args = TrainingArguments(
    output_dir="./zarnex_mistral_intent",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=2,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    optim="paged_adamw_8bit",
    report_to="none"
)

# -----------------------------
# 5. Trainer
# -----------------------------
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    args=training_args
)

# -----------------------------
# 6. Train & Save
# -----------------------------
trainer.train()
trainer.save_model("./zarnex_mistral_intent")
tokenizer.save_pretrained("./zarnex_mistral_intent")

print("✅ Mistral LoRA training completed")
