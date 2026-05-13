import os
from typing import Dict, Any, List

class FileSummarizer:
    """
    Generates lightweight summaries for important files to help infer architecture.
    """
    
    FILE_HINTS = {
        "auth": "Handles user authentication and authorization logic.",
        "db": "Database connection and configuration.",
        "route": "Defines API endpoints and request handling.",
        "model": "Data structure and schema definitions.",
        "service": "Core business logic and external integrations.",
        "controller": "Request/Response orchestration logic."
    }
    
    @classmethod
    def summarize_structure(cls, structure: Dict[str, Any]) -> List[Dict[str, str]]:
        summaries = []
        for file_path, info in structure.get("file_tree", {}).items():
            name = info["name"].lower()
            for hint, description in cls.FILE_HINTS.items():
                if hint in name:
                    summaries.append({
                        "file": file_path,
                        "summary": description
                    })
                    break
        return summaries
