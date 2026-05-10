from __future__ import annotations

from html import escape
from pathlib import Path
import shutil
from statistics import median


def render_html(document: dict, output_path: Path) -> None:
    page = document["layout"]["page"]
    scale = 0.45 if page["width"] > 1200 else 0.85
    underlay = _copy_underlay_asset(document, output_path)
    blocks = _render_blocks(document, scale)
    underlay_html = (
        f'    <img class="page-underlay" src="{escape(underlay)}" alt="">\n'
        if underlay
        else ""
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(document["document"]["title"])}</title>
  <style>
    @page {{ size: A4; margin: 12mm; }}
    body {{
      margin: 0;
      background: #f4f5f7;
      color: #111827;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .sheet {{
      position: relative;
      width: {page["width"] * scale:.1f}px;
      height: {page["height"] * scale:.1f}px;
      margin: 24px auto;
      background: #fff;
      box-shadow: 0 1px 8px rgba(15, 23, 42, 0.16);
      overflow: hidden;
    }}
    .page-underlay {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: fill;
      opacity: 0.95;
      filter: grayscale(1) contrast(1.05);
    }}
    .block {{
      position: absolute;
      white-space: nowrap;
      line-height: 1.15;
      color: rgba(17, 24, 39, 0.28);
    }}
    .heading {{ font-weight: 700; }}
    .field_line {{ font-weight: 600; }}
    .date_line {{ font-weight: 600; }}
    .low-confidence {{ color: #9f1239; }}
    .field-box {{
      position: absolute;
      border: 1px solid rgba(37, 99, 235, 0.28);
      background: rgba(219, 234, 254, 0.12);
      box-sizing: border-box;
      pointer-events: none;
    }}
    .detected-line {{
      position: absolute;
      background: rgba(15, 23, 42, 0.42);
      pointer-events: none;
    }}
    .meta {{
      max-width: {page["width"] * scale:.1f}px;
      margin: 18px auto 0;
      font-size: 12px;
      color: #475569;
    }}
  </style>
</head>
<body>
  <section class="meta">
    OCR: {escape(document["quality"]["ocr_engine"])} |
    Mean confidence: {document["quality"]["mean_confidence"]} |
    Source: {escape(document["source"]["filename"])}
  </section>
  <main class="sheet">
{underlay_html}{_render_fields(document, scale)}
{_render_lines(document, scale)}
{blocks}
  </main>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _render_blocks(document: dict, scale: float) -> str:
    if _should_hide_visible_ocr_text(document):
        return ""
    return "\n".join(
        rendered
        for block in document["content"]["text_blocks"]
        if (rendered := _render_block(block, scale))
    )


def _render_block(block: dict, scale: float) -> str:
    if not _should_render_block(block):
        return ""
    x1, y1, x2, y2 = block["bbox"]
    font_size = _block_font_size(block, scale)
    classes = ["block", block["type"]]
    if block["confidence"] < 55:
        classes.append("low-confidence")
    return (
        f'    <div class="{" ".join(classes)}" '
        f'style="left:{x1 * scale:.1f}px; top:{y1 * scale:.1f}px; '
        f'font-size:{font_size:.1f}px;">{escape(block["text"])}</div>'
    )


def _should_hide_visible_ocr_text(document: dict) -> bool:
    quality = document.get("quality", {})
    return quality.get("ocr_candidate") == "degraded" or quality.get("mean_confidence", 100) < 70


def _copy_underlay_asset(document: dict, output_path: Path) -> str | None:
    source_data = document.get("source", {})
    source = Path(source_data.get("original_image") or source_data.get("working_image", ""))
    if not source.exists() and source_data.get("working_image"):
        source = Path(source_data["working_image"])
    if not source.exists():
        return None
    assets_dir = output_path.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    target = assets_dir / source.name
    shutil.copy2(source, target)
    return f"assets/{target.name}"


def _should_render_block(block: dict) -> bool:
    text = block.get("text", "").strip()
    if not text:
        return False
    if block.get("confidence", 0) < 55:
        return False
    return any(char.isalnum() for char in text)


def _block_font_size(block: dict, scale: float) -> float:
    x1, y1, x2, y2 = block["bbox"]
    word_heights = [
        word["bbox"][3] - word["bbox"][1]
        for word in block.get("words", [])
        if word.get("bbox") and word["bbox"][3] - word["bbox"][1] > 2
    ]
    source_height = median(word_heights) if word_heights else y2 - y1
    max_size = 16.0 if block.get("type") == "heading" else 14.0
    return max(7.0, min(max_size, source_height * scale * 0.82))


def _render_fields(document: dict, scale: float) -> str:
    fields = document.get("content", {}).get("fields", [])
    parts = []
    for field in fields:
        x1, y1, x2, y2 = field["bbox"]
        parts.append(
            f'    <div class="field-box" title="{escape(field["name"])}" '
            f'style="left:{x1 * scale:.1f}px; top:{y1 * scale:.1f}px; '
            f'width:{(x2 - x1) * scale:.1f}px; height:{(y2 - y1) * scale:.1f}px;"></div>'
        )
    if not parts:
        return ""
    return "\n".join(parts) + "\n"


def _render_lines(document: dict, scale: float) -> str:
    lines = document.get("layout", {}).get("visual_elements", {}).get("lines", [])
    parts = []
    for line in lines:
        x1, y1, x2, y2 = line["bbox"]
        width = max(1.0, (x2 - x1) * scale)
        height = max(1.0, (y2 - y1) * scale)
        parts.append(
            f'    <div class="detected-line {escape(line["orientation"])}" '
            f'style="left:{x1 * scale:.1f}px; top:{y1 * scale:.1f}px; '
            f'width:{width:.1f}px; height:{height:.1f}px;"></div>'
        )
    if not parts:
        return ""
    return "\n".join(parts) + "\n"
