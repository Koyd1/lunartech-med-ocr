from lunartech_doc_ai.schemas import extract_schema


def test_auto_medical_certificate_schema_extracts_canonical_fields():
    blocks = [
        _block("line_0001", "ADEVERINTA MEDICALA nr. 11747 / 6359", [314, 232, 847, 258]),
        _block("line_0002", "Numele, prenumele", [95, 376, 322, 399]),
        _block("line_0003", "MOROZ ALEXANDR", [474, 376, 729, 394]),
        _block("line_0004", "Număr de identificare", [95, 448, 349, 466]),
        _block("line_0005", "2003500227856", [510, 449, 715, 467]),
        _block("line_0006", "Data nașterii", [96, 522, 242, 544]),
        _block("line_0007", "17.01.2004", [346, 521, 486, 540]),
        _block("line_0008", "АМ, А1, A2, A, В1, В", [349, 800, 611, 822]),
        _block("line_0009", "Cod rest", [108, 923, 204, 940]),
        _block("line_0010", "01.06. Ochelari sau lentile", [351, 924, 689, 943]),
        _block("line_0011", "contact", [736, 926, 831, 943]),
    ]

    schema = extract_schema(blocks, source_filename="Adeverinta Medicala AUTO.png")

    assert schema["subtype"] == "driver_medical_certificate"
    assert schema["fields"]["patient_name"]["value"] == "MOROZ ALEXANDR"
    assert schema["fields"]["idnp"]["value"] == "2003500227856"
    assert schema["fields"]["birth_date"]["value"] == "17.01.2004"
    assert schema["fields"]["categories"]["value"] == "АМ, А1, A2, A, В1, В"
    assert schema["fields"]["restriction_code"]["value"] == "01.06. Ochelari sau lentile contact"


def test_military_certificate_schema_extracts_diagnosis_and_decision():
    blocks = [
        _block("line_0001", "ADEVERINTA nr. 280", [629, 298, 1046, 332]),
        _block("line_0002", "Student CM UTM", [314, 352, 591, 410]),
        _block("line_0003", "Moroz Alexandr Veaceslav", [695, 384, 1110, 413]),
        _block("line_0004", "17.01.2004 a.n.", [312, 456, 540, 484]),
        _block("line_0005", "Sef Catedră Militară UTM.", [320, 530, 727, 559]),
        _block("line_0006", "05", [318, 736, 352, 762]),
        _block("line_0007", "03", [403, 736, 436, 763]),
        _block("line_0008", "2024", [488, 737, 562, 763]),
        _block("line_0009", "Diagnosticul şi decizia comisiei despre legătura cauzală a schilodirii", [423, 779, 1467, 818]),
        _block("line_0010", "(ranirii, contuziei, traumei), maladiei Rinită cronică subatrofică. Miopie OU.", [307, 822, 1465, 863]),
        _block("line_0011", "Apt pentru serviciul militar combatant.", [304, 1289, 892, 1323]),
    ]

    schema = extract_schema(blocks, source_filename="Adeverinta medicala Militara.png")

    assert schema["subtype"] == "military_medical_certificate"
    assert schema["fields"]["patient_name"]["value"] == "Moroz Alexandr Veaceslav"
    assert schema["fields"]["exam_date"]["value"] == "05.03.2024"
    assert "Rinită cronică" in schema["fields"]["diagnosis"]["value"]
    assert schema["fields"]["fitness_decision"]["value"] == "Apt pentru serviciul militar combatant."


def test_lab_report_schema_extracts_patient_and_result_table():
    blocks = [
        _block("line_0001", "DE LABORATOR", [609, 234, 922, 255]),
        _block("line_0002", "Nume", [83, 372, 141, 388]),
        _block("line_0003", "Moroz", [202, 372, 266, 388]),
        _block("line_0004", "Prenume", [83, 407, 167, 424]),
        _block("line_0005", "Alexandr", [200, 407, 287, 424]),
        _block("line_0006", "Data nasterii", [456, 372, 577, 393]),
        _block("line_0007", "17.01.2004 (20 ani}", [795, 372, 978, 392]),
        _block("line_0008", "CNP", [82, 477, 123, 494]),
        _block("line_0009", "2003500227856", [200, 477, 353, 494]),
        _block("line_0010", "Chlamydia trachomatis, ADN", [92, 809, 372, 831]),
        _block("line_0011", "NEGATIV", [931, 809, 1019, 826]),
        _block("line_0012", "NEGATIV", [1129, 809, 1216, 826]),
    ]

    schema = extract_schema(blocks, source_filename="Investigatii_biologie_moleculara.pdf")

    assert schema["subtype"] == "molecular_lab_report"
    assert schema["fields"]["patient_name"]["value"] == "Moroz Alexandr"
    assert schema["fields"]["idnp"]["value"] == "2003500227856"
    assert schema["fields"]["birth_date"]["value"] == "17.01.2004 (20 ani)"
    assert schema["tables"][0]["rows"][0]["test_name"] == "Chlamydia trachomatis, ADN"
    assert schema["tables"][0]["rows"][0]["result"] == "NEGATIV"


def test_lab_report_schema_ignores_explanatory_negativ_pozitiv_rows():
    blocks = [
        _block("line_0001", "DE LABORATOR", [609, 234, 922, 255]),
        _block("line_0002", "NEGATIV - în eşantion nu au fost detectate secvenţe de ADN specifice.", [92, 1289, 699, 1317]),
        _block("line_0003", "POZITIV - în eşantion au fost detectate secvenţe de ADN specifice", [92, 1315, 661, 1334]),
    ]

    schema = extract_schema(blocks, source_filename="Investigatii_biologie_moleculara.pdf")

    assert schema["tables"] == []


def _block(block_id: str, text: str, bbox: list[int], confidence: float = 90.0) -> dict:
    return {
        "id": block_id,
        "type": "paragraph",
        "text": text,
        "bbox": bbox,
        "confidence": confidence,
    }
