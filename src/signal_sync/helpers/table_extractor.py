"""
Table Extractor Helper Module.

Provides functionality to extract tables from PDF documents
using pdfplumber's built-in table extraction capabilities.
"""

import pdfplumber
from typing import List, Dict, Optional
import json


def extract_tables_impl(pdf_path: str, pdf_name: str) -> List[Dict]:
    """
    Extracts tables from each page using pdfplumber's
    built-in table extraction.
    
    Args:
        pdf_path: Absolute path to the PDF file
        pdf_name: Name identifier for the PDF
        
    Returns:
        List of dictionaries containing:
            - pdf_name: Name of the PDF
            - page_no: Page number (1-indexed)
            - table_id: Unique identifier for the table
            - headers: List of column headers
            - rows: List of row data
    """
    tables_data = []
    table_id_counter = 1

    try:
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
    except Exception as e:
        tables_data.append({
            "pdf_name": pdf_name,
            "page_no": 0,
            "table_id": "error",
            "headers": ["Error"],
            "rows": [[str(e)]]
        })

    return tables_data


def format_table_as_text(table_data: Dict) -> str:
    """
    Format a single table as readable text.
    
    Args:
        table_data: Dictionary containing headers and rows
        
    Returns:
        Formatted string representation of the table
    """
    headers = table_data.get("headers", [])
    rows = table_data.get("rows", [])
    
    if not headers:
        return "Empty table"
    
    # Clean None values
    headers = [str(h) if h else "" for h in headers]
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cell_str = str(cell) if cell else ""
                col_widths[i] = max(col_widths[i], len(cell_str))
    
    # Build table string
    lines = []
    
    # Header row
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-" * len(header_line))
    
    # Data rows
    for row in rows:
        row_cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell else ""
            if i < len(col_widths):
                row_cells.append(cell_str.ljust(col_widths[i]))
        lines.append(" | ".join(row_cells))
    
    return "\n".join(lines)


def format_all_tables(tables_data: List[Dict]) -> str:
    """
    Format all extracted tables as a readable text document.
    
    Args:
        tables_data: List of table dictionaries
        
    Returns:
        Formatted string containing all tables
    """
    if not tables_data:
        return "No tables found in the document."
    
    output_lines = []
    
    for table in tables_data:
        output_lines.append(f"\n=== {table['table_id']} (Page {table['page_no']}) ===\n")
        output_lines.append(format_table_as_text(table))
        output_lines.append("")
    
    return "\n".join(output_lines)


def extract_financial_tables(pdf_path: str, keywords: Optional[List[str]] = None) -> List[Dict]:
    """
    Extract tables that likely contain financial data based on keywords.
    
    Args:
        pdf_path: Absolute path to the PDF file
        keywords: List of keywords to filter tables (default: financial terms)
        
    Returns:
        List of table dictionaries that match the keyword criteria
    """
    if keywords is None:
        keywords = [
            "revenue", "profit", "loss", "income", "expense", "balance",
            "cash", "asset", "liability", "equity", "dividend", "eps",
            "margin", "ratio", "growth", "fiscal", "quarter", "annual",
            "total", "net", "gross", "operating", "financial"
        ]
    
    keywords = [k.lower() for k in keywords]
    
    all_tables = extract_tables_impl(pdf_path, "financial_doc")
    financial_tables = []
    
    for table in all_tables:
        headers = table.get("headers", [])
        table_text = " ".join(str(h).lower() for h in headers if h)
        
        # Check first row of data too
        rows = table.get("rows", [])
        if rows:
            first_row = rows[0]
            table_text += " " + " ".join(str(c).lower() for c in first_row if c)
        
        # Check if any keyword matches
        if any(keyword in table_text for keyword in keywords):
            financial_tables.append(table)
    
    return financial_tables
