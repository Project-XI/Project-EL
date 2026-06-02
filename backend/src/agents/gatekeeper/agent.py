from typing import Any, Dict
from src.agents.base import BaseAgent
from src.models.events import EventType

from .pipeline.gatekeeper_pipeline import GatekeeperPipeline


class GatekeeperAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="GatekeeperAgent")
        # Global pipeline instance so history store persists across requests
        self._pipeline = GatekeeperPipeline()

    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None) -> Dict[str, Any]:
        """
        Gatekeeper Identity & Session Agent.
        Runs the full verification pipeline (Roll + Face + Conflict).
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"Gatekeeper running verification for session {session_id}.")
        await send_log("[Gatekeeper] Starting End-to-End Verification Pipeline...", "info")
        
        # ── 1. Extract inputs ─────────────────────────────────────────────────
        # Typically provided by frontend/client API.
        raw_roll = input_data.get("roll_number", "")
        raw_face = input_data.get("face_id", "")

        # ── 2. Run Pipeline ───────────────────────────────────────────────────
        result = self._pipeline.run(raw_roll, raw_face)

        # ── 3. Emit Events & Logs ─────────────────────────────────────────────
        decision = result.access_decision
        
        if result.is_admitted:
            await send_log(f"[Gatekeeper] Identity Verified: {decision.student_name} ({decision.roll_number})", "success")
            self.emit_event(session_id, EventType.IDENTITY_VERIFIED, {"roll_number": decision.roll_number})
        else:
            await send_log(f"[Gatekeeper] Access {decision.decision.value.upper()}: {decision.reasons[0]}", "error")

        self.emit_event(session_id, EventType.AGENT_PROGRESS, {
            "agent": "Gatekeeper", 
            "status": "complete", 
            "milestone": "Pipeline Executed",
            "decision": decision.decision.value,
        })
        
        # ── 4. Return Output ──────────────────────────────────────────────────
        # Append pipeline results into the original input_data dictionary so 
        # Oracle or downstream agents can consume it.
        output_data = input_data.copy()
        output_data["gatekeeper_result"] = result.to_dict()
        
        return output_data
