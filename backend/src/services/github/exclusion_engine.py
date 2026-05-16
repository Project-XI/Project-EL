import os

class ExclusionEngine:
    """
    Filters out noise files and directories (like node_modules, .git)
    from the repository analysis pipeline.
    """
    
    EXCLUDED_DIRS = {
        "node_modules", ".git", "__pycache__", "venv", ".venv", 
        "dist", "build", "coverage", ".next"
    }
    
    EXCLUDED_EXTS = {
        ".pyc", ".log", ".DS_Store", ".sqlite3", ".pyo", 
        ".pyd", ".so", ".dll", ".class"
    }

    @classmethod
    def is_excluded(cls, path: str) -> bool:
        basename = os.path.basename(path)
        
        # Check if it's an excluded directory/file exactly
        if basename in cls.EXCLUDED_DIRS:
            return True
            
        # Check extensions
        for ext in cls.EXCLUDED_EXTS:
            if path.endswith(ext):
                return True
                
        return False
