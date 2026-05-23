from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings
from .agents.main_agent.agent import MainAgent

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    repo_url: str
    report_path: str = None # Allow optional document uploads
    enable_viva: bool = True
    enable_debug: bool = True
    generate_report: bool = False

# Initialize the orchestrator and agents
main_agent = MainAgent()
gatekeeper_pipeline = main_agent.gatekeeper._pipeline  # Access the global pipeline instance

class GatekeeperVerifyRequest(BaseModel):
    roll_number: str
    face_id: str = None

@app.get("/")
async def root():
    return {"message": "Welcome to ORACLE API", "status": "operational"}

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

@app.post("/gatekeeper/verify")
async def gatekeeper_verify(request: GatekeeperVerifyRequest):
    """
    Direct endpoint to run the Gatekeeper verification pipeline.
    """
    result = gatekeeper_pipeline.run(request.roll_number, request.face_id)
    return {"status": "success", "data": result.to_dict()}

@app.get("/gatekeeper/registry")
async def gatekeeper_registry():
    """
    Endpoint to fetch all active registered students.
    """
    students = gatekeeper_pipeline._registry.all_active()
    return {"status": "success", "data": [s.to_dict() for s in students]}

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
