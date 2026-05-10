from pathlib import Path

from lunartech_doc_ai.pipeline import _ensure_schema_sections, _ocr_candidate_score, process_image


def test_process_image_returns_structured_extraction(tmp_path):
    image_path = Path("test-img/Adeverinta Medicala AUTO.png")

    result = process_image(image_path, output_dir=tmp_path)

    assert result["source"]["filename"] == "Adeverinta Medicala AUTO.png"
    assert result["document"]["title"]
    assert result["document"]["subtype"] == "driver_medical_certificate"
    assert result["layout"]["page"]["width"] > 0
    assert result["layout"]["page"]["height"] > 0
    assert result["content"]["text_blocks"]
    assert result["content"]["fields"]
    assert result["content"]["schema_fields"]["patient_name"]["value"]
    assert "tables" in result["content"]
    assert result["quality"]["ocr_engine"] == "tesseract"
    assert 0 <= result["quality"]["mean_confidence"] <= 100


def test_process_image_writes_json_and_html_outputs(tmp_path):
    image_path = Path("test-img/Adeverinta Medicala AUTO.png")

    result = process_image(image_path, output_dir=tmp_path)

    stem = image_path.stem
    assert result["outputs"]["json"] == str(tmp_path / "json" / f"{stem}.json")
    assert result["outputs"]["html"] == str(tmp_path / "html" / f"{stem}.html")
    assert (tmp_path / "json" / f"{stem}.json").exists()
    assert (tmp_path / "html" / f"{stem}.html").exists()


def test_ocr_candidate_score_prefers_structured_schema_over_confidence_only():
    generic_score = _ocr_candidate_score(
        mean_confidence=72.0,
        word_count=50,
        schema={"subtype": "generic_medical_document", "fields": {}, "tables": []},
    )
    structured_score = _ocr_candidate_score(
        mean_confidence=64.0,
        word_count=300,
        schema={
            "subtype": "molecular_lab_report",
            "fields": {"patient_name": {"value": "A"}},
            "tables": [{"rows": [{"test_name": "HPV", "result": "NEGATIV"}] * 8}],
        },
    )

    assert structured_score > generic_score


def test_schema_section_fallback_adds_lab_result_section_when_headings_are_missing():
    blocks = [
        {
            "id": "line_0001",
            "type": "paragraph",
            "text": "Chlamydia trachomatis, ADN",
            "bbox": [90, 500, 370, 525],
            "confidence": 80,
        }
    ]
    schema = {
        "subtype": "molecular_lab_report",
        "fields": {},
        "tables": [{"rows": [{"source_block_id": "line_0001"}]}],
    }

    sections = _ensure_schema_sections([], schema, blocks)

    assert sections[0]["title"] == "Molecular biology results"
    assert sections[0]["extraction_method"] == "schema_fallback"
