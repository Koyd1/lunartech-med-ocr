from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from PIL import Image

from lunartech_doc_ai.layout import (
    build_text_blocks,
    extract_fields,
    extract_notes,
    extract_sections,
    infer_document_title,
)
from lunartech_doc_ai.ocr import choose_ocr_languages, get_available_tesseract_languages, run_tesseract_tsv
from lunartech_doc_ai.pdf_export import render_pdf_from_html
from lunartech_doc_ai.pdf import convert_pdf_first_page_to_png
from lunartech_doc_ai.preprocess import prepare_degraded_ocr_image, prepare_ocr_image
from lunartech_doc_ai.render import render_html
from lunartech_doc_ai.schemas import extract_schema
from lunartech_doc_ai.visual import detect_form_lines


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


@dataclass(frozen=True)
class OCRCandidate:
    name: str
    preprocessing: str
    image_path: Path
    psm: int
    width: int
    height: int
    words: list
    blocks: list[dict]
    fields: list[dict]
    schema: dict
    form_lines: list[dict]
    mean_confidence: float
    score: float


def process_image(
    image_path: Path | str,
    *,
    output_dir: Path | str = "output",
    source_path: Path | str | None = None,
    source_type: str = "image",
) -> dict:
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    source_path = Path(source_path) if source_path else image_path
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported image extension: {image_path.suffix}")

    ocr_languages = choose_ocr_languages(get_available_tesseract_languages())
    candidates = _build_ocr_candidates(
        image_path=image_path,
        output_dir=output_dir,
        source_filename=source_path.name,
        ocr_languages=ocr_languages,
    )
    candidate = max(candidates, key=lambda item: item.score)

    working_image = candidate.image_path
    width = candidate.width
    height = candidate.height
    words = candidate.words
    blocks = candidate.blocks
    fields = candidate.fields
    form_lines = candidate.form_lines
    schema = candidate.schema
    sections = _ensure_schema_sections(extract_sections(blocks), schema, blocks)
    title = infer_document_title(blocks, fallback=image_path.stem)
    mean_confidence = candidate.mean_confidence

    json_path = output_dir / "json" / f"{image_path.stem}.json"
    html_path = output_dir / "html" / f"{image_path.stem}.html"
    pdf_path = output_dir / "pdf" / f"{image_path.stem}.pdf"

    document = {
        "schema_version": "0.1",
        "source": {
            "filename": source_path.name,
            "path": str(source_path),
            "type": source_type,
            "working_image": str(working_image),
            "original_image": str(image_path),
        },
        "document": {
            "title": title,
            "document_type": infer_document_type(title, blocks),
            "subtype": schema["subtype"],
            "processed_at": datetime.now(timezone.utc).isoformat(),
        },
        "layout": {
            "page": {
                "width": width,
                "height": height,
                "unit": "px",
            },
            "visual_elements": {
                "lines": form_lines,
            },
        },
        "content": {
            "fields": fields,
            "schema_fields": schema["fields"],
            "sections": sections,
            "tables": schema["tables"],
            "notes": extract_notes(blocks),
            "text_blocks": blocks,
            "full_text": "\n".join(block["text"] for block in blocks),
        },
        "quality": {
            "ocr_engine": "tesseract",
            "ocr_languages": ocr_languages,
            "ocr_psm": candidate.psm,
            "ocr_candidate": candidate.name,
            "preprocessing": candidate.preprocessing,
            "mean_confidence": mean_confidence,
            "word_count": len(words),
            "candidate_scores": [
                {
                    "name": item.name,
                    "preprocessing": item.preprocessing,
                    "score": round(item.score, 2),
                    "mean_confidence": item.mean_confidence,
                    "word_count": len(item.words),
                    "subtype": item.schema["subtype"],
                }
                for item in candidates
            ],
            "low_confidence_blocks": [
                block["id"] for block in blocks if block["confidence"] < 55
            ],
        },
        "outputs": {
            "json": str(json_path),
            "html": str(html_path),
            "pdf": str(pdf_path),
            "pdf_status": "not_rendered",
        },
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    render_html(document, html_path)
    if render_pdf_from_html(html_path, pdf_path):
        document["outputs"]["pdf_status"] = "rendered"
    else:
        document["outputs"]["pdf_status"] = "renderer_unavailable"
    json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return document


def _build_ocr_candidates(
    *,
    image_path: Path,
    output_dir: Path,
    source_filename: str,
    ocr_languages: str,
) -> list[OCRCandidate]:
    standard_image = output_dir / "tmp" / "ocr" / f"{image_path.stem}_ocr.png"
    prepare_ocr_image(image_path, standard_image)
    standard = _read_ocr_candidate(
        name="standard",
        preprocessing="standard_autocontrast",
        image_path=standard_image,
        source_filename=source_filename,
        ocr_languages=ocr_languages,
        psm=11,
    )
    candidates = [standard]

    if _should_try_degraded_candidate(standard):
        degraded_image = output_dir / "tmp" / "ocr" / f"{image_path.stem}_ocr_degraded.png"
        prepare_degraded_ocr_image(image_path, degraded_image)
        candidates.append(
            _read_ocr_candidate(
                name="degraded",
                preprocessing="upscale_then_autocontrast",
                image_path=degraded_image,
                source_filename=source_filename,
                ocr_languages=ocr_languages,
                psm=11,
            )
        )

    return candidates


def _read_ocr_candidate(
    *,
    name: str,
    preprocessing: str,
    image_path: Path,
    source_filename: str,
    ocr_languages: str,
    psm: int,
) -> OCRCandidate:
    with Image.open(image_path) as image:
        width, height = image.size

    words = run_tesseract_tsv(image_path, lang=ocr_languages, psm=psm)
    blocks = build_text_blocks(words)
    fields = extract_fields(blocks)
    schema = extract_schema(blocks, source_filename=source_filename)
    fields = merge_schema_fields(fields, schema)
    form_lines = detect_form_lines(image_path, min_length=max(120, int(width * 0.18)))
    mean_confidence = round(mean(word.confidence for word in words), 2) if words else 0.0

    return OCRCandidate(
        name=name,
        preprocessing=preprocessing,
        image_path=image_path,
        psm=psm,
        width=width,
        height=height,
        words=words,
        blocks=blocks,
        fields=fields,
        schema=schema,
        form_lines=form_lines,
        mean_confidence=mean_confidence,
        score=_ocr_candidate_score(
            mean_confidence=mean_confidence,
            word_count=len(words),
            schema=schema,
        ),
    )


def _should_try_degraded_candidate(candidate: OCRCandidate) -> bool:
    return (
        candidate.mean_confidence < 75
        or len(candidate.words) < 80
        or candidate.schema["subtype"] == "generic_medical_document"
    )


def _ocr_candidate_score(*, mean_confidence: float, word_count: int, schema: dict) -> float:
    table_rows = sum(len(table.get("rows", [])) for table in schema.get("tables", []))
    schema_fields = len(schema.get("fields", {}))
    subtype_bonus = 0 if schema["subtype"] == "generic_medical_document" else 25
    return (
        mean_confidence
        + min(word_count, 220) / 8
        + subtype_bonus
        + table_rows * 4
        + schema_fields * 1.5
    )


def _ensure_schema_sections(
    sections: list[dict],
    schema: dict,
    blocks: list[dict],
) -> list[dict]:
    if sections:
        return sections
    if schema["subtype"] != "molecular_lab_report" or not schema.get("tables"):
        return sections

    block_by_id = {block["id"]: block for block in blocks}
    result_blocks = [
        block_by_id[row["source_block_id"]]
        for table in schema["tables"]
        for row in table.get("rows", [])
        if row.get("source_block_id") in block_by_id
    ]
    if not result_blocks:
        return sections

    return [
        {
            "id": "section_0001",
            "title": "Molecular biology results",
            "level": 1,
            "source_block_id": result_blocks[0]["id"],
            "block_ids": [block["id"] for block in result_blocks],
            "bbox": [
                min(block["bbox"][0] for block in result_blocks),
                min(block["bbox"][1] for block in result_blocks),
                max(block["bbox"][2] for block in result_blocks),
                max(block["bbox"][3] for block in result_blocks),
            ],
            "confidence": round(mean(block["confidence"] for block in result_blocks), 2),
            "extraction_method": "schema_fallback",
        }
    ]


def merge_schema_fields(fields: list[dict], schema: dict) -> list[dict]:
    merged = list(fields)
    existing = {(field.get("name"), field.get("value")) for field in merged}
    for key, field in schema.get("fields", {}).items():
        item = {
            "name": key,
            "value": field["value"],
            "source_block_id": field["source_block_id"],
            "value_block_id": None,
            "confidence": field["confidence"],
            "bbox": field["bbox"],
            "extraction_method": field["extraction_method"],
            "schema_key": key,
        }
        dedupe_key = (item["name"], item["value"])
        if dedupe_key not in existing:
            merged.append(item)
            existing.add(dedupe_key)
    return merged


def infer_document_type(title: str, blocks: list[dict]) -> str:
    text = " ".join([title] + [block["text"] for block in blocks[:12]]).lower()
    if "adever" in text and ("medical" in text or "medicala" in text or "nr." in text):
        return "medical_certificate"
    if "rx" in text or "tab" in text:
        return "prescription"
    if "investigatii" in text or "biologie moleculara" in text:
        return "lab_report"
    return "medical_document"


def process_path(input_path: Path | str, *, output_dir: Path | str = "output") -> list[dict]:
    input_path = Path(input_path)
    if input_path.is_file():
        if input_path.suffix.lower() == ".pdf":
            return [process_pdf(input_path, output_dir=output_dir)]
        return [process_image(input_path, output_dir=output_dir)]

    results: list[dict] = []
    for path in sorted(input_path.iterdir()):
        if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            results.append(process_image(path, output_dir=output_dir))
        elif path.suffix.lower() == ".pdf":
            results.append(process_pdf(path, output_dir=output_dir))
    return results


def process_pdf(pdf_path: Path | str, *, output_dir: Path | str = "output") -> dict:
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    working_image = output_dir / "tmp" / "pages" / f"{pdf_path.stem}_page_1.png"
    convert_pdf_first_page_to_png(pdf_path, working_image)
    return process_image(
        working_image,
        output_dir=output_dir,
        source_path=pdf_path,
        source_type="pdf",
    )
