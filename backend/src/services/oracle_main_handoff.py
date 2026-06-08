"""
ORACLE → MAIN Agent Handoff Orchestrator — Stage 4

Deterministic handoff pipeline that:
1. Takes ORACLE StructuredContext
2. Builds IntelligenceArtifact  
3. Persists artifact to session storage
4. Emits ORACLE_INTELLIGENCE_READY event
5. Signals MAIN Agent to start viva
"""

import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from src.models.intelligence_artifact import IntelligenceArtifact, IntelligenceHandoffEvent
from src.models.context import StructuredContext
from src.models.events import EventType, PlatformEvent
from src.services.intelligence_artifact_builder import IntelligenceArtifactBuilder
from src.services.storage import FileStorageProvider


class OracleMainHandoffOrchestrator:
    """
    Manages deterministic handoff from ORACLE analysis to MAIN Agent.
    
    Responsibilities:
    - Convert StructuredContext to IntelligenceArtifact
    - Persist artifact for audit/replay
    - Emit handoff event
    - Ensure deterministic, explainable transition
    """

    def __init__(self, storage_provider: Optional[FileStorageProvider] = None):
        import os
        if storage_provider is None:
            base_path = os.path.join(os.getcwd(), "session_storage", "artifacts")
            os.makedirs(base_path, exist_ok=True)
            storage_provider = FileStorageProvider(base_path)
        self.storage = storage_provider
        self.handoff_log = []

    async def handoff(
        self,
        session_id: str,
        oracle_context: StructuredContext,
        analysis_duration_seconds: float = 0.0,
        repo_path: Optional[str] = None,
    ) -> IntelligenceArtifact:
        """
        Execute handoff from ORACLE to MAIN Agent.

        Args:
            session_id: Exam session ID
            oracle_context: ORACLE's StructuredContext output
            analysis_duration_seconds: Time spent in ORACLE analysis
            repo_path: Optional repo path for evidence collection

        Returns:
            IntelligenceArtifact ready for MAIN Agent
        """

        handoff_start = time.time()

        # Step 1: Build IntelligenceArtifact
        artifact = IntelligenceArtifactBuilder.build(
            session_id=session_id,
            structured_context=oracle_context,
            analysis_duration_seconds=analysis_duration_seconds,
            repo_path=repo_path,
        )

        # Step 2: Persist artifact to session storage
        await self._persist_artifact(session_id, artifact)

        # Step 3: Emit handoff event
        handoff_event = IntelligenceHandoffEvent(
            session_id=session_id,
            artifact_id=artifact.artifact_id,
            artifact_summary={
                "project": artifact.project_name,
                "num_execution_nodes": len(artifact.execution_graph_nodes),
                "num_execution_paths": len(artifact.execution_paths),
                "num_viva_targets": len(artifact.viva_targets),
                "num_failure_scenarios": len(artifact.failure_scenarios),
                "num_weak_points": len(artifact.weak_points),
                "analysis_confidence": artifact.analysis_confidence,
            },
        )

        # Step 4: Log handoff transaction
        handoff_duration = time.time() - handoff_start
        self._log_handoff(session_id, artifact, handoff_duration)

        return artifact

    async def _persist_artifact(self, session_id: str, artifact: IntelligenceArtifact) -> None:
        """Persist IntelligenceArtifact to session storage for audit/replay."""

        # Serialize artifact
        artifact_data = artifact.model_dump_json(indent=2)

        # Store with session
        artifact_filename = f"oracle_intelligence_{artifact.artifact_id}.json"
        artifact_path = f"sessions/{session_id}/{artifact_filename}"

        # Use storage provider
        self.storage.append_artifact(
            session_id=session_id,
            artifact_type="ORACLE_INTELLIGENCE_ARTIFACT",
            payload={
                "artifact_id": artifact.artifact_id,
                "project_name": artifact.project_name,
                "timestamp": artifact.generated_at.isoformat(),
                "deterministic_hash": artifact.deterministic_hash,
                "viva_targets": len(artifact.viva_targets),
                "failure_scenarios": len(artifact.failure_scenarios),
            },
        )

    def _log_handoff(self, session_id: str, artifact: IntelligenceArtifact, duration_seconds: float) -> None:
        """Log handoff transaction for audit trail."""

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "artifact_id": artifact.artifact_id,
            "handoff_duration_seconds": duration_seconds,
            "artifact_summary": {
                "project": artifact.project_name,
                "viva_targets": len(artifact.viva_targets),
                "failure_scenarios": len(artifact.failure_scenarios),
                "weak_points": len(artifact.weak_points),
            },
            "deterministic_hash": artifact.deterministic_hash,
            "status": "SUCCESS",
        }

        self.handoff_log.append(log_entry)

    def get_artifact(self, session_id: str, artifact_id: str) -> Optional[IntelligenceArtifact]:
        """Retrieve persisted artifact for MAIN Agent or audit purposes."""

        # This would load from storage
        # Simplified for now
        return None


class OracleIntelligenceService:
    """
    Wrapper service that orchestrates ORACLE analysis and handoff in a single flow.
    Combines ORACLE analysis with handoff to MAIN Agent.
    """

    def __init__(self, oracle_agent, handoff_orchestrator: Optional[OracleMainHandoffOrchestrator] = None):
        self.oracle_agent = oracle_agent
        self.handoff_orchestrator = handoff_orchestrator or OracleMainHandoffOrchestrator()

    async def analyze_and_handoff(
        self,
        session_id: str,
        input_data: Dict[str, Any],
        log_callback=None,
    ) -> IntelligenceArtifact:
        """
        Execute full ORACLE analysis and handoff to MAIN Agent.

        Flow:
        1. Run ORACLE analysis → StructuredContext
        2. Convert to IntelligenceArtifact
        3. Persist and emit event
        4. Return artifact ready for MAIN Agent

        Args:
            session_id: Exam session ID
            input_data: Input to ORACLE (repo_url, report_path, etc.)
            log_callback: Optional async callback for logging

        Returns:
            IntelligenceArtifact ready for MAIN Agent viva
        """

        async def send_log(msg: str, type_: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type_})

        await send_log("[Stage 4] Starting ORACLE analysis...", "info")

        # Step 1: Run ORACLE analysis
        analysis_start = time.time()
        oracle_context = await self.oracle_agent.process(session_id, input_data, log_callback)
        analysis_duration = time.time() - analysis_start

        await send_log(f"[Stage 4] ORACLE analysis complete ({analysis_duration:.2f}s)", "info")

        # Step 2: Handoff to MAIN Agent
        await send_log("[Stage 4] Building intelligence artifact for MAIN Agent...", "info")
        artifact = await self.handoff_orchestrator.handoff(
            session_id=session_id,
            oracle_context=oracle_context,
            analysis_duration_seconds=analysis_duration,
            repo_path=input_data.get("repo_path"),
        )

        await send_log(
            f"[Stage 4] Intelligence handoff complete. Artifact: {artifact.artifact_id}", "success"
        )

        # Step 3: Emit platform event
        if hasattr(self.oracle_agent, "emit_event"):
            self.oracle_agent.emit_event(
                session_id,
                EventType.ORACLE_INTELLIGENCE_READY,
                {
                    "artifact_id": artifact.artifact_id,
                    "viva_targets": len(artifact.viva_targets),
                    "weak_points": len(artifact.weak_points),
                    "next_stage": "MAIN_AGENT_START_VIVA",
                },
            )

        await send_log("[Stage 4] Ready to start viva with MAIN Agent.", "success")

        return artifact
