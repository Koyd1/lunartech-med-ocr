from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def convert_pdf_first_page_to_png(pdf_path: Path | str, output_path: Path | str) -> Path:
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not shutil.which("sips"):
        raise RuntimeError("PDF input requires macOS sips or another PDF renderer.")

    subprocess.run(
        ["sips", "-s", "format", "png", str(pdf_path), "--out", str(output_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return output_path
