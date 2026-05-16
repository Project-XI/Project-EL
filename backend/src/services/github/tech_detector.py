import os
import json
from typing import Dict, Any, List, Optional
from src.models.context import EvidenceModel

class TechDetector:
    """
    Detects frameworks and technologies from config files and folder patterns.
    """
    
    @staticmethod
    def detect_from_files(repo_path: str, structure: Dict[str, Any]) -> Dict[str, EvidenceModel]:
        detections = {}
        
        # Helper to check if a keyword actually appears in the source code
        def verify_usage(keyword: str) -> bool:
            for rel_path in structure.get("file_tree", {}):
                if rel_path.endswith(".py") or rel_path.endswith(".js") or rel_path.endswith(".ts"):
                    abs_path = os.path.join(repo_path, rel_path)
                    try:
                        with open(abs_path, 'r', errors='ignore') as f:
                            if keyword.lower() in f.read().lower():
                                return True
                    except:
                        continue
            return False

        # 1. Node.js / React / etc.
        package_json_path = TechDetector.find_file(repo_path, structure, "package.json")
        if package_json_path:
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "react" in deps and verify_usage("React"):
                        detections["frontend_framework"] = EvidenceModel(
                            value="React",
                            confidence=0.98,
                            evidence=[f"'react' found and used in {os.path.relpath(package_json_path, repo_path)}"]
                        )
                    if "express" in deps and verify_usage("express"):
                        detections["backend_framework"] = EvidenceModel(
                            value="Express",
                            confidence=0.98,
                            evidence=[f"'express' found and used in {os.path.relpath(package_json_path, repo_path)}"]
                        )
            except:
                pass

        # 2. Python / FastAPI / etc.
        requirements_path = TechDetector.find_file(repo_path, structure, "requirements.txt")
        if requirements_path:
            with open(requirements_path, 'r') as f:
                content = f.read()
                if "fastapi" in content.lower() and verify_usage("FastAPI"):
                    detections["backend_framework"] = EvidenceModel(
                        value="FastAPI",
                        confidence=0.98,
                        evidence=[f"'fastapi' found and used in {os.path.relpath(requirements_path, repo_path)}"]
                    )

        return detections

    @staticmethod
    def find_file(repo_path: str, structure: Dict[str, Any], filename: str) -> Optional[str]:
        for rel_path in structure.get("file_tree", {}):
            if os.path.basename(rel_path) == filename:
                return os.path.join(repo_path, rel_path)
        return None
