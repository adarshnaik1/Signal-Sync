import json
from helpers.pdf_extraction.annual_report_pdf import AnnualReportPDF
from pathlib import Path

OUTPUT_PATH = Path("outputs/text_extracted.json")
PDF_PATH = r"C:\Users\hedet\Downloads\ITC Limited Annual Report 2024.pdf"  # change as needed


def main():
    pdf = AnnualReportPDF(PDF_PATH)
    extracted_data = pdf.extract_all()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
