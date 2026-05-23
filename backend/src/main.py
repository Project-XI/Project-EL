from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings
from .agents.main_agent.agent import MainAgent
from .services.face_detection import FaceDetectionService
from .services.audit_log import AuditLogService

app = FastAPI(title=settings.PROJECT_NAME)
face_service = FaceDetectionService()
audit_log = AuditLogService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    repo_url: str
    report_path: Optional[str] = None
    enable_viva: bool = True
    enable_debug: bool = True
    generate_report: bool = False

class FaceVerifyRequest(BaseModel):
    embedding: List[float]
    roll_number: str
    session_id: Optional[str] = None

class ResolveAlertRequest(BaseModel):
    conflict_id: str
    approved: bool = False
    reviewer_id: Optional[str] = None
    reason: Optional[str] = None

class AdminReviewRequest(BaseModel):
    conflict_id: str
    approved: bool
    reviewer_id: str
    reason: str

# Initialize the main orchestrator agent
main_agent = MainAgent()

@app.get("/")
async def root():
    return {"message": "Welcome to ORACLE API", "status": "operational"}

@app.post("/face/verify")
async def verify_face(request: FaceVerifyRequest):
    is_valid, alert, similarity = face_service.verify_identity(
        embedding=request.embedding,
        roll_number=request.roll_number,
        session_id=request.session_id,
    )
    
    return {
        "is_valid": is_valid,
        "alert": alert.to_dict() if alert else None,
        "similarity": similarity,
    }

@app.get("/face/pending-alerts")
async def get_pending_alerts():
    return [alert.to_dict() for alert in face_service.get_pending_alerts()]

@app.post("/face/resolve-alert")
async def resolve_alert(request: ResolveAlertRequest):
    success = face_service.resolve_alert(
        request.conflict_id, 
        request.approved,
        request.reviewer_id,
        request.reason
    )
    return {"success": success}

@app.get("/face/conflict/{conflict_id}")
async def get_conflict_details(conflict_id: str):
    details = face_service.get_conflict_details(conflict_id)
    if details is None:
        return {"error": "Conflict not found"}, 404
    return details

@app.post("/admin/review-conflict")
async def admin_review_conflict(request: AdminReviewRequest):
    success = face_service.admin_review_conflict(
        request.conflict_id,
        request.approved,
        request.reviewer_id,
        request.reason
    )
    if not success:
        return {"error": "Conflict not found"}, 404
    return {"success": True, "message": "Review decision recorded"}

@app.get("/admin/override-log")
async def get_override_log():
    return face_service.get_override_log()

@app.get("/audit/timeline")
async def get_audit_timeline(roll_number: Optional[str] = None, session_id: Optional[str] = None):
    result = []
    if session_id:
        result = audit_log.get_session_timeline(session_id)
    elif roll_number:
        result = audit_log.get_timeline(roll_number)
    else:
        result = audit_log.get_timeline()
    return result

@app.get("/audit/search")
async def search_audit_log(query: str):
    return audit_log.search(query)

@app.get("/audit/events/{event_type}")
async def get_audit_events_by_type(event_type: str):
    return audit_log.get_events_by_type(event_type)

@app.post("/analyze")
async def analyze_repo(request: AnalyzeRequest):
    # Legacy REST endpoint for backward compatibility
    input_data = {"repo_url": request.repo_url, "report_path": request.report_path}
    context = await main_agent.process("api_session", input_data)
    try:
        data = context.model_dump()
    except AttributeError:
        data = context.dict()
    return {"status": "success", "data": data}

@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    await websocket.accept()
    try:
        # Receive the initial request
        data = await websocket.receive_json()
        repo_url = data.get("repo_url")
        report_path = data.get("report_path")
        
        if not repo_url:
            await websocket.send_json({"type": "log", "message": "[ERROR] Missing repo_url", "log_type": "error"})
            await websocket.close()
            return

        async def log_cb(log_data):
            # Send live logs to the UI terminal
            await websocket.send_json({"type": "log", **log_data})

        # Run the main agent with the live callback
        input_payload = {"repo_url": repo_url, "report_path": report_path}
        context = await main_agent.process("ws_session", input_payload, log_callback=log_cb)
        
        # Dump the final structured data
        try:
            ctx_data = context.model_dump()
        except AttributeError:
            ctx_data = context.dict()
            
        # Run Evaluation if ground-truth exists
        import os
        import json
        
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        # Try both direct name and lowercased snake_case
        expected_path_1 = os.path.join("evaluation", "expected_outputs", f"{repo_name}.json")
        expected_path_2 = os.path.join("evaluation", "expected_outputs", f"{repo_name.lower().replace('-', '_')}.json")
        
        expected_path = expected_path_1 if os.path.exists(expected_path_1) else expected_path_2
        
        evaluation_metrics = None
        if os.path.exists(expected_path):
            await log_cb({"message": f"[EVAL] Running precision benchmarks against {os.path.basename(expected_path)}...", "log_type": "info"})
            try:
                from evaluation.evaluation_runner import OracleEvaluator
                evaluator = OracleEvaluator()
                with open(expected_path, 'r') as f:
                    expected = json.load(f)
                
                metrics = evaluator._calculate_metrics(expected, ctx_data)
                mismatches = evaluator._find_mismatches(expected, ctx_data)
                evaluation_metrics = {
                    "metrics": metrics,
                    "mismatches": mismatches,
                    "expected": expected
                }
                await log_cb({"message": f"[EVAL] Benchmarks completed.", "log_type": "success"})
            except Exception as e:
                await log_cb({"message": f"[EVAL] Benchmark error: {str(e)}", "log_type": "error"})
        
        ctx_data["evaluation_metrics"] = evaluation_metrics
            
        await websocket.send_json({"type": "result", "data": ctx_data})
        
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket.")
    except Exception as e:
        await websocket.send_json({"type": "log", "message": f"[ERROR] Analysis failed: {str(e)}", "log_type": "error"})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
