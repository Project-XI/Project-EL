from fastapi import FastAPI, BackgroundTasks
from .core.config import settings
from .agents.onboarding import OnboardingAgent
from .agents.context import ContextBuilderAgent
from .agents.examiner import MainExaminerAgent
from .agents.monitor import BehaviourMonitorAgent

app = FastAPI(title=settings.PROJECT_NAME)

# Initialize Agents
onboarding_agent = OnboardingAgent()
context_builder = ContextBuilderAgent()
examiner = MainExaminerAgent()
monitor = BehaviourMonitorAgent()

@app.get("/")
async def root():
    return {"message": "Welcome to TWELVE API", "status": "operational"}

@app.post("/sessions/initialize")
async def initialize_session(student_id: str):
    # Workflow: Onboarding -> Context Building -> Start Viva
    session_id = "sess_123" # Mocked
    await onboarding_agent.process(session_id, {"student_id": student_id})
    return {"session_id": session_id, "status": "initialized"}

@app.post("/sessions/{session_id}/monitor")
async def monitor_behaviour(session_id: str, metadata: dict):
    # This can be processed in background
    await monitor.process(session_id, metadata)
    return {"status": "logged"}

@app.post("/sessions/{session_id}/respond")
async def student_respond(session_id: str, response_text: str):
    next_q = await examiner.process(session_id, response_text)
    return {"next_question": next_q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
