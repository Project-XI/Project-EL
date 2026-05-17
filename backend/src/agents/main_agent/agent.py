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
        Orchestrates the project intelligence pipeline by coordinating other agents.
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"MainAgent starting analysis for session {session_id}")
        
        # 1. Gatekeeper: Session start, input validation, and initial data parsing
        initial_context = await self.gatekeeper.process(session_id, input_data, log_callback)
        
        # 2. Oracle: Deep repository and intelligence analysis
        analysis_context = await self.oracle.process(session_id, initial_context, log_callback)
        
        # 3. Sentinel: Behavior, risk analysis, and final checks
        final_context = await self.sentinel.process(session_id, analysis_context, log_callback)

        self.log_info(f"MainAgent finished analysis for session {session_id}")
        await send_log("[MainAgent] Analysis complete.", "success")
        
        return final_context
