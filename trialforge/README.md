# TrialForge (Frontend + CLI Bridge)

`trialforge/` is a top-level frontend for running the repository workflow from a browser.

It includes four workflows:

1. **Prompt Lab**: compare two prompt strategies for the same task with an evaluator verdict and vote tracking.
2. **Prompt Library**: save and reuse prompt templates locally.
3. **CLI Runner**: run `upload.py`, `train.py`, `check_status.py`, and `infer.py` from the UI.
4. **Dataset Builder**: create training examples visually and export JSONL text.

## Run locally

From repository root:

```bash
python trialforge/server.py
```

Open:

- `http://localhost:8080`

Optional port override:

```bash
TRIALFORGE_PORT=9000 python trialforge/server.py
```

## API endpoints

- `GET /api/health` – health check.
- `POST /api/cli` – run repository scripts.
  - Body:
    ```json
    {
      "command": "upload|train|status|infer",
      "file_id": "file-...",
      "job_id": "ftjob-...",
      "model": "gpt-4o-mini"
    }
    ```
- `POST /api/compare` – run strategy A vs strategy B comparison flow.
  - Body:
    ```json
    {
      "model": "ft:gpt-4o-mini-...",
      "task_input": "...",
      "strategy_a_prompt": "...",
      "strategy_b_prompt": "...",
      "evaluator_prompt": "..."
    }
    ```
- `POST /api/courtroom` – legacy alias to `/api/compare`.


## Local storage model

TrialForge currently stores state in browser localStorage:

- Prompt library templates (`trialforgePromptLibrary`)
- API key (`trialforgeOpenAIKey`)
- Comparison vote ledger with prompt snapshots (`trialforgeVoteLedger`)

This means prompts and votes persist per browser profile.

## OpenAI API key options

You can provide API keys in either way:

1. In the UI key field (stored in browser localStorage and sent as `X-OpenAI-API-Key`).
2. As server env var:

```bash
export OPENAI_API_KEY="sk-..."
```

Model selection order for comparison requests:

1. `model` in request body
2. `FINE_TUNED_MODEL`
3. `config.json` (`{"model": "..."}`)
4. fallback: `gpt-4o-mini`

## Access for others

The server binds to `0.0.0.0`, so teammates on your network can access it via host IP + port.

If internet-exposed, place behind auth/proxy since `/api/cli` executes local scripts.
