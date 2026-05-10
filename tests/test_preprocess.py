from PIL import Image

from lunartech_doc_ai.preprocess import prepare_degraded_ocr_image, prepare_ocr_image


def test_prepare_ocr_image_upscales_small_pages(tmp_path):
    source = tmp_path / "small.png"
    target = tmp_path / "prepared.png"
    Image.new("RGB", (595, 842), "white").save(source)

    result = prepare_ocr_image(source, target, min_width=1400)

    assert result == target
    with Image.open(target) as image:
        assert image.width >= 1400
        assert image.height > 842


def test_prepare_degraded_ocr_image_upscales_before_enhancement(tmp_path):
    source = tmp_path / "faint.png"
    target = tmp_path / "degraded.png"
    image = Image.new("RGB", (700, 900), "white")
    for x in range(180, 520):
        for y in range(260, 290):
            image.putpixel((x, y), (170, 170, 170))
    image.save(source)

    result = prepare_degraded_ocr_image(source, target, min_width=1400)

    assert result == target
    with Image.open(target) as prepared:
        assert prepared.width >= 1400
        assert prepared.mode == "RGB"
        assert prepared.getbbox() is not None
