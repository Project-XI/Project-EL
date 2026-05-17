from src.agents.base import BaseAgent


from typing import Any, Dict
from src.agents.base import BaseAgent
from src.models.events import EventType
from src.models.context import StructuredContext, EvidenceModel, ProjectGraph
from src.services.github.repo_cloner import RepoCloner
from src.services.github.structure_analyzer import StructureAnalyzer
from src.services.github.tech_detector import TechDetector
from src.services.github.file_summarizer import FileSummarizer
from src.services.intelligence.project_relationship_engine import ProjectRelationshipEngine
from src.services.intelligence.graph_confidence_engine import GraphConfidenceEngine
from src.services.intelligence.implementation_flow_engine import ImplementationFlowEngine

class OracleAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="OracleAgent")

    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None) -> Dict[str, Any]:
        """
        Analyzes the repository to build a comprehensive project graph and technical context.
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"Oracle starting for session {session_id}")
        await send_log("[Oracle] Analyzing repository...", "info")

        repo_url = input_data.get("repo_url")
        repo_detections = {}
        project_graph = ProjectGraph()
        repo_structure = {}
        file_summaries = []
        repo_path = None

        if repo_url:
            try:
                import os
                target_dir = "./backend/data/cloned_repos"
                repo_name = repo_url.split("/")[-1].replace(".git", "")
                clone_path = os.path.join(target_dir, repo_name)
                
                if os.path.exists(clone_path):
                    await send_log(f"[Oracle] Using cached repository at {clone_path}...")
                else:
                    await send_log("[Oracle] Cloning repository...")
                    
                repo_path = RepoCloner.clone(repo_url, target_dir)
                if repo_path:
                    self.emit_event(session_id, EventType.REPO_CLONED, {"url": repo_url})
                    
                    await send_log("[Oracle] Detecting framework and structure...")
                    repo_structure = StructureAnalyzer.analyze(repo_path)
                    self.emit_event(session_id, EventType.STRUCTURE_ANALYZED, {"path": repo_path})
                    
                    repo_detections = TechDetector.detect_from_files(repo_path, repo_structure)
                    self.emit_event(session_id, EventType.TECH_STACK_DETECTED, {"count": len(repo_detections)})
                    
                    file_summaries = FileSummarizer.summarize_structure(repo_structure)
                    
                    await send_log("[Oracle] Building execution graph...")
                    project_graph = ProjectRelationshipEngine.infer_relationships(repo_path, repo_detections, repo_structure)
                    project_graph = GraphConfidenceEngine.refine_scores(project_graph)
                    self.emit_event(session_id, EventType.PROJECT_GRAPH_BUILT, {"nodes": len(project_graph.nodes), "edges": len(project_graph.edges)})
            except Exception as e:
                self.log_info(f"Repository analysis failed gracefully: {str(e)}")
                repo_path = None

        analysis_context = {
            **input_data,
            "repo_path": repo_path,
            "repo_detections": repo_detections,
            "project_graph": project_graph,
            "repo_structure": repo_structure,
            "file_summaries": file_summaries
        }

        # Implementation Intelligence
        if repo_url and repo_path:
            self.log_info("Starting implementation flow analysis...")
            await send_log("[Oracle] Tracing active code logic flows...")
            # This needs a proper StructuredContext object, so we'll create a temporary one
            temp_context = StructuredContext(
                project_graph=project_graph,
                **{k: v for k, v in repo_detections.items()}
            )
            
            # The engine modifies the context in place
            temp_context = ImplementationFlowEngine.analyze_implementation(repo_path, repo_structure, temp_context)
            analysis_context["execution_graph"] = temp_context.execution_graph
            self.emit_event(session_id, EventType.IMPLEMENTATION_FLOW_DETECTED, {"nodes": len(temp_context.execution_graph.nodes)})

        await send_log("[Oracle] Repository analysis complete.", "info")
        self.emit_event(session_id, "AGENT_PROGRESS", {"agent": "Oracle", "status": "complete", "milestone": "Code Analysis"})

        return analysis_context
