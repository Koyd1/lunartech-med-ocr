from lunartech_doc_ai.ocr import choose_ocr_languages
from lunartech_doc_ai.ocr import parse_tesseract_tsv


def test_choose_ocr_languages_prefers_multilingual_medical_set():
    assert choose_ocr_languages({"eng", "ron", "rus", "osd"}) == "eng+ron+rus"


def test_choose_ocr_languages_falls_back_to_english():
    assert choose_ocr_languages({"eng", "osd"}) == "eng"


def test_parse_tesseract_tsv_skips_malformed_tab_like_text():
    tsv = (
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
        "5\t1\t1\t1\t1\t1\t10\t10\t20\t10\t90\tValid\n"
        "5\t1\t1\t1\t1\t2\t20\t10\t2\t2\t25\t5\t1\t34\t1\t1\t2\t479\t215\t143\t41\t60\tReceptionarea\n"
    )

    words = parse_tesseract_tsv(tsv)

    assert [word.text for word in words] == ["Valid"]
