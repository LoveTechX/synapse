"""Single entry point for the Synapse AI MVP."""

import argparse
import json

from synapse.core.pipeline import SynapsePipeline


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for processing one file."""
    parser = argparse.ArgumentParser(description="Synapse AI file processing pipeline")
    parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to the file that should be processed",
    )
    return parser.parse_args()


def main() -> int:
    """Collect input, run the pipeline, and print the final result."""
    args = parse_args()
    file_path = args.file_path or input("Enter file path: ").strip()

    if not file_path:
        raise ValueError("A file path is required.")

    pipeline = SynapsePipeline()
    result = pipeline.process_file(file_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
