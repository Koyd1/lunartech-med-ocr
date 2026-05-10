from pathlib import Path

from PIL import Image

from lunartech_doc_ai.redact import redact_image


def test_redact_image_writes_copy_with_filled_regions(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "redacted.png"
    Image.new("RGB", (20, 20), "white").save(source)

    redact_image(source, output, boxes=[(2, 3, 10, 12)])

    with Image.open(output) as image:
        assert image.getpixel((3, 4)) == (245, 245, 245)
        assert image.getpixel((15, 15)) == (255, 255, 255)
