from pathlib import Path
from helpers.pdf_extraction.text_extractor import extract_text_sections_impl
from helpers.pdf_extraction.table_extractor import extract_tables_impl


class AnnualReportPDF:
    """
    PDF-level abstraction.
    Delegates extraction logic to helper modules.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_name = Path(pdf_path).name

    def extract_text_sections(self):
        return extract_text_sections_impl(self.pdf_path, self.pdf_name)

    def extract_tables(self):
        return extract_tables_impl(self.pdf_path, self.pdf_name)

    def extract_all(self):
        return {
            "pdf_name": self.pdf_name,
            "text_sections": self.extract_text_sections(),
            "tables": self.extract_tables()
        }
