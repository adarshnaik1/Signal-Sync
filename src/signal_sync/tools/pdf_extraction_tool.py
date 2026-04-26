"""
PDF Extraction Tools for CrewAI Agents.

These tools enable agents to extract and analyze content from PDF documents,
particularly useful for processing annual reports and financial documents.
"""

from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import os
import json

from signal_sync.helpers.text_extractor import (
    extract_text_sections_impl,
    get_full_text,
    extract_text_from_pages
)
from signal_sync.helpers.table_extractor import (
    extract_tables_impl,
    format_all_tables,
    format_table_as_text,
    extract_financial_tables
)


class PDFTextExtractInput(BaseModel):
    """Input schema for PDF Text Extraction Tool."""
    pdf_path: str = Field(..., description="Absolute path to the PDF file")
    start_page: Optional[int] = Field(
        default=None,
        description="Starting page number (1-indexed). If not provided, extracts from page 1."
    )
    end_page: Optional[int] = Field(
        default=None,
        description="Ending page number (1-indexed). If not provided, extracts to the last page."
    )


class PDFTextExtractTool(BaseTool):
    """
    Tool for extracting text content from PDF documents.
    
    Use this tool to read and analyze text content from annual reports,
    financial statements, or any PDF document.
    """
    name: str = "pdf_text_extractor"
    description: str = (
        "Extracts text content from a PDF document. Can extract from specific page ranges "
        "or the entire document. Use this to read annual reports, financial statements, "
        "and other PDF documents for analysis."
    )
    args_schema: Type[BaseModel] = PDFTextExtractInput
    
    def _run(self, pdf_path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> str:
        """Execute the text extraction."""
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at path: {pdf_path}"
        
        try:
            if start_page or end_page:
                return extract_text_from_pages(
                    pdf_path,
                    start_page=start_page or 1,
                    end_page=end_page
                )
            else:
                return get_full_text(pdf_path)
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"


class PDFTableExtractInput(BaseModel):
    """Input schema for PDF Table Extraction Tool."""
    pdf_path: str = Field(..., description="Absolute path to the PDF file")
    financial_only: bool = Field(
        default=False,
        description="If True, only extract tables that appear to contain financial data"
    )


class PDFTableExtractTool(BaseTool):
    """
    Tool for extracting tables from PDF documents.
    
    Use this tool to extract tabular data from annual reports and financial documents.
    Tables are formatted as readable text for analysis.
    """
    name: str = "pdf_table_extractor"
    description: str = (
        "Extracts tables from a PDF document. Can filter to only financial tables. "
        "Returns formatted tables that can be analyzed for financial data, "
        "balance sheets, income statements, and other structured information."
    )
    args_schema: Type[BaseModel] = PDFTableExtractInput
    
    def _run(self, pdf_path: str, financial_only: bool = False) -> str:
        """Execute the table extraction."""
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at path: {pdf_path}"
        
        try:
            pdf_name = os.path.basename(pdf_path)
            
            if financial_only:
                tables = extract_financial_tables(pdf_path)
            else:
                tables = extract_tables_impl(pdf_path, pdf_name)
            
            if not tables:
                return "No tables found in the PDF document."
            
            return format_all_tables(tables)
        except Exception as e:
            return f"Error extracting tables from PDF: {str(e)}"


class PDFFullAnalysisInput(BaseModel):
    """Input schema for PDF Full Analysis Tool."""
    pdf_path: str = Field(..., description="Absolute path to the PDF file")


class PDFFullAnalysisTool(BaseTool):
    """
    Tool for comprehensive PDF analysis.
    
    Extracts both text and tables, providing a structured summary
    suitable for agent decision-making.
    """
    name: str = "pdf_full_analysis"
    description: str = (
        "Performs comprehensive analysis of a PDF document, extracting both text "
        "and tables. Returns a structured summary including document statistics, "
        "extracted content, and financial tables when found. Best used for initial "
        "document overview and understanding."
    )
    args_schema: Type[BaseModel] = PDFFullAnalysisInput
    
    def _run(self, pdf_path: str) -> str:
        """Execute full PDF analysis."""
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at path: {pdf_path}"
        
        try:
            pdf_name = os.path.basename(pdf_path)
            
            # Extract text sections for overview
            text_sections = extract_text_sections_impl(pdf_path, pdf_name)
            
            # Extract all tables
            all_tables = extract_tables_impl(pdf_path, pdf_name)
            
            # Extract financial tables separately
            financial_tables = extract_financial_tables(pdf_path)
            
            # Build comprehensive summary
            summary_parts = []
            
            # Document statistics
            total_pages = len(text_sections)
            total_chars = sum(s.get("char_count", 0) for s in text_sections)
            total_tables = len(all_tables)
            financial_table_count = len(financial_tables)
            
            summary_parts.append("=" * 60)
            summary_parts.append(f"PDF ANALYSIS SUMMARY: {pdf_name}")
            summary_parts.append("=" * 60)
            summary_parts.append(f"\nDocument Statistics:")
            summary_parts.append(f"  - Total Pages: {total_pages}")
            summary_parts.append(f"  - Total Characters: {total_chars:,}")
            summary_parts.append(f"  - Total Tables Found: {total_tables}")
            summary_parts.append(f"  - Financial Tables: {financial_table_count}")
            
            # First few pages text (executive summary area)
            summary_parts.append("\n" + "=" * 60)
            summary_parts.append("DOCUMENT TEXT (First 3 Pages)")
            summary_parts.append("=" * 60)
            
            for section in text_sections[:3]:
                page_no = section.get("page_no", 0)
                text = section.get("text", "")
                # Truncate very long pages
                if len(text) > 3000:
                    text = text[:3000] + "\n... [truncated]"
                summary_parts.append(f"\n--- Page {page_no} ---\n{text}")
            
            # Financial tables
            if financial_tables:
                summary_parts.append("\n" + "=" * 60)
                summary_parts.append("FINANCIAL TABLES")
                summary_parts.append("=" * 60)
                summary_parts.append(format_all_tables(financial_tables[:5]))  # Limit to first 5
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            return f"Error analyzing PDF: {str(e)}"


class PDFSearchInput(BaseModel):
    """Input schema for PDF Search Tool."""
    pdf_path: str = Field(..., description="Absolute path to the PDF file")
    search_term: str = Field(..., description="Term or phrase to search for in the document")


class PDFSearchTool(BaseTool):
    """
    Tool for searching within PDF documents.
    
    Searches for specific terms and returns relevant context from the document.
    """
    name: str = "pdf_search"
    description: str = (
        "Searches for a specific term or phrase in a PDF document and returns "
        "relevant excerpts with context. Use this to find specific information "
        "like company names, financial terms, dates, or key phrases."
    )
    args_schema: Type[BaseModel] = PDFSearchInput
    
    def _run(self, pdf_path: str, search_term: str) -> str:
        """Execute the search."""
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at path: {pdf_path}"
        
        try:
            pdf_name = os.path.basename(pdf_path)
            text_sections = extract_text_sections_impl(pdf_path, pdf_name)
            
            search_term_lower = search_term.lower()
            results = []
            
            for section in text_sections:
                text = section.get("text", "")
                page_no = section.get("page_no", 0)
                
                if search_term_lower in text.lower():
                    # Find all occurrences and extract context
                    text_lower = text.lower()
                    pos = 0
                    while True:
                        pos = text_lower.find(search_term_lower, pos)
                        if pos == -1:
                            break
                        
                        # Extract context around the match
                        start = max(0, pos - 150)
                        end = min(len(text), pos + len(search_term) + 150)
                        context = text[start:end]
                        
                        # Add ellipsis if truncated
                        if start > 0:
                            context = "..." + context
                        if end < len(text):
                            context = context + "..."
                        
                        results.append(f"Page {page_no}: {context}")
                        pos += 1
            
            if not results:
                return f"No matches found for '{search_term}' in the document."
            
            output = [f"Found {len(results)} matches for '{search_term}':\n"]
            output.extend(results[:10])  # Limit to first 10 results
            
            if len(results) > 10:
                output.append(f"\n... and {len(results) - 10} more matches")
            
            return "\n\n".join(output)
            
        except Exception as e:
            return f"Error searching PDF: {str(e)}"


# Convenience function to create all PDF tools with a pre-configured path
def create_pdf_tools(pdf_path: Optional[str] = None):
    """
    Create instances of all PDF extraction tools.
    
    Args:
        pdf_path: Optional default PDF path to configure tools with
        
    Returns:
        List of tool instances
    """
    return [
        PDFTextExtractTool(),
        PDFTableExtractTool(),
        PDFFullAnalysisTool(),
        PDFSearchTool()
    ]
