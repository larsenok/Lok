# Fine-tuning GPT-4o-mini

This repository provides a minimal workflow for fine-tuning an OpenAI GPT-4o-mini model with a JSONL chat dataset.

## Repository layout
- `dataset/dataset.jsonl` – placeholder chat-format dataset. Replace with your own examples.
- `scripts/upload.py` – uploads the dataset to OpenAI Files for fine-tuning.
- `scripts/train.py` – starts a fine-tuning job from an uploaded file.
- `scripts/check_status.py` – checks job status and prints the fine-tuned model name when ready.
- `scripts/infer.py` – runs a quick chat completion against the fine-tuned model.

## Installation
1. (Optional) Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Environment variables
Set your API key (and optionally the fine-tuned model name for inference):
```bash
export OPENAI_API_KEY="sk-..."
export FINE_TUNED_MODEL="ft:gpt-4o-mini-..."  # set after the job finishes
```
You can also provide the model name via `config.json` at the repo root:
```json
{"model": "ft:gpt-4o-mini-..."}
```

## Prepare the dataset
Replace `dataset/dataset.jsonl` with your own JSONL file. Each line should be a chat example:
```jsonl
{"messages": [{"role": "system", "content": "You are a helpful bot."}, {"role": "user", "content": "Hi!"}, {"role": "assistant", "content": "Hello!"}]}
```
Ensure the dataset is tokenized efficiently—long prompts and responses count toward token usage.

## Upload the dataset
```bash
python scripts/upload.py
```
Note the printed file ID for the next step.

## Start the fine-tune
```bash
python scripts/train.py <FILE_ID>
```
This defaults to `gpt-4o-mini`. Specify `--model` to target another compatible base model.

## Monitor progress
```bash
python scripts/check_status.py <JOB_ID>
```
The script prints the status on each run and includes the fine-tuned model name once available.

## Run inference
Ensure `FINE_TUNED_MODEL` or `config.json` is set, then:
```bash
python scripts/infer.py
```
The script sends a short chat prompt to verify the model is responding.

## Notes on tokens, epochs, and dataset size
- **Tokens**: Pricing and limits depend on total tokens per example (prompt + completion). Shorter messages reduce cost and time.
- **Epochs**: OpenAI fine-tuning runs multiple epochs by default; more epochs can improve learning but risk overfitting on tiny datasets.
- **Dataset size**: Larger datasets generally yield more robust models. Aim for diverse, high-quality examples rather than quantity alone.
