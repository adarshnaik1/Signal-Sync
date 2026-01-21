import pdfplumber
from typing import List, Dict


def extract_tables_impl(pdf_path: str, pdf_name: str) -> List[Dict]:
    """
    Extracts tables from each page using pdfplumber's
    built-in table extraction.
    """
    tables_data = []
    table_id_counter = 1

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            if not tables:
                continue

            for table in tables:
                if not table or len(table) < 1:
                    continue

                headers = table[0]
                rows = table[1:]

                tables_data.append({
                    "pdf_name": pdf_name,
                    "page_no": page_no,
                    "table_id": f"table_{table_id_counter}",
                    "headers": headers,
                    "rows": rows
                })

                table_id_counter += 1

    return tables_data
