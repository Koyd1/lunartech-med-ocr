from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


Box = tuple[int, int, int, int]


DEFAULT_REDACTION_BOXES: dict[str, list[Box]] = {
    "Adeverinta Medicala AUTO.png": [
        (385, 350, 960, 455),   # name
        (380, 430, 960, 535),   # personal identifier
        (290, 500, 720, 620),   # birth date
        (650, 590, 960, 700),   # medical exam date
        (900, 340, 1125, 545),  # QR
        (90, 985, 425, 1405),   # photo
        (485, 1150, 1170, 1510),# signature/stamp area
    ],
    "Adeverinta medicala Militara.png": [
        (330, 360, 1260, 470),  # name line
        (290, 455, 780, 560),   # birth date
        (290, 540, 1320, 650),  # organization/name line
        (285, 780, 1525, 955),  # diagnosis
        (1020, 1480, 1545, 1690),# signature
        (270, 1460, 675, 1785), # stamp
    ],
}


def redact_image(
    input_path: Path | str,
    output_path: Path | str,
    *,
    boxes: list[Box],
    fill: tuple[int, int, int] = (245, 245, 245),
) -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        for box in boxes:
            draw.rectangle(box, fill=fill)
        image.save(output_path)


def redact_known_test_images(input_dir: Path | str, output_dir: Path | str) -> list[Path]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    written: list[Path] = []
    for filename, boxes in DEFAULT_REDACTION_BOXES.items():
        source = input_dir / filename
        if not source.exists():
            continue
        target = output_dir / f"{source.stem}_redacted{source.suffix}"
        redact_image(source, target, boxes=boxes)
        written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Create redacted copies of known test images.")
    parser.add_argument("--input-dir", default="test-img")
    parser.add_argument("--output-dir", default="data/redacted")
    args = parser.parse_args()

    written = redact_known_test_images(args.input_dir, args.output_dir)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
