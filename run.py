from __future__ import annotations

import argparse
from pathlib import Path

from lunartech_doc_ai.pipeline import process_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstruct scanned medical documents.")
    parser.add_argument("--input", required=True, help="Input image file or directory.")
    parser.add_argument("--output", default="output", help="Output directory.")
    args = parser.parse_args()

    results = process_path(Path(args.input), output_dir=Path(args.output))
    for result in results:
        print(f"Processed {result['source']['filename']}")
        print(f"  JSON: {result['outputs']['json']}")
        print(f"  HTML: {result['outputs']['html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
