from src.agents.base import BaseAgent


from typing import Any, Dict
from src.agents.base import BaseAgent
from src.models.context import StructuredContext
from src.agents.gatekeeper.agent import GatekeeperAgent
from src.agents.oracle.agent import OracleAgent
from src.agents.sentinel.agent import SentinelAgent

class MainAgent(BaseAgent):
    def __init__(self, prompt_version: str = "v2"):
        super().__init__(name="MainAgent")
        self.prompt_version = prompt_version
        self.gatekeeper = GatekeeperAgent()
        self.oracle = OracleAgent()
        self.sentinel = SentinelAgent()

    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None) -> StructuredContext:
        """
        Orchestrates the project intelligence pipeline according to the defined agent roles.
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"MainAgent starting analysis for session {session_id}")
        
        # Agent 2 (GATEKEEPER) — Identity + Session Agent (Placeholder)
        gatekeeper_output = await self.gatekeeper.process(session_id, input_data, log_callback)
        
        # Agent 1 (ORACLE) — Submission Intelligence Agent
        oracle_output = await self.oracle.process(session_id, gatekeeper_output, log_callback)
        
        # Agent 3 (SENTINEL) — Behaviour Analysis Agent (Placeholder)
        final_context = await self.sentinel.process(session_id, oracle_output, log_callback)

        self.log_info(f"MainAgent finished analysis for session {session_id}")
        await send_log("[MainAgent] Analysis complete.", "success")
        
        return final_context

