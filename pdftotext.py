import pymupdf
from typing import Union

def extract_text_from_pdf(file_path: str = None, file_bytes: bytes = None) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file (either this or file_bytes must be provided)
        file_bytes: PDF file content as bytes (either this or file_path must be provided)
        
    Returns:
        Extracted text as a single string
        
    Raises:
        ValueError: If neither file_path nor file_bytes is provided
        RuntimeError: If PDF reading fails
    """
    if not file_path and not file_bytes:
        raise ValueError("Either file_path or file_bytes must be provided")
    
    try:
        # Open the PDF either from path or bytes
        if file_bytes:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        else:
            doc = pymupdf.open(file_path)
            
        text = ""
        for page in doc:
            text += page.get_text()
        return text
        
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")
    finally:
        if 'doc' in locals():
            doc.close()

# Example usage (for testing)
if __name__ == "__main__":
    # Test with file path
    text_from_file = extract_text_from_pdf(file_path="MODULE5.pdf")
    print(f"Extracted {len(text_from_file)} characters from file path")
    
    # Test with bytes
    with open("MODULE5.pdf", "rb") as f:
        bytes_content = f.read()
    text_from_bytes = extract_text_from_pdf(file_bytes=bytes_content)
    print(f"Extracted {len(text_from_bytes)} characters from bytes")