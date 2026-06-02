"""
Stage 7 - SENTINEL Parallel Oversight

SENTINEL is a monitoring-only component. It never asks viva questions or
changes pacing. It only surfaces observable integrity signals.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.stage_7_8_9 import (
    IntegritySeverity,
    IntegritySignalType,
    SentinelAlert,
    SentinelIntegrityEvent,
)
from src.services.storage import FileStorageProvider


class SentinelParallelMonitor:
    """Deterministic integrity monitor for live viva sessions."""

    def __init__(self, session_id: str, storage_provider: Optional[FileStorageProvider] = None):
        self.session_id = session_id
        if storage_provider is None:
            import os

            base_path = os.path.join(os.getcwd(), "session_storage", "sentinel")
            os.makedirs(base_path, exist_ok=True)
            storage_provider = FileStorageProvider(base_path)

        self.storage = storage_provider
        self.integrity_events: List[SentinelIntegrityEvent] = []
        self.alerts: List[SentinelAlert] = []

    def evaluate_observation(self, turn_index: int, observation: Dict[str, Any]) -> List[SentinelIntegrityEvent]:
        """
        Evaluate observable signals and produce structured integrity events.

        Expected observation fields:
        - gaze_offscreen_seconds: float
        - gaze_shift_count: int
        - interruption_count: int
        - audio_anomaly_score: float (0-1)
        - visibility_ratio: float (0-1)
        - response_confidence: float (0-1)
        - contradiction_count: int
        - silence_ratio: float (0-1)
        - environment_change_detected: bool
        """

        events: List[SentinelIntegrityEvent] = []

        def _emit(signal_type: IntegritySignalType, severity: IntegritySeverity, explanation: str, evidence: Dict[str, Any]) -> None:
            event = SentinelIntegrityEvent(
                event_id=f"sentinel_{self.session_id}_{turn_index}_{len(self.integrity_events) + len(events)}",
                session_id=self.session_id,
                signal_type=signal_type,
                severity=severity,
                explanation=explanation,
                evidence=evidence,
                replay_metadata={
                    "turn_index": turn_index,
                    "observation_snapshot": observation,
                },
            )
            events.append(event)

        gaze_offscreen_seconds = float(observation.get("gaze_offscreen_seconds", 0.0))
        if gaze_offscreen_seconds >= 15.0:
            _emit(
                IntegritySignalType.PROLONGED_OFFSCREEN_FOCUS,
                IntegritySeverity.HIGH if gaze_offscreen_seconds >= 25.0 else IntegritySeverity.MEDIUM,
                f"Student looked away from screen for {gaze_offscreen_seconds:.1f} seconds during active response window.",
                {"gaze_offscreen_seconds": gaze_offscreen_seconds},
            )

        gaze_shift_count = int(observation.get("gaze_shift_count", 0))
        if gaze_shift_count >= 6:
            _emit(
                IntegritySignalType.REPEATED_GAZE_SHIFT,
                IntegritySeverity.MEDIUM,
                f"Repeated gaze shifts detected ({gaze_shift_count} shifts) in a single turn.",
                {"gaze_shift_count": gaze_shift_count},
            )

        interruption_count = int(observation.get("interruption_count", 0))
        if interruption_count >= 2:
            _emit(
                IntegritySignalType.SESSION_INTERRUPTION,
                IntegritySeverity.MEDIUM if interruption_count < 4 else IntegritySeverity.HIGH,
                f"Session interruption pattern detected ({interruption_count} interruptions).",
                {"interruption_count": interruption_count},
            )

        audio_anomaly_score = float(observation.get("audio_anomaly_score", 0.0))
        if audio_anomaly_score >= 0.7:
            _emit(
                IntegritySignalType.SUSPICIOUS_AUDIO_PATTERN,
                IntegritySeverity.MEDIUM if audio_anomaly_score < 0.85 else IntegritySeverity.HIGH,
                f"Unusual audio pattern score observed ({audio_anomaly_score:.2f}).",
                {"audio_anomaly_score": audio_anomaly_score},
            )

        visibility_ratio = float(observation.get("visibility_ratio", 1.0))
        if visibility_ratio <= 0.55:
            _emit(
                IntegritySignalType.LOW_VISIBILITY_WARNING,
                IntegritySeverity.MEDIUM,
                f"Low camera visibility ratio observed ({visibility_ratio:.2f}).",
                {"visibility_ratio": visibility_ratio},
            )

        response_confidence = float(observation.get("response_confidence", 1.0))
        if response_confidence <= 0.45:
            _emit(
                IntegritySignalType.CONFIDENCE_INSTABILITY,
                IntegritySeverity.MEDIUM,
                f"Speech/transcript confidence unstable at {response_confidence:.2f}.",
                {"response_confidence": response_confidence},
            )

        contradiction_count = int(observation.get("contradiction_count", 0))
        if contradiction_count >= 2:
            _emit(
                IntegritySignalType.CONTRADICTION_ESCALATION,
                IntegritySeverity.HIGH if contradiction_count >= 3 else IntegritySeverity.MEDIUM,
                f"Contradiction escalation frequency detected ({contradiction_count} contradictions).",
                {"contradiction_count": contradiction_count},
            )

        silence_ratio = float(observation.get("silence_ratio", 0.0))
        if silence_ratio >= 0.65:
            _emit(
                IntegritySignalType.EXCESSIVE_SILENCE_PATTERN,
                IntegritySeverity.MEDIUM,
                f"Excessive silence detected with ratio {silence_ratio:.2f}.",
                {"silence_ratio": silence_ratio},
            )

        if bool(observation.get("environment_change_detected", False)):
            _emit(
                IntegritySignalType.ENVIRONMENT_CHANGE,
                IntegritySeverity.MEDIUM,
                "Environmental change detected during active viva turn.",
                {"environment_change_detected": True},
            )

        self.integrity_events.extend(events)
        for event in events:
            self.storage.append_artifact(
                session_id=self.session_id,
                artifact_type="SENTINEL_EVENT",
                payload=event.model_dump(mode="json"),
            )

        # Manual review recommendation is deterministic from count and severity.
        high_severity_count = sum(1 for e in events if e.severity == IntegritySeverity.HIGH)
        if high_severity_count >= 1 or len(events) >= 3:
            alert = SentinelAlert(
                alert_id=f"alert_{self.session_id}_{turn_index}_{len(self.alerts)}",
                session_id=self.session_id,
                event_ids=[e.event_id for e in events],
                manual_review_recommended=True,
                reason="Integrity threshold reached based on observable signals.",
            )
            self.alerts.append(alert)
            self.storage.append_artifact(
                session_id=self.session_id,
                artifact_type="SENTINEL_ALERT",
                payload=alert.model_dump(mode="json"),
            )

        return events

    def get_active_alerts(self) -> List[SentinelAlert]:
        """Return all generated alerts for session-level attachment."""

        return self.alerts

    def attach_alerts_to_exam_session(self, exam_session: Dict[str, Any]) -> Dict[str, Any]:
        """Attach SENTINEL alerts to an exam session payload."""

        updated = dict(exam_session)
        existing_alerts = list(updated.get("integrity_alerts", []))
        existing_alerts.extend([a.model_dump(mode="json") for a in self.alerts])
        updated["integrity_alerts"] = existing_alerts
        updated["manual_review_recommended"] = any(a.manual_review_recommended for a in self.alerts)
        updated["integrity_last_updated_at"] = datetime.utcnow().isoformat()
        return updated
