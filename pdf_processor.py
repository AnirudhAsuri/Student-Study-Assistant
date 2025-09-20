"""
PDF and text file processing utilities
Handles text extraction from various document formats
"""

import io
from pathlib import Path
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using pdfminer.six
    
    Args:
        file_path (str): Path to PDF file
        
    Returns:
        str: Extracted text content
    """
    try:
        # Configure layout analysis parameters for better text extraction
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5
        )
        
        text = extract_text(file_path, laparams=laparams)
        
        # Clean up the extracted text
        cleaned_text = clean_extracted_text(text)
        
        logger.info(f"Successfully extracted {len(cleaned_text)} characters from PDF: {file_path}")
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from text file with encoding detection
    
    Args:
        file_path (str): Path to text file
        
    Returns:
        str: File content as string
    """
    try:
        # Try UTF-8 first, then fall back to other common encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    text = file.read()
                logger.info(f"Successfully read text file with {encoding} encoding: {file_path}")
                return clean_extracted_text(text)
            except UnicodeDecodeError:
                continue
        
        raise Exception("Could not decode text file with any supported encoding")
        
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        raise Exception(f"Failed to read text file: {str(e)}")


def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace while preserving paragraph structure
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove leading/trailing whitespace
        cleaned_line = line.strip()
        
        # Skip empty lines but preserve single empty lines between paragraphs
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
        elif cleaned_lines and cleaned_lines[-1] != "":
            cleaned_lines.append("")
    
    # Join lines back together
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Remove multiple consecutive empty lines
    while '\n\n\n' in cleaned_text:
        cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
    
    # Remove very short lines that are likely artifacts (less than 3 characters)
    lines = cleaned_text.split('\n')
    final_lines = []
    
    for line in lines:
        if len(line.strip()) >= 3 or line.strip() == "":
            final_lines.append(line)
    
    return '\n'.join(final_lines).strip()


def validate_file_content(text: str) -> bool:
    """
    Validate that extracted text contains meaningful content
    
    Args:
        text (str): Extracted text
        
    Returns:
        bool: True if content is valid for processing
    """
    if not text or len(text.strip()) < 50:
        return False
    
    # Check if text contains mostly readable characters
    readable_chars = sum(1 for char in text if char.isalnum() or char.isspace() or char in '.,!?-:;()[]{}')
    total_chars = len(text)
    
    if total_chars == 0:
        return False
    
    readable_ratio = readable_chars / total_chars
    return readable_ratio > 0.8  # At least 80% readable characters


def get_file_info(file_path: str) -> dict:
    """
    Get information about a file
    
    Args:
        file_path (str): Path to file
        
    Returns:
        dict: File information
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return {
        "name": path.name,
        "size": path.stat().st_size,
        "extension": path.suffix.lower(),
        "exists": True
    }