import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.context import ContextBuilderAgent
from src.agents.examiner import MainExaminerAgent
from src.agents.monitor import BehaviourMonitorAgent
from src.agents.onboarding import OnboardingAgent
from src.models.events import EventType

async def verify_agents():
    print("--- Verifying Agent Instantiation ---")
    
    onboarding = OnboardingAgent()
    context_builder = ContextBuilderAgent()
    examiner = MainExaminerAgent()
    monitor = BehaviourMonitorAgent()
    
    session_id = "test_session_001"
    
    print("\n1. Testing Onboarding Agent...")
    success = await onboarding.process(session_id, {"student_id": "STU456"})
    print(f"Onboarding Success: {success}")
    
    print("\n2. Testing Context Builder Agent...")
    context = await context_builder.process(session_id, {"repo": "test-repo"})
    print(f"Context Project: {context.project_name}")
    
    print("\n3. Testing Examiner Agent...")
    question = await examiner.process(session_id, "I used Python for data processing.")
    print(f"Examiner Question: {question}")
    
    print("\n4. Testing Behaviour Monitor Agent...")
    await monitor.process(session_id, {"gaze_off_screen_duration": 4.5})
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_agents())
