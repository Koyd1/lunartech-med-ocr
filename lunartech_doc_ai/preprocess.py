from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


def prepare_ocr_image(
    input_path: Path | str,
    output_path: Path | str,
    *,
    min_width: int = 1400,
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as image:
        prepared = image.convert("L")
        prepared = ImageOps.autocontrast(prepared, cutoff=1)
        prepared = prepared.filter(ImageFilter.SHARPEN)

        if prepared.width < min_width:
            scale = min_width / prepared.width
            new_size = (int(prepared.width * scale), int(prepared.height * scale))
            prepared = prepared.resize(new_size, Image.Resampling.LANCZOS)

        prepared.convert("RGB").save(output_path)

    return output_path


def prepare_degraded_ocr_image(
    input_path: Path | str,
    output_path: Path | str,
    *,
    min_width: int = 1400,
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as image:
        prepared = image.convert("L")

        if prepared.width < min_width:
            scale = min_width / prepared.width
            new_size = (int(prepared.width * scale), int(prepared.height * scale))
            prepared = prepared.resize(new_size, Image.Resampling.LANCZOS)

        prepared = ImageOps.autocontrast(prepared, cutoff=0)
        prepared = prepared.filter(ImageFilter.SHARPEN)
        prepared.convert("RGB").save(output_path)

    return output_path
