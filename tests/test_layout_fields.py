from lunartech_doc_ai.layout import extract_fields, extract_notes, extract_sections


def test_extract_fields_uses_neighboring_value_blocks():
    blocks = [
        {
            "id": "line_0001",
            "type": "paragraph",
            "text": "Numele, prenumele",
            "bbox": [95, 376, 322, 399],
            "confidence": 91.97,
        },
        {
            "id": "line_0002",
            "type": "heading",
            "text": "MOROZ ALEXANDR",
            "bbox": [474, 376, 729, 394],
            "confidence": 89.85,
        },
        {
            "id": "line_0003",
            "type": "paragraph",
            "text": "Numar de identificare",
            "bbox": [95, 448, 349, 466],
            "confidence": 77.01,
        },
        {
            "id": "line_0004",
            "type": "paragraph",
            "text": "2003500227856",
            "bbox": [510, 449, 715, 467],
            "confidence": 96.07,
        },
    ]

    fields = extract_fields(blocks)

    assert _value_for(fields, "Numele") == "MOROZ ALEXANDR"
    assert _value_for(fields, "Numar de identificare") == "2003500227856"


def test_extract_fields_ignores_label_words_inside_descriptors():
    blocks = [
        {
            "id": "line_0001",
            "type": "paragraph",
            "text": "(gradul militar, semnatura, numele si initialele)",
            "bbox": [870, 1614, 1378, 1674],
            "confidence": 73.39,
        }
    ]

    fields = extract_fields(blocks)

    assert fields == []


def test_extract_fields_ignores_name_initials_descriptor():
    blocks = [
        {
            "id": "line_0001",
            "type": "paragraph",
            "text": "numele şi inițialele",
            "bbox": [870, 1614, 1378, 1674],
            "confidence": 73.39,
        }
    ]

    fields = extract_fields(blocks)

    assert fields == []


def test_extract_sections_uses_semantic_headings_not_table_rows():
    blocks = [
        _block("line_0001", "DE LABORATOR", [600, 100, 900, 130], block_type="heading"),
        _block("line_0002", "Panel infecții sexual transmisibile", [90, 300, 580, 330]),
        _block("line_0003", "Chlamydia trachomatis, ADN", [90, 400, 370, 425], block_type="heading"),
        _block("line_0004", "NEGATIV", [930, 400, 1020, 425], block_type="heading"),
        _block("line_0005", "Caracteristici de diagnostic", [90, 1100, 320, 1120]),
    ]

    sections = extract_sections(blocks)

    assert [section["title"] for section in sections] == [
        "DE LABORATOR",
        "Panel infecții sexual transmisibile",
        "Caracteristici de diagnostic",
    ]


def test_extract_notes_captures_interpretation_and_uncertainty_notes():
    blocks = [
        _block(
            "line_0001",
            "NEGATIV - în eşantion nu au fost detectate secvenţe de ADN specifice.",
            [90, 1200, 700, 1220],
        ),
        _block(
            "line_0002",
            "Rezultatele investigaţiilor de laborator nu reprezintă diagnosticul clinic.",
            [90, 1300, 760, 1320],
        ),
        _block("line_0003", "Chlamydia trachomatis, ADN", [90, 400, 370, 425]),
        _block("line_0004", "Centru consultativ-diagnostic MA RM", [90, 500, 370, 525]),
    ]

    notes = extract_notes(blocks)

    assert len(notes) == 2
    assert notes[0]["category"] == "interpretation"
    assert notes[1]["category"] == "clinical_limitation"


def _value_for(fields: list[dict], name: str) -> str:
    for field in fields:
        if field["name"] == name:
            return field["value"]
    raise AssertionError(f"Missing field {name}")


def _block(
    block_id: str,
    text: str,
    bbox: list[int],
    *,
    block_type: str = "paragraph",
    confidence: float = 90.0,
) -> dict:
    return {
        "id": block_id,
        "type": block_type,
        "text": text,
        "bbox": bbox,
        "confidence": confidence,
    }
