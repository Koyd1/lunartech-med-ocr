from pathlib import Path

from PIL import Image

from lunartech_doc_ai.pdf import convert_pdf_first_page_to_png


def test_convert_pdf_first_page_to_png(tmp_path):
    source_pdf = tmp_path / "sample.pdf"
    output_png = tmp_path / "sample.png"
    Image.new("RGB", (40, 30), "white").save(source_pdf, "PDF")

    convert_pdf_first_page_to_png(source_pdf, output_png)

    assert output_png.exists()
    with Image.open(output_png) as image:
        assert image.width > 0
        assert image.height > 0
