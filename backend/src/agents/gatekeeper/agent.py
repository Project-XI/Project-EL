"""
GatekeeperAgent — Identity, Session, and Student Registry gate.

Entry point for all student identity verification in the EL system.
Consumes the StudentRegistry to validate roll numbers before any session
is allowed to proceed to ORACLE analysis.
"""

from typing import Any, Dict, Optional
from src.agents.base import BaseAgent
from .registry.registry_store import StudentRegistry, SAMPLE_STUDENTS
from .registry.lookup import RegistryLookup, LookupResult, LookupFailureReason


class GatekeeperAgent(BaseAgent):
    def __init__(self, registry: Optional[StudentRegistry] = None):
        super().__init__(name="GatekeeperAgent")
        # Use injected registry (for testing) or create and seed the default one
        if registry is not None:
            self._registry = registry
        else:
            self._registry = StudentRegistry()
            self._registry.seed(SAMPLE_STUDENTS)
        self._lookup = RegistryLookup(self._registry)

    async def process(
        self,
        session_id: str,
        input_data: Dict[str, Any],
        log_callback=None,
    ) -> Dict[str, Any]:
        """
        Validate student identity before allowing session to proceed.

        Expected input_data keys:
          - roll_number (str): Student roll number to verify
          - [any other session fields passed through]

        Returns input_data enriched with:
          - gatekeeper_status: "verified" | "rejected"
          - gatekeeper_reason: failure reason string (if rejected)
          - student_profile:   plain dict of StudentProfile (if verified)
        """
        async def send_log(msg: str, log_type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": log_type})

        self.log_info(f"Gatekeeper processing session {session_id}")
        await send_log("[Gatekeeper] Identity verification started.", "info")

        roll_number: str = input_data.get("roll_number", "")

        # ── Roll-number lookup ────────────────────────────────────────────────
        result: LookupResult = self._lookup.by_roll_number(roll_number)

        if result.success:
            self.log_info(
                f"Student verified: {result.profile.full_name} ({result.roll_number})"
            )
            await send_log(
                f"[Gatekeeper] ✅ Student verified: {result.profile.full_name}", "success"
            )
            self.emit_event(
                session_id, "AGENT_PROGRESS",
                {
                    "agent": "Gatekeeper",
                    "status": "complete",
                    "milestone": f"Identity Verified: {result.roll_number}",
                },
            )
            return {
                **input_data,
                "gatekeeper_status": "verified",
                "gatekeeper_reason": None,
                "student_profile":   result.profile.to_dict(),
            }

        # ── Rejection ─────────────────────────────────────────────────────────
        self.log_info(
            f"Gatekeeper rejected '{roll_number}': {result.failure_reason} — {result.message}"
        )
        await send_log(
            f"[Gatekeeper] ❌ Rejected: {result.message}", "error"
        )
        self.emit_event(
            session_id, "AGENT_PROGRESS",
            {
                "agent": "Gatekeeper",
                "status": "failed",
                "milestone": f"Identity Rejected: {result.failure_reason}",
            },
        )
        return {
            **input_data,
            "gatekeeper_status": "rejected",
            "gatekeeper_reason": result.failure_reason.value if result.failure_reason else "unknown",
            "student_profile":   None,
        }

    @property
    def registry(self) -> StudentRegistry:
        """Expose the registry for direct queries (e.g. batch listing)."""
        return self._registry

    @property
    def lookup(self) -> RegistryLookup:
        """Expose the lookup service for external callers."""
        return self._lookup
