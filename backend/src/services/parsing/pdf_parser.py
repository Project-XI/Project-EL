import fitz # PyMuPDF
from typing import List, Dict, Any

class PDFParser:
    """
    Service for extracting raw text and metadata from PDF files.
    """
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        text = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
            return ""

    @staticmethod
    def extract_with_structure(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text while attempting to identify blocks and basic structure.
        """
        blocks = []
        try:
            with fitz.open(file_path) as doc:
                for page_num, page in enumerate(doc):
                    page_blocks = page.get_text("blocks")
                    for b in page_blocks:
                        blocks.append({
                            "page": page_num + 1,
                            "content": b[4],
                            "type": b[6], # 0 for text, 1 for image
                            "bbox": (b[0], b[1], b[2], b[3])
                        })
            return blocks
        except Exception as e:
            print(f"Error parsing structured PDF {file_path}: {e}")
            return []
