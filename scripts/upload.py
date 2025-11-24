from pathlib import Path
import os

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    dataset_path = Path(__file__).resolve().parents[1] / "dataset" / "dataset.jsonl"
    if not dataset_path.exists():
        raise SystemExit(f"Dataset file not found at {dataset_path}")

    with dataset_path.open("rb") as dataset_file:
        uploaded_file = client.files.create(file=dataset_file, purpose="fine-tune")

    print(f"Uploaded file ID: {uploaded_file.id}")


if __name__ == "__main__":
    main()
