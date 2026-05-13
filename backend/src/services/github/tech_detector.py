import os
import json
from typing import Dict, Any, List
from ...models.context import EvidenceModel

class TechDetector:
    """
    Detects frameworks and technologies from config files and folder patterns.
    """
    
    @staticmethod
    def detect_from_files(repo_path: str, structure: Dict[str, Any]) -> Dict[str, EvidenceModel]:
        detections = {}
        
        # Helper to find file by name in the entire tree
        def find_file(filename: str) -> Optional[str]:
            for rel_path in structure.get("file_tree", {}):
                if os.path.basename(rel_path) == filename:
                    return os.path.join(repo_path, rel_path)
            return None

        # 1. Node.js / React / etc.
        package_json_path = find_file("package.json")
        if package_json_path:
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "react" in deps:
                        detections["frontend_framework"] = EvidenceModel(
                            value="React",
                            confidence=0.98,
                            evidence=[f"'react' found in {os.path.relpath(package_json_path, repo_path)}"]
                        )
                    if "express" in deps:
                        detections["backend_framework"] = EvidenceModel(
                            value="Express",
                            confidence=0.98,
                            evidence=[f"'express' found in {os.path.relpath(package_json_path, repo_path)}"]
                        )
                    if "mongoose" in deps:
                        detections["database_used"] = EvidenceModel(
                            value="MongoDB",
                            confidence=0.95,
                            evidence=[f"'mongoose' found in {os.path.relpath(package_json_path, repo_path)}"]
                        )
            except:
                pass

        # 2. Python / FastAPI / etc.
        requirements_path = find_file("requirements.txt")
        if requirements_path:
            with open(requirements_path, 'r') as f:
                content = f.read()
                if "fastapi" in content.lower():
                    detections["backend_framework"] = EvidenceModel(
                        value="FastAPI",
                        confidence=0.98,
                        evidence=[f"'fastapi' found in {os.path.relpath(requirements_path, repo_path)}"]
                    )
                if "sqlalchemy" in content.lower():
                    detections["database_used"] = EvidenceModel(
                        value="SQLAlchemy (Relational)",
                        confidence=0.8,
                        evidence=[f"'sqlalchemy' found in {os.path.relpath(requirements_path, repo_path)}"]
                    )

        # 3. Authentication detection
        for file in structure.get("high_priority", []):
            if file == ".env.example":
                path = os.path.join(repo_path, file)
                with open(path, 'r') as f:
                    content = f.read().lower()
                    if "jwt" in content or "token" in content:
                        detections["authentication_system"] = EvidenceModel(
                            value="JWT / Token-based",
                            confidence=0.7,
                            evidence=["'JWT' or 'TOKEN' found in .env.example"]
                        )

        return detections
