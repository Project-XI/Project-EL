"""
Viva Session Persistence Layer — Stage 5

Handles deterministic, replay-safe persistence of:
- Viva session state
- Question-answer chains
- Contradiction events
- Evaluation results
- Timestamps for audit trail
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.models.intelligence_artifact import VivaSessionState
from src.services.storage import FileStorageProvider


class VivaSessionStore:
    """
    Persistent store for viva session data with audit trail support.

    Responsibilities:
    - Save/load session state
    - Persist question-answer chains
    - Log contradiction events
    - Support replay verification
    - Maintain deterministic artifact references
    """

    def __init__(self, storage_provider: Optional[FileStorageProvider] = None):
        import os
        if storage_provider is None:
            base_path = os.path.join(os.getcwd(), "session_storage", "viva")
            os.makedirs(base_path, exist_ok=True)
            storage_provider = FileStorageProvider(base_path)
        self.storage = storage_provider

    async def save_session_state(
        self, session_id: str, viva_session_state: VivaSessionState
    ) -> str:
        """
        Save viva session state to persistent storage.

        Returns:
            Path/ID of saved state
        """

        state_data = viva_session_state.model_dump_json(indent=2)

        state_id = f"viva_state_{datetime.utcnow().isoformat().replace(':', '-')}.json"

        self.storage.append_artifact(
            session_id=session_id,
            artifact_type="VIVA_SESSION_STATE",
            payload={
                "viva_phase": viva_session_state.viva_phase,
                "questions_asked": viva_session_state.questions_asked,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return state_id

    async def save_question_answer_pair(
        self,
        session_id: str,
        question_data: Dict[str, Any],
        answer_data: Dict[str, Any],
        evaluation_data: Dict[str, Any],
    ) -> str:
        """
        Save a question-answer-evaluation triplet.

        Returns:
            Transcript segment ID
        """

        qa_pair = {
            "question": question_data,
            "answer": answer_data,
            "evaluation": evaluation_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        qa_json = json.dumps(qa_pair, indent=2)

        qa_id = f"qa_pair_{len(datetime.utcnow().isoformat())}_{question_data.get('target_id', 'unknown')}.json"

        self.storage.append_artifact(
            session_id=session_id,
            artifact_type="VIVA_QA_PAIR",
            payload={
                "target_id": question_data.get("target_id"),
                "depth_level": answer_data.get("depth_level"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return qa_id

    async def save_contradiction_event(
        self, session_id: str, contradiction_event: Dict[str, Any]
    ) -> str:
        """Save detected contradiction for audit trail."""

        event_data = {
            "type": "CONTRADICTION_DETECTED",
            "event": contradiction_event,
            "timestamp": datetime.utcnow().isoformat(),
        }

        event_json = json.dumps(event_data, indent=2)

        event_id = f"contradiction_{datetime.utcnow().isoformat().replace(':', '-')}.json"

        self.storage.append_artifact(
            session_id=session_id,
            artifact_type="VIVA_CONTRADICTION",
            payload={
                "target_id": contradiction_event.get("target_id"),
                "severity": contradiction_event.get("contradiction", {}).get("severity", "MEDIUM"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return event_id

    async def save_session_summary(
        self, session_id: str, summary: Dict[str, Any], oracle_artifact_id: str
    ) -> str:
        """
        Save final viva session summary with references to ORACLE artifact.

        Includes:
        - Performance metrics
        - Weak/strong areas
        - Contradiction events
        - ORACLE artifact reference (for replay)
        """

        summary_data = {
            "session_summary": summary,
            "oracle_artifact_reference": oracle_artifact_id,
            "saved_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
        }

        summary_json = json.dumps(summary_data, indent=2)

        summary_id = f"viva_summary_{session_id}_{datetime.utcnow().isoformat().replace(':', '-')}.json"

        self.storage.append_artifact(
            session_id=session_id,
            artifact_type="VIVA_SESSION_SUMMARY",
            payload={
                "total_questions": summary.get("total_questions"),
                "contradictions": summary.get("contradictions_found"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return summary_id

    async def load_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Load complete viva session history for analysis or replay.

        Returns session transcript, state changes, and key events.
        """

        # This would load from storage; simplified for now
        return {
            "session_id": session_id,
            "qa_pairs": [],
            "state_changes": [],
            "contradictions": [],
        }


class VivaTranscriptBuilder:
    """
    Builds human-readable and machine-parseable transcripts from viva sessions.

    Supports:
    - Plain text transcripts for export
    - JSON transcripts for analysis
    - Marked contradiction events
    - Performance metrics
    """

    @staticmethod
    def build_text_transcript(session_summary: Dict[str, Any]) -> str:
        """Build plain text transcript."""

        lines = []

        lines.append("=" * 60)
        lines.append(f"VIVA SESSION TRANSCRIPT")
        lines.append(f"Session ID: {session_summary['session_id']}")
        lines.append(f"Timestamp: {session_summary['timestamp']}")
        lines.append(f"Total Questions: {session_summary['total_questions']}")
        lines.append("=" * 60)
        lines.append("")

        for i, qa in enumerate(session_summary.get("questions", []), 1):
            lines.append(f"Q{i}: {qa.get('question', 'N/A')}")
            lines.append(f"    [Category: {qa.get('category')}, Difficulty: {qa.get('difficulty')}]")
            lines.append("")

        lines.append("")
        lines.append("=" * 60)
        lines.append("PERFORMANCE SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Average Depth Score: {session_summary.get('average_depth_score', 'N/A'):.2f}")
        lines.append(f"Average Coverage: {session_summary.get('average_coverage_score', 'N/A'):.2f}")
        lines.append(f"Weak Areas: {', '.join(session_summary.get('weak_areas', []))}")
        lines.append(f"Strong Areas: {', '.join(session_summary.get('strong_areas', []))}")
        lines.append(f"Contradictions Found: {session_summary.get('contradictions_found', 0)}")
        lines.append("")

        if session_summary.get("contradictions"):
            lines.append("=" * 60)
            lines.append("CONTRADICTIONS DETECTED")
            lines.append("=" * 60)
            for c in session_summary.get("contradictions"):
                lines.append(f"  - {c.get('contradiction', {}).get('previous')} vs {c.get('contradiction', {}).get('current')}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def build_json_transcript(session_summary: Dict[str, Any]) -> str:
        """Build JSON transcript for programmatic analysis."""

        return json.dumps(session_summary, indent=2, default=str)

    @staticmethod
    def build_evaluation_report(session_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build structured evaluation report from session summary.

        Used for grading and feedback generation.
        """

        return {
            "session_id": session_summary["session_id"],
            "overall_score": (
                session_summary.get("average_depth_score", 0)
                + session_summary.get("average_coverage_score", 0)
            )
            / 2,
            "depth_assessment": session_summary.get("average_depth_score"),
            "coverage_assessment": session_summary.get("average_coverage_score"),
            "weak_areas": session_summary.get("weak_areas", []),
            "strong_areas": session_summary.get("strong_areas", []),
            "contradictions_count": session_summary.get("contradictions_found", 0),
            "adaptive_difficulty_final": session_summary.get("final_adaptive_difficulty"),
            "viva_phase_final": session_summary.get("viva_phase"),
            "recommendations": VivaTranscriptBuilder._generate_recommendations(session_summary),
        }

    @staticmethod
    def _generate_recommendations(session_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on viva performance."""

        recommendations = []

        weak_areas = session_summary.get("weak_areas", [])
        if weak_areas:
            recommendations.append(
                f"Student should focus on strengthening understanding in: {', '.join(weak_areas)}"
            )

        contradictions = session_summary.get("contradictions_found", 0)
        if contradictions > 3:
            recommendations.append("Multiple contradictions detected. Consider additional technical depth assessment.")

        avg_depth = session_summary.get("average_depth_score", 0)
        if avg_depth < 3:
            recommendations.append("Responses suggest surface-level understanding. Recommend remedial study.")
        elif avg_depth > 8:
            recommendations.append("Student demonstrates strong implementation knowledge.")

        return recommendations
