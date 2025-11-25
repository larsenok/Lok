import argparse
import os
import time

from dotenv import load_dotenv
from openai import OpenAI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check fine-tuning job status")
    parser.add_argument("job_id", help="ID of the fine-tuning job")
    parser.add_argument(
        "--watch",
        type=float,
        metavar="SECONDS",
        help="Poll the job until it finishes, sleeping this many seconds between checks",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    args = parse_args()
    client = OpenAI(api_key=api_key)

    while True:
        job = client.fine_tuning.jobs.retrieve(args.job_id)
        print(f"Status: {job.status}")
        if job.fine_tuned_model:
            print(f"Fine-tuned model: {job.fine_tuned_model}")

        if args.watch is None:
            break

        if job.status in {"succeeded", "failed", "cancelled"}:
            break

        time.sleep(args.watch)


if __name__ == "__main__":
    main()
