from PIL import Image, ImageDraw

from lunartech_doc_ai.visual import detect_form_lines


def test_detect_form_lines_finds_long_horizontal_and_vertical_lines(tmp_path):
    image_path = tmp_path / "form.png"
    image = Image.new("RGB", (120, 90), "white")
    draw = ImageDraw.Draw(image)
    draw.line((10, 20, 110, 20), fill="black", width=2)
    draw.line((30, 10, 30, 80), fill="black", width=2)
    image.save(image_path)

    lines = detect_form_lines(image_path, min_length=50)

    orientations = {line["orientation"] for line in lines}
    assert "horizontal" in orientations
    assert "vertical" in orientations
