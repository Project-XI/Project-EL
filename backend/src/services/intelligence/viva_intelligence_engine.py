from typing import List, Dict, Any
from ...models.context import VivaTarget, InconsistencyFlag, EvidenceModel

class VivaIntelligenceEngine:
    """
    Generates questioning targets and detects implementation inconsistencies.
    """
    
    @staticmethod
    def generate_targets(detections: Dict[str, Any], arch: EvidenceModel) -> List[VivaTarget]:
        targets = []
        
        # 1. Architecture specific targets
        if "REST" in arch.value:
            targets.append(VivaTarget(
                topic="Architecture",
                question_target="REST vs GraphQL",
                difficulty="medium",
                importance_score=0.8,
                focus="Why REST was preferred over GraphQL for this project."
            ))

        # 2. Tech specific targets
        for key, model in detections.items():
            if model.value == "FastAPI":
                targets.append(VivaTarget(
                    topic="Backend",
                    question_target="Async performance",
                    difficulty="hard",
                    importance_score=0.9,
                    focus="How FastAPI handles concurrent requests compared to Flask."
                ))
            if "JWT" in str(model.value):
                targets.append(VivaTarget(
                    topic="Security",
                    question_target="Token revocation",
                    difficulty="hard",
                    importance_score=0.85,
                    focus="How the system handles token invalidation or logout."
                ))
                
        return targets

    @staticmethod
    def detect_inconsistencies(doc_text: str, detections: Dict[str, Any]) -> List[InconsistencyFlag]:
        flags = []
        
        # 1. Redis Check
        if "redis" in doc_text.lower() and not any("redis" in str(m.value).lower() for m in detections.values()):
            flags.append(InconsistencyFlag(
                issue="Redis mentioned in documentation but absent in repository",
                severity="medium",
                confidence=0.85,
                evidence=["'Redis' keyword found in project report", "No Redis dependency or config found in repo."]
            ))
            
        # 2. Microservices Check
        if "microservices" in doc_text.lower():
            # Check if it looks like a monolith (simple check: only one backend framework detected)
            backend_count = sum(1 for k in detections if "backend" in k and detections[k].value != "Unknown")
            if backend_count <= 1:
                flags.append(InconsistencyFlag(
                    issue="Microservices architecture claimed but monolithic structure detected",
                    severity="high",
                    confidence=0.75,
                    evidence=["'Microservices' mentioned in documentation", "Only a single backend service framework detected."]
                ))
                
        return flags

    @staticmethod
    def detect_complexity_mismatch(arch: EvidenceModel, detections: Dict[str, Any]) -> EvidenceModel:
        # Simple mismatch: High claims vs low implementation
        if "Microservices" in arch.value and sum(1 for k in detections if detections[k].value != "Unknown") < 3:
            return EvidenceModel(
                value="High Complexity Claim vs Minimal Implementation",
                confidence=0.7,
                evidence=["Complex architecture pattern claimed", "Very few actual technology components detected."]
            )
        return EvidenceModel(value="No major mismatch detected", confidence=1.0, evidence=[])
