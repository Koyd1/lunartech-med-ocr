from __future__ import annotations

import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OCRWord:
    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int
    block_num: int
    par_num: int
    line_num: int
    word_num: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def run_tesseract_tsv(image_path: Path, *, lang: str | None = None, psm: int = 11) -> list[OCRWord]:
    lang = lang or choose_ocr_languages(get_available_tesseract_languages())
    command = [
        "tesseract",
        str(image_path),
        "stdout",
        "-l",
        lang,
        "--psm",
        str(psm),
        "tsv",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return parse_tesseract_tsv(completed.stdout)


def get_available_tesseract_languages() -> set[str]:
    completed = subprocess.run(
        ["tesseract", "--list-langs"],
        check=True,
        capture_output=True,
        text=True,
    )
    languages: set[str] = set()
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("List of available languages"):
            continue
        languages.add(stripped)
    return languages


def choose_ocr_languages(available_languages: set[str]) -> str:
    preferred = [language for language in ["eng", "ron", "rus"] if language in available_languages]
    if preferred:
        return "+".join(preferred)
    return "eng"


def parse_tesseract_tsv(tsv_text: str) -> list[OCRWord]:
    rows = csv.DictReader(tsv_text.splitlines(), delimiter="\t")
    words: list[OCRWord] = []
    for row in rows:
        if row.get(None):
            continue
        text = (row.get("text") or "").strip()
        if not text or _is_malformed_ocr_text(text):
            continue

        confidence = _safe_float(row.get("conf"), default=-1.0)
        if confidence < 0:
            continue

        words.append(
            OCRWord(
                text=text,
                confidence=confidence,
                left=_safe_int(row.get("left")),
                top=_safe_int(row.get("top")),
                width=_safe_int(row.get("width")),
                height=_safe_int(row.get("height")),
                block_num=_safe_int(row.get("block_num")),
                par_num=_safe_int(row.get("par_num")),
                line_num=_safe_int(row.get("line_num")),
                word_num=_safe_int(row.get("word_num")),
            )
        )
    return words


def _is_malformed_ocr_text(text: str) -> bool:
    if "\t" in text or len(text) > 200:
        return True
    return bool(repeated_tsv_like_text(text))


def repeated_tsv_like_text(text: str) -> bool:
    return text.startswith("5\t") or text.startswith("2\t") or "\t-1\t" in text


def _safe_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default


def _safe_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except ValueError:
        return default
