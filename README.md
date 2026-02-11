# Fine-tuning GPT-4o-mini

This repository provides a minimal workflow for fine-tuning an OpenAI GPT-4o-mini model with a JSONL chat dataset.

## Repository layout
- `dataset/dataset.jsonl` – your chat-format dataset (gitignored so you can supply your own examples).
- `scripts/upload.py` – uploads the dataset to OpenAI Files for fine-tuning.
- `scripts/train.py` – starts a fine-tuning job from an uploaded file.
- `scripts/check_status.py` – checks job status and prints the fine-tuned model name when ready.
- `scripts/infer.py` – runs a quick chat completion against the fine-tuned model.
- `trialforge/` – optional browser UI for prompt strategy comparisons, dataset authoring, and one-click CLI actions.

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
Create `dataset/dataset.jsonl` with one JSON object per line. Each line should represent a single chat example that includes a system prompt, a user message, and the assistant reply:
```jsonl
{"messages": [
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "How can I break down a big weekend chore list so it feels manageable?"},
  {"role": "assistant", "content": "Here is a clear, prioritized plan you can follow."}
]}
```
Guidance on dataset size for GPT-4o-mini experiments:
- **Minimum to run**: ~10 high-quality Q&A pairs.
- **Recommended starting point**: 50–100 varied examples.
- **Plenty for a small experiment**: 200+ well-edited examples.
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

## Optional frontend (TrialForge)
Run a polished web UI for prompt strategy comparisons and existing CLI scripts:
```bash
python trialforge/server.py
```
Then open `http://localhost:8080`. See `trialforge/README.md` for details.
