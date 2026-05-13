import re
from typing import List, Dict, Any

class TextCleaner:
    """
    Normalizes and cleans extracted text for better entity extraction.
    """
    
    @staticmethod
    def clean(text: str) -> str:
        # 1. Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # 2. Remove page numbers (simple heuristic)
        text = re.sub(r'Page \d+ of \d+', '', text)
        
        # 3. Fix common extraction artifacts (e.g., ligatures)
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        
        return text.strip()

    @staticmethod
    def extract_headings(structured_data: List[Dict[str, Any]]) -> List[str]:
        """
        Extracts identified headings from structured data.
        """
        headings = []
        for item in structured_data:
            if item.get("is_heading") or (item.get("type") == 0 and len(item.get("content", "")) < 100 and item.get("content", "").isupper()):
                headings.append(item["content"].strip())
        return headings
