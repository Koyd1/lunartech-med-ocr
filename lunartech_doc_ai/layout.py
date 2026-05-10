from __future__ import annotations

import re
from collections import defaultdict
from statistics import mean

from lunartech_doc_ai.ocr import OCRWord


def build_text_blocks(words: list[OCRWord]) -> list[dict]:
    grouped: dict[tuple[int, int, int], list[OCRWord]] = defaultdict(list)
    for word in words:
        grouped[(word.block_num, word.par_num, word.line_num)].append(word)

    blocks: list[dict] = []
    for index, (_, line_words) in enumerate(sorted(grouped.items(), key=_line_sort_key), start=1):
        ordered = sorted(line_words, key=lambda item: (item.left, item.word_num))
        text = " ".join(word.text for word in ordered)
        bbox = _bbox(ordered)
        blocks.append(
            {
                "id": f"line_{index:04d}",
                "type": classify_line(text),
                "text": text,
                "bbox": bbox,
                "confidence": round(mean(word.confidence for word in ordered), 2),
                "words": [
                    {
                        "text": word.text,
                        "confidence": round(word.confidence, 2),
                        "bbox": [word.left, word.top, word.right, word.bottom],
                    }
                    for word in ordered
                ],
            }
        )
    return blocks


def infer_document_title(blocks: list[dict], fallback: str) -> str:
    candidates = [
        block
        for block in blocks[:50]
        if len(block["text"]) >= 4 and block["type"] in {"heading", "field_line", "paragraph"}
    ]
    if not candidates:
        candidates = [block for block in blocks[:15] if len(block["text"]) >= 4]
    if not candidates:
        return fallback
    return max(candidates, key=_title_score)["text"]


def extract_fields(blocks: list[dict]) -> list[dict]:
    fields: list[dict] = []
    for block in blocks:
        text = block["text"].strip()
        label = _extract_label(text)
        if label:
            name, remainder = label
            value_block = _find_neighbor_value_block(block, blocks)
            value = _clean_field_value(remainder)
            if not value and value_block:
                value = value_block["text"].strip()
            if value:
                bbox = _merge_block_bboxes(block, value_block) if value_block else block["bbox"]
                confidence_values = [block["confidence"]]
                if value_block:
                    confidence_values.append(value_block["confidence"])
                fields.append(
                    {
                        "name": name,
                        "value": value,
                        "source_block_id": block["id"],
                        "value_block_id": value_block["id"] if value_block else None,
                        "confidence": round(mean(confidence_values), 2),
                        "bbox": bbox,
                        "extraction_method": "neighbor_geometry" if value_block else "inline_text",
                    }
                )
                continue

        field = _extract_key_value(text)
        if field:
            fields.append(
                {
                    "name": field[0],
                    "value": field[1],
                    "source_block_id": block["id"],
                    "value_block_id": None,
                    "confidence": block["confidence"],
                    "bbox": block["bbox"],
                    "extraction_method": "inline_text",
                }
            )

    if fields:
        return fields

    # Fallback keeps downstream consumers useful even for documents without obvious labels.
    for block in blocks[:8]:
        if len(block["text"]) >= 6 and not _is_instructional_descriptor(block["text"]):
            fields.append(
                {
                    "name": "text_line",
                    "value": block["text"],
                    "source_block_id": block["id"],
                    "confidence": block["confidence"],
                    "bbox": block["bbox"],
                }
            )
    return fields


def extract_sections(blocks: list[dict]) -> list[dict]:
    headings = [
        (index, block)
        for index, block in enumerate(blocks)
        if _is_section_heading(block)
    ]
    sections: list[dict] = []
    for section_index, (block_index, heading) in enumerate(headings, start=1):
        next_index = headings[section_index][0] if section_index < len(headings) else len(blocks)
        section_blocks = [
            block
            for block in blocks[block_index + 1 : next_index]
            if _is_section_body_block(block)
        ]
        grouped_blocks = [heading, *section_blocks]
        sections.append(
            {
                "id": f"section_{section_index:04d}",
                "title": heading["text"],
                "level": 1 if heading["type"] == "heading" else 2,
                "source_block_id": heading["id"],
                "block_ids": [block["id"] for block in section_blocks],
                "bbox": _merge_dict_bboxes(grouped_blocks),
                "confidence": heading["confidence"],
                "extraction_method": "semantic_heading",
            }
        )
    return sections


def extract_notes(blocks: list[dict]) -> list[dict]:
    notes = []
    for block in blocks:
        category = _note_category(block["text"])
        if not category or block["confidence"] < 45:
            continue
        notes.append(
            {
                "id": f"note_{len(notes) + 1:04d}",
                "category": category,
                "text": block["text"],
                "source_block_id": block["id"],
                "bbox": block["bbox"],
                "confidence": block["confidence"],
            }
        )
    return notes


def classify_line(text: str) -> str:
    clean = text.strip()
    letters = [char for char in clean if char.isalpha()]
    uppercase_ratio = (
        sum(1 for char in letters if char.isupper()) / len(letters)
        if letters
        else 0.0
    )

    if len(clean) <= 3:
        return "marker"
    if uppercase_ratio > 0.65 and len(clean) > 8:
        return "heading"
    if _extract_key_value(clean):
        return "field_line"
    if re.search(r"\b\d{2}[./-]\d{2}[./-]\d{4}\b", clean):
        return "date_line"
    return "paragraph"


SECTION_HEADING_TERMS = [
    "adeverinta",
    "adeverinţa",
    "adeverința",
    "documenta",
    "медицинская",
    "concluzia",
    "заключение",
    "laborator",
    "panel",
    "caracteristici",
    "diagnosticul",
    "executat",
    "validat",
]


def _is_section_heading(block: dict) -> bool:
    text = " ".join(block["text"].split())
    lowered = text.lower()
    if block["confidence"] < 55 or len(text) < 4 or len(text) > 120:
        return False
    if lowered.startswith("(") or "se indic" in lowered:
        return False
    if _looks_like_lab_result_or_test_row(text):
        return False
    if _note_category(text) in {"interpretation", "clinical_limitation", "accreditation"}:
        return False
    if _is_explicit_section_phrase(lowered):
        return True
    if block["type"] != "heading":
        return False
    return any(term in lowered for term in SECTION_HEADING_TERMS)


def _looks_like_lab_result_or_test_row(text: str) -> bool:
    normalized = text.strip()
    upper = normalized.upper()
    if upper.startswith(("NEGATIV", "POZITIV")):
        return True
    if "ADN" in normalized or "HPV" in normalized:
        return True
    return upper in {"NEGATIV", "POZITIV"}


def _is_explicit_section_phrase(lowered: str) -> bool:
    return (
        lowered.startswith("panel ")
        or lowered.startswith("caracteristici de diagnostic")
        or lowered.startswith("executat")
        or lowered.startswith("validat")
        or ("diagnosticul" in lowered and "decizia" in lowered)
        or "concluzia" in lowered
        or "заключение" in lowered
    )


def _is_section_body_block(block: dict) -> bool:
    text = block["text"].strip()
    return block["confidence"] >= 35 and len(text) >= 2


def _merge_dict_bboxes(blocks: list[dict]) -> list[int]:
    return [
        min(block["bbox"][0] for block in blocks),
        min(block["bbox"][1] for block in blocks),
        max(block["bbox"][2] for block in blocks),
        max(block["bbox"][3] for block in blocks),
    ]


def _note_category(text: str) -> str | None:
    lowered = text.lower()
    if "negativ" in lowered and "secven" in lowered:
        return "interpretation"
    if "pozitiv" in lowered and "secven" in lowered:
        return "interpretation"
    if "caracteristici" in lowered or "sensibilitatea" in lowered or "specificitatea" in lowered:
        return "diagnostic_characteristics"
    if "acreditate" in lowered or "acreditat" in lowered:
        return "accreditation"
    if (
        "nu reprezint" in lowered
        or "consultați medic" in lowered
        or "consultati medic" in lowered
        or "diagnosticul clinic" in lowered
    ):
        return "clinical_limitation"
    return None


def _line_sort_key(item: tuple[tuple[int, int, int], list[OCRWord]]) -> tuple[int, int]:
    words = item[1]
    return (min(word.top for word in words), min(word.left for word in words))


def _bbox(words: list[OCRWord]) -> list[int]:
    return [
        min(word.left for word in words),
        min(word.top for word in words),
        max(word.right for word in words),
        max(word.bottom for word in words),
    ]


def _extract_key_value(text: str) -> tuple[str, str] | None:
    normalized = " ".join(text.split())
    label = _extract_label(normalized)
    if label:
        name, remainder = label
        value = _clean_field_value(remainder)
        if value:
            return (name, value)

    colon_match = re.match(r"^([A-Za-zА-Яа-яăâîșțĂÂÎȘȚ ,./-]{3,45})[:：]\s*(.+)$", normalized)
    if colon_match:
        return (colon_match.group(1).strip(), colon_match.group(2).strip())

    return None


FIELD_LABELS: list[tuple[str, list[str]]] = [
    ("Numele", ["Numele, prenumele", "Numele"]),
    ("Numar de identificare", ["Numar de identificare", "Număr de identificare"]),
    ("Data nasterii", ["Data nasterii", "Data nașterii"]),
    ("Categoriile", ["Categoriile", "Categoria"]),
    ("Cod restrictie", ["Cod restrictie", "Cod restricție"]),
    ("Urmatoarea reexaminare", ["Urmatoarea reexaminare", "Următoarea reexaminare"]),
    ("Data eliberarii", ["Data eliberarii", "Data eliberării"]),
    ("Presedintele comisiei", ["Presedintele comisiei", "Președintele comisiei"]),
    ("Student", ["Student"]),
    ("Diagnosticul", ["Diagnosticul"]),
    ("Conform paragrafului", ["Conform paragrafului"]),
    ("Apt pentru", ["Apt pentru"]),
]


def _extract_label(text: str) -> tuple[str, str] | None:
    normalized = " ".join(text.split())
    for canonical, aliases in FIELD_LABELS:
        for alias in aliases:
            match = re.search(re.escape(alias), normalized, flags=re.IGNORECASE)
            if match and _is_label_position(normalized, match.start()):
                return canonical, normalized[match.end() :]
    return None


def _clean_field_value(value: str) -> str:
    cleaned = value.strip(" :_-.,()")
    if not cleaned:
        return ""
    descriptor_words = {
        "prenumele",
        "patronimicul",
        "numele",
        "si",
        "şi",
        "și",
        "initialele",
        "inițialele",
        "iniţialele",
        "familia",
        "имя",
        "отчество",
    }
    tokens = {token.strip(" ,.;:-").lower() for token in cleaned.split()}
    if tokens and tokens.issubset(descriptor_words):
        return ""
    return cleaned


def _find_neighbor_value_block(label_block: dict, blocks: list[dict]) -> dict | None:
    lx1, ly1, lx2, ly2 = label_block["bbox"]
    label_center_y = (ly1 + ly2) / 2
    label_height = max(1, ly2 - ly1)
    candidates: list[tuple[float, dict]] = []

    for candidate in blocks:
        if candidate["id"] == label_block["id"]:
            continue
        if candidate["type"] == "marker":
            continue
        if _extract_label(candidate["text"]):
            continue
        cx1, cy1, cx2, cy2 = candidate["bbox"]
        candidate_center_y = (cy1 + cy2) / 2
        vertical_delta = abs(candidate_center_y - label_center_y)
        if vertical_delta > max(16, label_height * 1.1):
            continue
        if cx1 <= lx2:
            continue
        text = candidate["text"].strip()
        if len(text) < 2:
            continue
        distance = cx1 - lx2
        candidates.append((distance + vertical_delta * 2, candidate))

    if not candidates:
        return None
    return min(candidates, key=lambda item: item[0])[1]


def _merge_block_bboxes(block: dict, value_block: dict | None) -> list[int]:
    if not value_block:
        return block["bbox"]
    x1, y1, x2, y2 = block["bbox"]
    vx1, vy1, vx2, vy2 = value_block["bbox"]
    return [min(x1, vx1), min(y1, vy1), max(x2, vx2), max(y2, vy2)]


def _is_label_position(text: str, start: int) -> bool:
    prefix = text[:start].strip(" \t:-")
    if not prefix:
        return True
    # Parenthesized helper text often repeats field names as instructions.
    if prefix in {"(", "(se indica", "(gradul militar,"}:
        return False
    return len(prefix) <= 2 and not prefix.startswith("(")


def _is_instructional_descriptor(text: str) -> bool:
    normalized = text.strip().lower()
    if normalized.startswith("(") and normalized.endswith(")"):
        return True
    descriptor_tokens = {
        token.strip(" ,.;:-()")
        for token in normalized.replace("și", "şi").split()
    }
    return bool(descriptor_tokens) and descriptor_tokens.issubset(
        {"numele", "şi", "si", "initialele", "inițialele", "iniţialele"}
    )


def _title_score(block: dict) -> tuple[float, float, int]:
    text = block["text"].lower()
    height = block["bbox"][3] - block["bbox"][1]
    score = 0.0
    if "adever" in text or "medical" in text or "certificat" in text:
        score += 100.0
    if block["type"] == "heading":
        score += 20.0
    if block["confidence"] >= 40:
        score += block["confidence"] / 5.0
    return (score, height, len(text))
