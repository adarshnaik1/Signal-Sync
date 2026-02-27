"""
Text Extractor Helper Module.

Provides functionality to extract page-wise text from PDF documents
using pdfplumber for deterministic and reproducible extraction.
"""

import pdfplumber
from typing import List, Dict, Optional


def extract_text_sections_impl(pdf_path: str, pdf_name: str) -> List[Dict]:
    """
    Extracts page-wise text from a PDF using pdfplumber.
    Deterministic and reproducible.
    
    Args:
        pdf_path: Absolute path to the PDF file
        pdf_name: Name identifier for the PDF
        
    Returns:
        List of dictionaries containing:
            - pdf_name: Name of the PDF
            - page_no: Page number (1-indexed)
            - text: Extracted text content
            - char_count: Number of characters in the text
    """
    extracted = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_no, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""

                extracted.append({
                    "pdf_name": pdf_name,
                    "page_no": page_no,
                    "text": text.strip(),
                    "char_count": len(text),
                })
    except Exception as e:
        extracted.append({
            "pdf_name": pdf_name,
            "page_no": 0,
            "text": f"Error extracting text: {str(e)}",
            "char_count": 0,
        })

    return extracted


def get_full_text(pdf_path: str) -> str:
    """
    Extract all text from a PDF as a single string.
    
    Args:
        pdf_path: Absolute path to the PDF file
        
    Returns:
        Complete text content from all pages
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text.append(text.strip())
            return "\n\n".join(all_text)
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def extract_text_from_pages(pdf_path: str, start_page: int = 1, end_page: Optional[int] = None) -> str:
    """
    Extract text from specific page range.
    
    Args:
        pdf_path: Absolute path to the PDF file
        start_page: Starting page number (1-indexed)
        end_page: Ending page number (inclusive, defaults to last page)
        
    Returns:
        Text content from the specified page range
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            # Validate page range
            start_page = max(1, start_page)
            end_page = end_page or total_pages
            end_page = min(end_page, total_pages)
            
            all_text = []
            for page_no in range(start_page - 1, end_page):
                page = pdf.pages[page_no]
                text = page.extract_text()
                if text:
                    all_text.append(f"--- Page {page_no + 1} ---\n{text.strip()}")
            return "\n\n".join(all_text)
    except Exception as e:
        return f"Error extracting text: {str(e)}"
