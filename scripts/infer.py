import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def load_model_name() -> str:
    env_model = os.getenv("FINE_TUNED_MODEL")
    if env_model:
        return env_model

    config_path = Path(__file__).resolve().parents[1] / "config.json"
    if config_path.exists():
        with config_path.open() as config_file:
            config = json.load(config_file)
            model = config.get("model")
            if model:
                return model

    raise SystemExit("Fine-tuned model name not found. Set FINE_TUNED_MODEL or create config.json with a 'model' field.")


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    model = load_model_name()
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one short sentence."},
        ],
    )

    message = response.choices[0].message.content
    print(message)


if __name__ == "__main__":
    main()
