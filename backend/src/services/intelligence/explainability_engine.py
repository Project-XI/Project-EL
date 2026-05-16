from typing import List, Dict, Any
from ...models.context import StructuredContext

class ExplainabilityEngine:
    """
    Synthesizes evidence-driven explanations for ORACLE claims.
    """
    @staticmethod
    def explain_claim(context: StructuredContext, claim_id: str) -> Dict[str, Any]:
        # Mapping logic to find evidence for a specific conclusion
        # This is a simplified version that returns explanation based on context fields
        
        explanations = {
            "tech_stack": {
                "claim": f"Backend detected as {context.backend_framework.value}",
                "evidence": context.backend_framework.evidence,
                "confidence": context.backend_framework.confidence,
                "reasoning": "Detected framework-specific configuration files or directory structures."
            },
            "auth_flow": {
                "claim": "Authentication flow traced",
                "evidence": context.authentication_flow.evidence if context.authentication_flow else [],
                "confidence": context.authentication_flow.confidence if context.authentication_flow else 0.0,
                "reasoning": "Identified security handlers and middleware chain entry points."
            }
        }
        
        return explanations.get(claim_id, {"error": "Claim ID not found or not yet supported for explanation."})
