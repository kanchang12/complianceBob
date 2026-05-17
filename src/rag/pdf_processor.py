"""
PDF Processor Module
Extracts text from PDF compliance documents
"""

import PyPDF2
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF text extraction for compliance documents"""
    
    def __init__(self):
        """Initialize PDF processor"""
        self.supported_formats = ['.pdf']
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                logger.info(f"Processing {num_pages} pages from {pdf_path}")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise
    
    def extract_text_by_pages(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF with page information
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries with page number and text
        """
        try:
            pages_data = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    pages_data.append({
                        'page_number': page_num + 1,
                        'text': text.strip(),
                        'source': pdf_path
                    })
            
            return pages_data
        
        except Exception as e:
            logger.error(f"Error extracting pages from {pdf_path}: {str(e)}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for embedding
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Number of overlapping characters between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        
        return chunks

# Made with Bob
