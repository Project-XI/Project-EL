from typing import List, Dict, Any
from ...models.context import ImplementationReasoning, EvidenceModel

class ReasoningInferenceEngine:
    """
    Infers probable engineering tradeoffs and design intents.
    """
    
    TECH_REASONING = {
        "MongoDB": [
            "Flexible schema allows for fast iteration during development.",
            "Handling of semi-structured or dynamic data types.",
            "Scalability through horizontal sharding support."
        ],
        "PostgreSQL": [
            "Strict data integrity and ACID compliance requirements.",
            "Support for complex relational queries and joins.",
            "Mature ecosystem for structured business data."
        ],
        "FastAPI": [
            "High performance requirements for asynchronous I/O operations.",
            "Automatic OpenAPI/Swagger documentation for better developer experience.",
            "Type safety through Pydantic integration."
        ],
        "React": [
            "Component-based UI architecture for reusability.",
            "Efficient DOM updates through Virtual DOM.",
            "Rich ecosystem for complex state management."
        ],
        "JWT / Token-based": [
            "Stateless authentication preferred for horizontal scalability.",
            "Easier cross-domain authentication support.",
            "Reduced server-side session storage overhead."
        ]
    }

    @classmethod
    def infer_reasoning(cls, detections: Dict[str, Any]) -> List[ImplementationReasoning]:
        reasonings = []
        
        for key, model in detections.items():
            tech_name = model.value
            if tech_name in cls.TECH_REASONING:
                reasonings.append(ImplementationReasoning(
                    technology=tech_name,
                    probable_reasoning=cls.TECH_REASONING[tech_name],
                    confidence=0.75,
                    evidence=model.evidence
                ))
                
        return reasonings

    @staticmethod
    def infer_tradeoffs(detections: Dict[str, Any]) -> List[EvidenceModel]:
        tradeoffs = []
        if "MongoDB" in [m.value for m in detections.values()]:
            tradeoffs.append(EvidenceModel(
                value="Schema Flexibility vs Data Consistency",
                confidence=0.8,
                evidence=["MongoDB detected. Traditional relational constraints may be absent."]
            ))
        if "JWT" in str([m.value for m in detections.values()]):
            tradeoffs.append(EvidenceModel(
                value="Statelessness vs Revocation Complexity",
                confidence=0.7,
                evidence=["JWT detected. Token revocation usually requires extra logic compared to sessions."]
            ))
        return tradeoffs
