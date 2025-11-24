import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a fine-tuning job")
    parser.add_argument("file_id", help="ID of the uploaded training file")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Base model to fine-tune (default: gpt-4o-mini)",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    args = parse_args()
    client = OpenAI(api_key=api_key)

    job = client.fine_tuning.jobs.create(training_file=args.file_id, model=args.model)
    print(f"Started fine-tuning job: {job.id}")


if __name__ == "__main__":
    main()
