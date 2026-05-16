from typing import List, Dict, Any
from ...models.context import VivaTarget, InconsistencyFlag, EvidenceModel

class VivaIntelligenceEngine:
    """
    Generates questioning targets and detects implementation inconsistencies.
    """
    
    @staticmethod
    def generate_targets(detections: Dict[str, Any], arch: EvidenceModel) -> List[VivaTarget]:
        targets = []
        
        # 1. Tradeoff-based targets (Why X over Y?)
        if "REST" in arch.value:
            targets.append(VivaTarget(
                topic="Architecture",
                question_target="Tradeoff: REST vs GraphQL",
                difficulty="medium",
                importance_score=0.8,
                focus="Given the data complexity, why was REST's fixed endpoint structure chosen over GraphQL's flexibility?"
            ))

        # 2. Tech-pair Reasoning (FastAPI + JWT example)
        has_fastapi = any(m.value == "FastAPI" for m in detections.values())
        has_jwt = any("JWT" in str(m.value) for m in detections.values())
        
        if has_fastapi and has_jwt:
            targets.append(VivaTarget(
                topic="Security",
                question_target="Implementation: JWT Middleware Lifecycle",
                difficulty="hard",
                importance_score=0.95,
                focus="What happens if the JWT verification fails inside the FastAPI middleware chain? Is the failure path gracefully handled before reaching the business logic?"
            ))

        # 3. Scalability Reasoning
        if any("SQL" in str(m.value) for m in detections.values()):
            targets.append(VivaTarget(
                topic="Database",
                question_target="Scaling: Vertical vs Horizontal",
                difficulty="medium",
                importance_score=0.75,
                focus="If the request load triples, what is the primary bottleneck for your relational database implementation?"
            ))

        from src.services.intelligence.viva_question_ranker import VivaQuestionRanker
        return VivaQuestionRanker.rank_targets(targets)

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
