import pdfplumber
from typing import List, Dict


def extract_text_sections_impl(pdf_path: str, pdf_name: str) -> List[Dict]:
    """
    Extracts page-wise text from a PDF using pdfplumber.
    Deterministic and reproducible.
    """
    extracted = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            extracted.append({
                "pdf_name": pdf_name,
                "page_no": page_no,
                "text": text.strip(),
                # Optional metadata for downstream use
                "char_count": len(text),
            })

    return extracted
