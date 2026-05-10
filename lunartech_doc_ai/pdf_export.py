from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def find_chrome_executable() -> Path | None:
    env_path = os.environ.get("CHROME_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    candidates = [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
        Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    for name in ["google-chrome", "chromium", "chromium-browser"]:
        resolved = shutil.which(name)
        if resolved:
            return Path(resolved)
    return None


def render_pdf_from_html(html_path: Path | str, pdf_path: Path | str) -> bool:
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    chrome = find_chrome_executable()
    if not chrome:
        return False

    command = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--allow-file-access-from-files",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    return pdf_path.exists()
