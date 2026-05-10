from pathlib import Path

from lunartech_doc_ai.pdf_export import render_pdf_from_html


def test_render_pdf_from_html_uses_chrome_and_writes_pdf(tmp_path, monkeypatch):
    html_path = tmp_path / "doc.html"
    pdf_path = tmp_path / "doc.pdf"
    html_path.write_text("<html><body>ok</body></html>", encoding="utf-8")
    calls = []

    def fake_find_chrome():
        return Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

    def fake_run(command, check, capture_output, text):
        calls.append(command)
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr("lunartech_doc_ai.pdf_export.find_chrome_executable", fake_find_chrome)
    monkeypatch.setattr("lunartech_doc_ai.pdf_export.subprocess.run", fake_run)

    assert render_pdf_from_html(html_path, pdf_path) is True
    assert pdf_path.exists()
    assert "--headless=new" in calls[0]
    assert f"--print-to-pdf={pdf_path}" in calls[0]
