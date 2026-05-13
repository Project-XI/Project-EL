import os
from typing import List, Dict, Any

class StructureAnalyzer:
    """
    Analyzes the repository structure, prioritizing important files and ignoring noise.
    """
    
    HIGH_PRIORITY_FILES = {
        "README.md", "package.json", "requirements.txt", 
        "pyproject.toml", "docker-compose.yml", ".env.example"
    }
    
    IGNORE_DIRS = {
        "node_modules", "build", "dist", "assets", 
        "coverage", ".git", "__pycache__", ".venv"
    }
    
    @classmethod
    def analyze(cls, repo_path: str) -> Dict[str, Any]:
        structure = {
            "high_priority": [],
            "directories": [],
            "file_tree": {}
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]
            
            rel_path = os.path.relpath(root, repo_path)
            if rel_path == ".":
                rel_path = ""
            
            structure["directories"].append(rel_path)
            
            for file in files:
                file_rel_path = os.path.join(rel_path, file)
                if file in cls.HIGH_PRIORITY_FILES:
                    structure["high_priority"].append(file_rel_path)
                
                # Build basic tree
                structure["file_tree"][file_rel_path] = {
                    "name": file,
                    "priority": "HIGH" if file in cls.HIGH_PRIORITY_FILES else "NORMAL"
                }
                
        return structure
