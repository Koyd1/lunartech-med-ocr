from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


def detect_form_lines(
    image_path: Path | str,
    *,
    min_length: int = 120,
    dark_threshold: int = 120,
) -> list[dict]:
    image_path = Path(image_path)
    with Image.open(image_path) as image:
        gray = ImageOps.grayscale(image)
        width, height = gray.size
        pixels = gray.load()

        lines: list[dict] = []
        lines.extend(_scan_horizontal(pixels, width, height, min_length, dark_threshold))
        lines.extend(_scan_vertical(pixels, width, height, min_length, dark_threshold))
        lines = _filter_page_edge_artifacts(lines, width, height)
        return _dedupe_lines(lines)


def _scan_horizontal(pixels, width: int, height: int, min_length: int, threshold: int) -> list[dict]:
    lines: list[dict] = []
    for y in range(height):
        start: int | None = None
        for x in range(width):
            is_dark = pixels[x, y] <= threshold
            if is_dark and start is None:
                start = x
            if (not is_dark or x == width - 1) and start is not None:
                end = x if is_dark and x == width - 1 else x - 1
                if end - start + 1 >= min_length:
                    lines.append(
                        {
                            "orientation": "horizontal",
                            "bbox": [start, y, end, y + 1],
                            "length": end - start + 1,
                        }
                    )
                start = None
    return lines


def _scan_vertical(pixels, width: int, height: int, min_length: int, threshold: int) -> list[dict]:
    lines: list[dict] = []
    for x in range(width):
        start: int | None = None
        for y in range(height):
            is_dark = pixels[x, y] <= threshold
            if is_dark and start is None:
                start = y
            if (not is_dark or y == height - 1) and start is not None:
                end = y if is_dark and y == height - 1 else y - 1
                if end - start + 1 >= min_length:
                    lines.append(
                        {
                            "orientation": "vertical",
                            "bbox": [x, start, x + 1, end],
                            "length": end - start + 1,
                        }
                    )
                start = None
    return lines


def _dedupe_lines(lines: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    for line in lines:
        if not any(_overlaps_same_line(line, existing) for existing in deduped):
            deduped.append(line)
    return deduped


def _overlaps_same_line(left: dict, right: dict) -> bool:
    if left["orientation"] != right["orientation"]:
        return False
    lx1, ly1, lx2, ly2 = left["bbox"]
    rx1, ry1, rx2, ry2 = right["bbox"]
    if left["orientation"] == "horizontal":
        return abs(ly1 - ry1) <= 8 and max(lx1, rx1) <= min(lx2, rx2)
    return abs(lx1 - rx1) <= 8 and max(ly1, ry1) <= min(ly2, ry2)


def _filter_page_edge_artifacts(lines: list[dict], width: int, height: int) -> list[dict]:
    filtered = []
    for line in lines:
        x1, y1, x2, y2 = line["bbox"]
        if line["orientation"] == "horizontal":
            full_width = line["length"] >= width * 0.95
            near_edge = y1 < 60 or y1 > height - 60
            if full_width and near_edge:
                continue
        else:
            full_height = line["length"] >= height * 0.95
            near_edge = x1 <= 80 or x1 >= width - 80
            if full_height and near_edge:
                continue
        filtered.append(line)
    return filtered
