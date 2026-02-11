import json
import os
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = Path(__file__).resolve().parent


def load_model_name() -> str:
    env_model = os.getenv("FINE_TUNED_MODEL")
    if env_model:
        return env_model

    config_path = ROOT / "config.json"
    if config_path.exists():
        with config_path.open() as config_file:
            config = json.load(config_file)
            model = config.get("model")
            if model:
                return model

    return "gpt-4o-mini"


def api_key_from_request(handler: BaseHTTPRequestHandler) -> str:
    key = handler.headers.get("X-OpenAI-API-Key", "").strip()
    return key or os.getenv("OPENAI_API_KEY", "")


def run_cli(command: str, payload: dict, api_key: str) -> tuple[int, str, str]:
    scripts = {
        "upload": ["scripts/upload.py"],
        "train": ["scripts/train.py", payload.get("file_id", "")],
        "status": ["scripts/check_status.py", payload.get("job_id", "")],
        "infer": ["scripts/infer.py"],
    }

    if command not in scripts:
        return 400, "", f"Unknown command: {command}"

    cmd = [sys.executable, *scripts[command]]
    if command in {"train", "status"} and not cmd[-1]:
        return 400, "", f"Missing required value for {command}"

    if command == "train" and payload.get("model"):
        cmd.extend(["--model", payload["model"]])

    env = os.environ.copy()
    if api_key:
        env["OPENAI_API_KEY"] = api_key

    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return completed.returncode, completed.stdout, completed.stderr


def run_prompt_comparison(payload: dict, api_key: str) -> dict:
    if not api_key:
        raise ValueError("OpenAI API key is not set. Provide X-OpenAI-API-Key or OPENAI_API_KEY.")

    model = payload.get("model") or load_model_name()
    task_input = payload.get("task_input", "")
    strategy_a_prompt = payload.get("strategy_a_prompt", "")
    strategy_b_prompt = payload.get("strategy_b_prompt", "")
    evaluator_prompt = payload.get("evaluator_prompt", "")

    if not task_input.strip():
        raise ValueError("Task input is required")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    strategy_a = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": strategy_a_prompt or "You are an expert assistant. Solve the task directly and clearly."},
            {"role": "user", "content": f"Task input:\n{task_input}\n\nProvide your best answer."},
        ],
    )
    strategy_b = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": strategy_b_prompt or "You are an expert assistant. Be thorough and include caveats and edge cases."},
            {"role": "user", "content": f"Task input:\n{task_input}\n\nProvide your best answer."},
        ],
    )

    output_a = strategy_a.choices[0].message.content or ""
    output_b = strategy_b.choices[0].message.content or ""

    evaluator = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": evaluator_prompt or "You are an evaluator. Compare outputs for correctness, usefulness, and clarity."},
            {
                "role": "user",
                "content": (
                    "Compare both outputs and choose the better one for this task.\n\n"
                    f"Task input:\n{task_input}\n\n"
                    f"Output A:\n{output_a}\n\n"
                    f"Output B:\n{output_b}\n\n"
                    "Return JSON with keys winner (A or B), confidence_0_to_100, strengths, weaknesses, rationale."
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    evaluator_text = evaluator.choices[0].message.content or "{}"
    evaluation = json.loads(evaluator_text)

    return {
        "model": model,
        "output_a": output_a,
        "output_b": output_b,
        "evaluation": evaluation,
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-OpenAI-API-Key")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        mime = "text/plain"
        if file_path.suffix == ".html":
            mime = "text/html"
        elif file_path.suffix == ".css":
            mime = "text/css"
        elif file_path.suffix == ".js":
            mime = "application/javascript"

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self) -> None:
        self._send_json({}, 200)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        requested = self.path.split("?", 1)[0]
        if requested == "/":
            requested = "/index.html"

        file_path = (WEB_ROOT / requested.lstrip("/")).resolve()
        if WEB_ROOT not in file_path.parents and file_path != WEB_ROOT:
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return

        self._serve_file(file_path)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON payload"}, 400)
            return

        api_key = api_key_from_request(self)

        if self.path == "/api/cli":
            rc, out, err = run_cli(payload.get("command", ""), payload, api_key)
            status = 200 if rc == 0 else 400
            self._send_json({"return_code": rc, "stdout": out, "stderr": err}, status)
            return

        if self.path in {"/api/compare", "/api/courtroom"}:
            try:
                result = run_prompt_comparison(payload, api_key)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
                return
            except Exception as exc:
                self._send_json({"error": f"Comparison request failed: {exc}"}, 500)
                return

            self._send_json(result)
            return

        self._send_json({"error": "Unknown endpoint"}, 404)


def main() -> None:
    port = int(os.getenv("TRIALFORGE_PORT", os.getenv("PROMPT_COURT_PORT", "8080")))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"TrialForge running at http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
