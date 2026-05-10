from pathlib import Path

from lunartech_doc_ai.render import render_html


def test_render_html_includes_source_underlay_when_asset_is_available(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")
    output_path = tmp_path / "doc.html"
    document = {
        "source": {"filename": "page.png", "working_image": str(image_path)},
        "document": {"title": "Title"},
        "layout": {"page": {"width": 100, "height": 80}},
        "quality": {"ocr_engine": "tesseract", "mean_confidence": 90},
        "content": {
            "text_blocks": [
                {
                    "id": "line_0001",
                    "type": "heading",
                    "text": "Title",
                    "bbox": [10, 10, 50, 20],
                    "confidence": 90,
                }
            ]
        },
    }

    render_html(document, output_path)

    html = output_path.read_text(encoding="utf-8")
    assert "page-underlay" in html
    assert "assets/page.png" in html
    assert (tmp_path / "assets" / "page.png").exists()


def test_render_html_prefers_original_image_for_visual_underlay(tmp_path):
    working_image = tmp_path / "page_ocr.png"
    original_image = tmp_path / "page.png"
    working_image.write_bytes(b"ocr")
    original_image.write_bytes(b"original")
    output_path = tmp_path / "doc.html"
    document = {
        "source": {
            "filename": "page.png",
            "working_image": str(working_image),
            "original_image": str(original_image),
        },
        "document": {"title": "Title"},
        "layout": {"page": {"width": 100, "height": 80}},
        "quality": {"ocr_engine": "tesseract", "mean_confidence": 90},
        "content": {"text_blocks": []},
    }

    render_html(document, output_path)

    html = output_path.read_text(encoding="utf-8")
    assert "assets/page.png" in html
    assert "assets/page_ocr.png" not in html


def test_render_html_omits_low_confidence_noise_blocks(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")
    output_path = tmp_path / "doc.html"
    document = {
        "source": {"filename": "page.png", "working_image": str(image_path)},
        "document": {"title": "Title"},
        "layout": {"page": {"width": 100, "height": 80}},
        "quality": {"ocr_engine": "tesseract", "mean_confidence": 90},
        "content": {
            "text_blocks": [
                {
                    "id": "line_0001",
                    "type": "paragraph",
                    "text": "DI A",
                    "bbox": [10, 10, 60, 40],
                    "confidence": 34,
                }
            ]
        },
    }

    render_html(document, output_path)

    html = output_path.read_text(encoding="utf-8")
    assert "DI A" not in html


def test_render_html_hides_visible_ocr_text_for_degraded_candidate(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")
    output_path = tmp_path / "doc.html"
    document = {
        "source": {"filename": "page.png", "working_image": str(image_path)},
        "document": {"title": "Title"},
        "layout": {"page": {"width": 100, "height": 80}},
        "quality": {
            "ocr_engine": "tesseract",
            "mean_confidence": 64,
            "ocr_candidate": "degraded",
        },
        "content": {
            "text_blocks": [
                {
                    "id": "line_0001",
                    "type": "paragraph",
                    "text": "Noisy text",
                    "bbox": [10, 10, 60, 40],
                    "confidence": 90,
                }
            ]
        },
    }

    render_html(document, output_path)

    html = output_path.read_text(encoding="utf-8")
    assert "Noisy text" not in html
