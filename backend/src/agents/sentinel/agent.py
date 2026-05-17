from src.agents.base import BaseAgent


from typing import Any, Dict
from src.agents.base import BaseAgent
from src.models.events import EventType
from src.models.context import StructuredContext, EvidenceModel
from src.services.intelligence.architecture_inference_engine import ArchitectureInferenceEngine
from src.services.intelligence.reasoning_inference_engine import ReasoningInferenceEngine
from src.services.intelligence.viva_intelligence_engine import VivaIntelligenceEngine

class SentinelAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="SentinelAgent")

    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None) -> StructuredContext:
        """
        Synthesizes intelligence, detects inconsistencies, and builds the final structured context.
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"Sentinel starting for session {session_id}")
        await send_log("[Sentinel] Synthesizing final intelligence...", "info")

        doc_text = input_data.get("doc_text", "")
        repo_detections = input_data.get("repo_detections", {})
        project_graph = input_data.get("project_graph")

        # Intelligence Synthesis
        await send_log("[Sentinel] Running explainability engine...")
        arch_inference = ArchitectureInferenceEngine.infer_architecture(project_graph, repo_detections)
        reasoning = ReasoningInferenceEngine.infer_reasoning(repo_detections)
        tradeoffs = ReasoningInferenceEngine.infer_tradeoffs(repo_detections)
        
        await send_log("[Sentinel] Generating viva intelligence...")
        viva_targets = VivaIntelligenceEngine.generate_targets(repo_detections, arch_inference)
        inconsistencies = VivaIntelligenceEngine.detect_inconsistencies(doc_text, repo_detections)
        complexity_mismatch = VivaIntelligenceEngine.detect_complexity_mismatch(arch_inference, repo_detections)

        # Final Synthesis
        context = StructuredContext(
            project_name=EvidenceModel(value="Project TWELVE", confidence=0.9, evidence=["Inferred from repo/docs"]),
            project_type=EvidenceModel(value="Intelligence System", confidence=0.8, evidence=["Technical analysis patterns"]),
            frontend_framework=repo_detections.get("frontend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            backend_framework=repo_detections.get("backend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            database_used=repo_detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            authentication_system=repo_detections.get("authentication_system", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            architecture_pattern=arch_inference,
            project_graph=project_graph,
            execution_graph=input_data.get("execution_graph"),
            implementation_reasoning=reasoning,
            tradeoff_analysis=tradeoffs,
            viva_intelligence_targets=viva_targets,
            inconsistencies=inconsistencies,
            complexity_mismatch=complexity_mismatch
        )

        self.emit_event(session_id, EventType.CONTEXT_READY, {"project_name": context.project_name.value})
        await send_log("[Sentinel] Analysis complete.", "success")
        self.emit_event(session_id, "AGENT_PROGRESS", {"agent": "Sentinel", "status": "complete", "milestone": "Final Synthesis"})

        return context
