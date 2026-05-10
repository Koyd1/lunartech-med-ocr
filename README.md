# LunarTech Medical Document Reconstruction

Baseline system for the scanned medical document reconstruction assignment.

The pipeline takes scanned medical documents, extracts OCR words and layout boxes, produces a structured JSON representation, and creates a clean HTML/PDF reconstruction that preserves the original page geometry as closely as the baseline allows.

## Current Scope

Supported inputs:

- PNG, JPG, JPEG, TIFF, WEBP
- PDF first page on macOS via `sips`

Generated outputs:

- `output/json/*.json` - structured extraction
- `output/html/*.html` - visually reconstructed document
- `output/pdf/*.pdf` - PDF export rendered from reconstructed HTML when Chrome is available
- `output/tmp/pages/*.png` - intermediate PDF page renders

The current checked outputs are generated under `output/private/` when using the command below.

## Setup

Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Install Tesseract OCR:

```bash
brew install tesseract
brew install tesseract-lang
```

The pipeline automatically uses `eng+ron+rus` when those Tesseract language packs are available, and falls back to `eng` otherwise.

For HTML-to-PDF export, install Google Chrome or set `CHROME_PATH` to a compatible Chromium executable. On macOS the default path `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` is detected automatically.

## Run

Process private source documents:

```bash
python3 run.py --input test-img --output output
```

Process one file:

```bash
python3 run.py --input "test-img/Adeverinta Medicala AUTO.png" --output output/private
```

Process the PDF first page:

```bash
python3 run.py --input "test-img/Moroz_Alexandr_Investigatii_biologie_moleculara_18_03_2024_15_25.pdf" --output output/private
```

## Test

```bash
pytest -q
```

## Pipeline

1. Read image or render the first PDF page to PNG.
2. Preprocess the working image with grayscale conversion, autocontrast, sharpening, and upscaling for low-resolution pages.
3. For weak OCR candidates, try a degraded-scan fallback that upscales before enhancement, then select the candidate using confidence, word count, subtype, fields, and table rows.
4. Run Tesseract TSV OCR to get words, coordinates, and confidence scores.
5. Group OCR words into line-level text blocks.
6. Classify blocks as headings, field lines, dates, markers, or paragraphs.
7. Extract field-value candidates using conservative label heuristics plus same-line geometry for values placed to the right of labels.
8. Extract semantic sections and note/uncertainty blocks for the structured JSON.
9. Run schema-specific extractors for known document types:
   - driver medical certificate
   - military medical certificate
   - molecular lab report
10. Detect long horizontal/vertical form lines as visual elements.
11. Save structured JSON with source metadata, layout boxes, generic fields, `schema_fields`, `sections`, `tables`, `notes`, visual elements, OCR language, and confidence data.
12. Render HTML with absolute positioning, detected field boxes, detected form lines, and the original source image as the visual underlay. Low-confidence OCR noise is hidden in the visual layer so barcodes and degraded scans remain readable.
13. Export HTML to PDF through headless Chrome when available.

## Current Sample Status

The current `test-img/` sample set produces:

- driver medical certificate: structured fields, HTML, and PDF
- military medical certificate: structured fields, HTML, and PDF
- molecular lab report PDF first page: structured fields, 12-row result table, HTML, and PDF
- degraded lab report level 1: structured fields, 12-row result table, HTML, and PDF
- degraded lab report level 2: degraded OCR fallback, 11-row result table, original-scan visual reconstruction, HTML, and PDF

## Uncertainty Handling

- Every OCR word/block carries confidence, and the JSON includes `mean_confidence`, `low_confidence_blocks`, selected OCR candidate, preprocessing mode, and candidate scores.
- Low-confidence visual overlays are suppressed in HTML/PDF to avoid making noisy scans less readable.
- Degraded scans may use a different OCR image for extraction while preserving the original image for visual reconstruction.
- Ambiguous fields are left absent instead of being filled with guessed values.

## Submission Notes

The assignment materials and generated outputs are confidential. Keep submissions private and do not publish the repository, sample scans, or outputs publicly.

Recommended private submission contents:

- source code in `lunartech_doc_ai/`
- `run.py`, `requirements.txt`, `pytest.ini`, `README.md`, and `instructions.md`
- tests in `tests/`
- generated JSON/HTML/PDF outputs from `output/private/`

Do not include unrelated local artifacts such as `.venv/`, `.pytest_cache/`, `tmp/`, `.DS_Store`, or `synthetic_prescription_dataset/`. The synthetic prescription dataset is not used by this solution and is ignored by `.gitignore`.

## Hugging Face Notes

The baseline is intentionally local and reproducible. Hugging Face model search and docs suggest useful next steps:

- `microsoft/trocr-base-printed` and `microsoft/trocr-base-handwritten` are practical OCR model candidates for cropped printed/handwritten text regions.
- Transformers document-question-answering pipelines support document images with word boxes; for LayoutLM-style models, the processor can use Tesseract OCR boxes.
- Donut-style document models are an OCR-free direction for structured extraction, but they are heavier and should be added after the deterministic baseline is stable.

## GitHub Notes

This directory is not currently a git repository. If publishing work for review:

- initialize a private repository only;
- keep `test-img/` and raw/generated sensitive outputs out of public remotes;
- commit source code, tests, README, and redacted/sample-safe outputs only.

## Limitations

- OCR quality is limited by installed Tesseract language data and scan quality.
- PDF input support currently renders only the first page.
- HTML-to-PDF export requires Chrome/Chromium.
- Layout reconstruction is still mostly line-based, not full table-grid aware yet.
- Checkbox detection is not implemented because the current evaluated samples do not require it.
- Field extraction combines generic heuristics with schema-specific extractors for the current sample types. Wider document coverage still needs more schemas or a learned/classifier layer.

## Strong Next Improvements

- Add optional Hugging Face TrOCR inference for low-confidence cropped regions.
- Add uncertainty annotations per field and per section.
- Improve table-grid reconstruction beyond long-line detection.
- Add more schema-specific extractors for intake forms, prescriptions, and clinical summaries.
- Add a document-type classifier and schema-specific extractors.
