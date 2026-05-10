from __future__ import annotations

import re
from statistics import mean


def extract_schema(blocks: list[dict], *, source_filename: str = "") -> dict:
    subtype = classify_subtype(blocks, source_filename=source_filename)
    if subtype == "driver_medical_certificate":
        return _driver_medical_certificate_schema(blocks)
    if subtype == "military_medical_certificate":
        return _military_medical_certificate_schema(blocks)
    if subtype == "molecular_lab_report":
        return _molecular_lab_report_schema(blocks)
    return {"subtype": "generic_medical_document", "fields": {}, "tables": []}


def classify_subtype(blocks: list[dict], *, source_filename: str = "") -> str:
    joined = _joined_text(blocks).lower()
    filename = source_filename.lower()
    if "auto" in filename or "conduc" in joined or "permisului de conducere" in joined:
        return "driver_medical_certificate"
    if "militar" in filename or "serviciul militar" in joined or "catedră militară" in joined:
        return "military_medical_certificate"
    if "laborator" in joined or "biologie_moleculara" in filename or "chlamydia" in joined:
        return "molecular_lab_report"
    return "generic_medical_document"


def _driver_medical_certificate_schema(blocks: list[dict]) -> dict:
    fields = {}
    _put_neighbor_field(fields, "patient_name", "Numele", blocks)
    _put_neighbor_field(fields, "idnp", "identificare", blocks)
    _put_neighbor_field(fields, "birth_date", "Data na", blocks)
    _put_neighbor_field(fields, "medical_exam_date", "A trecut examinarea", blocks)
    category_block = _find_category_code_block(blocks)
    if category_block:
        _put_field(fields, "categories", category_block["text"], category_block)
    restriction_label = _find_block_containing(blocks, "Cod rest")
    if restriction_label:
        restriction_blocks = _find_right_neighbors_same_row(restriction_label, blocks)
        if restriction_blocks:
            _put_field(
                fields,
                "restriction_code",
                " ".join(block["text"] for block in restriction_blocks),
                _merge_blocks("restriction_code", [restriction_label, *restriction_blocks]),
            )
    _put_neighbor_field(fields, "next_reexamination", "Următoarea", blocks)
    _put_neighbor_field(fields, "issue_date", "Data eliber", blocks)
    return {"subtype": "driver_medical_certificate", "fields": fields, "tables": []}


def _military_medical_certificate_schema(blocks: list[dict]) -> dict:
    fields = {}
    student = _find_block_containing(blocks, "Student")
    if student:
        _put_field(fields, "military_status", _remove_prefix(student["text"], "Student"), student)
        value = _find_right_neighbor(student, blocks)
        if value:
            _put_field(fields, "patient_name", value["text"], value)

    birth = _find_date_block(blocks)
    if birth:
        _put_field(fields, "birth_date", birth["text"], birth)

    sender = _find_block_containing(blocks, "Catedr")
    if sender:
        _put_field(fields, "referring_unit", sender["text"].strip("."), sender)

    exam_date = _extract_split_exam_date(blocks)
    if exam_date:
        _put_field(fields, "exam_date", exam_date["value"], exam_date["block"])

    diagnosis_label = _find_block_containing(blocks, "Diagnosticul")
    if diagnosis_label:
        diagnosis_value = _find_next_content_block(diagnosis_label, blocks)
        if diagnosis_value:
            _put_field(fields, "diagnosis", diagnosis_value["text"].strip("() "), diagnosis_value)

    decision = _find_block_containing(blocks, "Apt pentru")
    if decision:
        _put_field(fields, "fitness_decision", decision["text"].strip(), decision)

    return {"subtype": "military_medical_certificate", "fields": fields, "tables": []}


def _molecular_lab_report_schema(blocks: list[dict]) -> dict:
    fields = {}
    surname = _right_value_for_label(blocks, "Nume")
    given = _right_value_for_label(blocks, "Prenume")
    if surname and given:
        _put_field(
            fields,
            "patient_name",
            f"{surname['text']} {given['text']}",
            _merge_blocks("patient_name", [surname, given]),
        )
    elif surname:
        _put_field(fields, "patient_name", surname["text"], surname)

    _put_neighbor_field(fields, "birth_date", "Data nasterii", blocks)
    _put_neighbor_field(fields, "idnp", "CNP", blocks)
    _put_neighbor_field(fields, "sample_collected_at", "Recoltarea probei", blocks)
    _put_neighbor_field(fields, "sample_received_at", "Receptionarea probei", blocks)
    _put_neighbor_field(fields, "performed_at", "Data efectu", blocks)

    table_rows = _extract_lab_result_rows(blocks)
    tables = [
        {
            "name": "molecular_biology_results",
            "columns": ["test_name", "result", "reference"],
            "rows": table_rows,
        }
    ] if table_rows else []
    return {"subtype": "molecular_lab_report", "fields": fields, "tables": tables}


def _extract_lab_result_rows(blocks: list[dict]) -> list[dict]:
    rows = []
    left_blocks = [
        block
        for block in blocks
        if _is_lab_test_name_block(block)
    ]
    for test_block in left_blocks:
        y = _center_y(test_block)
        same_row = [
            block
            for block in blocks
            if abs(_center_y(block) - y) <= 14 and block["bbox"][0] > 800
        ]
        result = _nearest_text(same_row, min_x=850, max_x=1080)
        reference = _nearest_text(same_row, min_x=1080, max_x=1300)
        if result or reference:
            rows.append(
                {
                    "test_name": test_block["text"],
                    "result": result or "",
                    "reference": reference or "",
                    "source_block_id": test_block["id"],
                    "confidence": test_block["confidence"],
                }
            )
    return rows


def _put_neighbor_field(fields: dict, key: str, label_text: str, blocks: list[dict]) -> None:
    label = _find_block_containing(blocks, label_text)
    if not label:
        return
    value = _find_right_neighbor(label, blocks)
    if value:
        _put_field(fields, key, value["text"], _merge_blocks(key, [label, value]))


def _put_field(fields: dict, key: str, value: str, block: dict) -> None:
    value = _normalize_field_value(value)
    if not value:
        return
    fields[key] = {
        "value": value,
        "source_block_id": block["id"],
        "confidence": block.get("confidence", 0.0),
        "bbox": block["bbox"],
        "extraction_method": "schema_specific",
    }


def _find_block_containing(blocks: list[dict], text: str) -> dict | None:
    lowered = text.lower()
    for block in blocks:
        if lowered in block["text"].lower():
            return block
    return None


def _find_right_neighbor(label_block: dict, blocks: list[dict]) -> dict | None:
    lx1, ly1, lx2, ly2 = label_block["bbox"]
    y = (ly1 + ly2) / 2
    candidates = []
    for block in blocks:
        if block["id"] == label_block["id"]:
            continue
        bx1, by1, bx2, by2 = block["bbox"]
        if bx1 <= lx2:
            continue
        if abs(((by1 + by2) / 2) - y) > 22:
            continue
        if len(block["text"].strip()) < 2:
            continue
        candidates.append((bx1 - lx2, block))
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[0])[1]


def _find_right_neighbors_same_row(label_block: dict, blocks: list[dict]) -> list[dict]:
    lx1, ly1, lx2, ly2 = label_block["bbox"]
    y = (ly1 + ly2) / 2
    candidates = []
    for block in blocks:
        if block["id"] == label_block["id"]:
            continue
        bx1, by1, bx2, by2 = block["bbox"]
        if bx1 <= lx2:
            continue
        if abs(((by1 + by2) / 2) - y) > 22:
            continue
        if len(block["text"].strip()) < 2:
            continue
        candidates.append(block)
    return sorted(candidates, key=lambda block: block["bbox"][0])


def _right_value_for_label(blocks: list[dict], label_text: str) -> dict | None:
    label = _find_block_containing(blocks, label_text)
    if not label:
        return None
    return _find_right_neighbor(label, blocks)


def _find_date_block(blocks: list[dict]) -> dict | None:
    for block in blocks:
        if re.search(r"\b\d{2}[.-]\d{2}[.-]\d{4}\b", block["text"]):
            return block
    return None


def _extract_split_exam_date(blocks: list[dict]) -> dict | None:
    numeric = [
        block
        for block in blocks
        if re.fullmatch(r"\d{2}|\d{4}", block["text"].strip())
    ]
    for first in numeric:
        row = [
            block
            for block in numeric
            if abs(_center_y(block) - _center_y(first)) <= 8
        ]
        values = [block["text"].strip() for block in sorted(row, key=lambda item: item["bbox"][0])]
        if len(values) >= 3 and re.fullmatch(r"\d{2}", values[0]) and re.fullmatch(r"\d{2}", values[1]) and re.fullmatch(r"\d{4}", values[2]):
            return {"value": f"{values[0]}.{values[1]}.{values[2]}", "block": _merge_blocks("exam_date", row[:3])}
    return None


def _find_next_content_block(label_block: dict, blocks: list[dict]) -> dict | None:
    _, _, _, label_bottom = label_block["bbox"]
    candidates = [
        block
        for block in blocks
        if block["bbox"][1] >= label_bottom and block["confidence"] > 50 and len(block["text"]) > 10
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda block: block["bbox"][1] - label_bottom)


def _nearest_text(blocks: list[dict], *, min_x: int, max_x: int) -> str | None:
    candidates = [block for block in blocks if min_x <= block["bbox"][0] <= max_x]
    if not candidates:
        return None
    return min(candidates, key=lambda block: abs(block["bbox"][0] - min_x))["text"]


def _find_category_code_block(blocks: list[dict]) -> dict | None:
    pattern = re.compile(r"\b(?:AM|A1|A2|A|B1|B|АМ|А1|А2|В1|В)\b", flags=re.IGNORECASE)
    candidates = [
        block
        for block in blocks
        if pattern.search(block["text"]) and "," in block["text"] and block["bbox"][1] > 650
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda block: len(block["text"]))


def _is_lab_test_name_block(block: dict) -> bool:
    text = block["text"].strip()
    if block["bbox"][0] >= 700:
        return False
    if len(text) > 160 or "\t" in text:
        return False
    if text.upper().startswith(("NEGATIV", "POZITIV")):
        return False
    if "secven" in text.lower() or "eşantion" in text.lower() or "eșantion" in text.lower():
        return False
    return "ADN" in text or "HPV" in text


def _merge_blocks(block_id: str, blocks: list[dict]) -> dict:
    return {
        "id": block_id,
        "text": " ".join(block["text"] for block in blocks),
        "bbox": [
            min(block["bbox"][0] for block in blocks),
            min(block["bbox"][1] for block in blocks),
            max(block["bbox"][2] for block in blocks),
            max(block["bbox"][3] for block in blocks),
        ],
        "confidence": round(mean(block["confidence"] for block in blocks), 2),
    }


def _center_y(block: dict) -> float:
    return (block["bbox"][1] + block["bbox"][3]) / 2


def _remove_prefix(text: str, prefix: str) -> str:
    return re.sub(rf"^{re.escape(prefix)}", "", text, flags=re.IGNORECASE).strip()


def _joined_text(blocks: list[dict]) -> str:
    return " ".join(block["text"] for block in blocks)


def _normalize_field_value(value: str) -> str:
    normalized = value.strip(" :_")
    if normalized.count("(") > normalized.count(")") and normalized.endswith("}"):
        normalized = f"{normalized[:-1]})"
    return normalized
