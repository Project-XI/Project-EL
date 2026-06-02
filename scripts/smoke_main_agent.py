import sys
from pathlib import Path
sys.path.insert(0, str(Path('backend').resolve()))
import asyncio
import types

from src.agents.main_agent.agent import MainAgent

async def main():
    ma = MainAgent()

    async def fake_process(session_id, input_data, log_callback=None):
        return types.SimpleNamespace(implementation_viva_targets=[])

    # Patch dependent agents to avoid external I/O in smoke test
    ma.gatekeeper.process = fake_process
    ma.oracle.process = fake_process
    ma.sentinel.process = fake_process

    result = await ma.process("smoke-session-1", {"student_id": "test-123", "enable_voice": False})
    print("MainAgent.process returned:", type(result), getattr(result, 'implementation_viva_targets', None))

if __name__ == '__main__':
    asyncio.run(main())
