import os
from typing import List

class ExclusionEngine:
    """
    Handles directory and file exclusions for efficient large-scale repository analysis.
    """
    DEFAULT_EXCLUSIONS = [
        "node_modules", ".git", "__pycache__", "venv", "env", 
        "build", "dist", "target", ".next", ".cache", "out"
    ]
    
    DEFAULT_EXTENSIONS = [
        ".exe", ".bin", ".pyc", ".png", ".jpg", ".jpeg", ".gif", 
        ".svg", ".mp4", ".mov", ".zip", ".tar.gz", ".pdf"
    ]

    @classmethod
    def is_excluded(cls, path: str) -> bool:
        parts = path.split(os.sep)
        # Check for excluded directories
        if any(ex in parts for ex in cls.DEFAULT_EXCLUSIONS):
            return True
        
        # Check for excluded extensions
        if any(path.endswith(ext) for ext in cls.DEFAULT_EXTENSIONS):
            return True
            
        return False

    @classmethod
    def filter_structure(cls, structure: List[str]) -> List[str]:
        return [p for p in structure if not cls.is_excluded(p)]
