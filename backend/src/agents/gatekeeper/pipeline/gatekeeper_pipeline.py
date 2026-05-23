"""
gatekeeper_pipeline.py
──────────────────────
Central orchestrator for the GATEKEEPER verification process.

Responsibilities
────────────────
- Construct all stage engines (Registry, Roll, Face, History, Conflict, Auth).
- Execute the verification stages in sequence for a given session.
- Manage error boundaries (never raise).
- Return a structured PipelineResult.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from src.agents.gatekeeper.authorization.auth_engine import AuthorizationEngine
from src.agents.gatekeeper.conflict_detection.conflict_detector import IdentityConflictDetector
from src.agents.gatekeeper.face_history.history_checker import FaceHistoryChecker
from src.agents.gatekeeper.face_history.history_store import FaceHistoryStore
from src.agents.gatekeeper.face_verification.face_verifier import FaceVerifier
from src.agents.gatekeeper.pipeline.pipeline_result import PipelineResult
from src.agents.gatekeeper.registry.registry_store import StudentRegistry
from src.agents.gatekeeper.roll_verification.fixtures import build_fixture_registry
from src.agents.gatekeeper.roll_verification.flow import RollVerificationFlow

logger = logging.getLogger(__name__)


class GatekeeperPipeline:
    """
    End-to-End GATEKEEPER Verification Pipeline.

    Usage
    ─────
        pipeline = GatekeeperPipeline()
        result   = pipeline.run("150096725066", "photos/150096725066.jpg")
        if result.is_admitted:
            ...
    """

    def __init__(self, registry: Optional[StudentRegistry] = None, history_store: Optional[FaceHistoryStore] = None) -> None:
        """
        Initialize pipeline dependencies.
        Uses fixture registry and isolated memory history store by default.
        """
        # Shared state stores
        self._registry = registry or build_fixture_registry()
        self._history_store = history_store or FaceHistoryStore()

        # Pipeline stages
        self._roll_verifier = RollVerificationFlow(registry=self._registry, require_manual_confirmation=False)
        self._face_verifier = FaceVerifier(registry=self._registry)
        self._history_checker = FaceHistoryChecker(store=self._history_store)
        self._conflict_detector = IdentityConflictDetector()
        self._auth_engine = AuthorizationEngine()

    def run(self, raw_roll_number: str, raw_face_id: Optional[str] = None) -> PipelineResult:
        """
        Execute the full verification pipeline.
        """
        start_time = time.time()
        logger.info("[GatekeeperPipeline] Starting verification for roll=%s face=%s", raw_roll_number, raw_face_id)

        # ── Stage 1: Roll Number Verification (Identity Lookup) ───────────────
        roll_result = self._roll_verifier.verify(raw_roll_number)
        
        # ── Stage 2: Face Verification (Biometric Check) ──────────────────────
        # We run this even if roll fails, though it will naturally fail NO_PHOTO / UNVERIFIABLE
        # It's safer to run it so the interface receives complete stage results.
        normalized_roll = roll_result.roll_number  # Use normalized roll from Stage 1
        face_result = self._face_verifier.verify(normalized_roll, raw_face_id)

        # ── Stage 3: Face History Check ───────────────────────────────────────
        # Only check history if a face was presented.
        if raw_face_id and raw_face_id.strip() and roll_result.is_verified:
            history_result = self._history_checker.check(normalized_roll, raw_face_id)
        else:
            # Dummy clean result if we skipped history
            from src.agents.gatekeeper.face_history.history_checker import HistoryCheckResult
            history_result = HistoryCheckResult(roll_number=normalized_roll, face_id=raw_face_id or "", is_new_face=True)

        # ── Stage 4: Identity Conflict Detection ──────────────────────────────
        conflict_report = self._conflict_detector.analyze(history_result)

        # ── Stage 5: Final Authorization Decision ─────────────────────────────
        access_decision = self._auth_engine.evaluate(
            roll_result=roll_result,
            face_result=face_result,
            conflict_report=conflict_report,
        )

        # ── Post-Pipeline: State Updates ──────────────────────────────────────
        # If granted, we record the face in history for future checks.
        if access_decision.is_granted and raw_face_id:
            self._history_store.record(normalized_roll, raw_face_id)

        # ── Result Assembly ───────────────────────────────────────────────────
        duration_ms = (time.time() - start_time) * 1000.0

        stage_results = {
            "roll_verification": roll_result.to_dict(),
            "face_verification": face_result.to_dict(),
            "history_check": history_result.to_dict(),
            "conflict_detection": conflict_report.to_dict(),
        }

        logger.info(
            "[GatekeeperPipeline] Finished in %.1fms. Decision: %s",
            duration_ms, access_decision.decision.value
        )

        return PipelineResult(
            is_admitted=access_decision.is_granted,
            access_decision=access_decision,
            pipeline_duration_ms=duration_ms,
            stage_results=stage_results,
        )
