import os
from typing import Any, Dict
from src.agents.base import BaseAgent
from src.models.events import EventType
from src.models.context import StructuredContext, EvidenceModel, ProjectGraph
from src.services.parsing.pdf_parser import PDFParser
from src.services.parsing.docx_parser import DocxParser
from src.services.parsing.text_cleaner import TextCleaner
from src.services.parsing.entity_extractor import EntityExtractor
from src.services.github.repo_cloner import RepoCloner
from src.services.github.structure_analyzer import StructureAnalyzer
from src.services.github.tech_detector import TechDetector
from src.services.github.file_summarizer import FileSummarizer
from src.services.intelligence.project_relationship_engine import ProjectRelationshipEngine
from src.services.intelligence.graph_confidence_engine import GraphConfidenceEngine
from src.services.intelligence.implementation_flow_engine import ImplementationFlowEngine
from src.services.intelligence.architecture_inference_engine import ArchitectureInferenceEngine
from src.services.intelligence.reasoning_inference_engine import ReasoningInferenceEngine
from src.services.intelligence.viva_intelligence_engine import VivaIntelligenceEngine
# NEW: Context-aware reasoning engines
from src.services.intelligence.observable_signals_engine import ObservableSignalsEngine
from src.services.intelligence.execution_graph_failure_analyzer import ExecutionGraphFailureAnalyzer
from src.services.intelligence.evidence_grounded_viva_generator import EvidenceGroundedVivaGenerator

class OracleAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="OracleAgent")

    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None) -> StructuredContext:
        """
        Submission Intelligence Agent: Analyzes documents and repositories to build full context.
        
        Enhanced Pipeline:
        AST + Execution Graph + Evidence Extraction
                ↓
        Structured Context Builder
                ↓
        Context-Aware Reasoning Layer
                ↓
        Tradeoff & Failure Analysis
                ↓
        Viva Intelligence Generation + Quality Scoring
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"Oracle starting submission intelligence for session {session_id}")
        self.emit_event(session_id, EventType.SESSION_STARTED, {"agent": self.name})

        # 1. Document Parsing
        report_path = input_data.get("report_path")
        doc_text = ""
        if report_path:
            await send_log(f"[Oracle] Parsing document: {report_path}...", "info")
            self.emit_event(session_id, EventType.FILE_RECEIVED, {"file": report_path})
            if report_path.endswith(".pdf"):
                doc_text = PDFParser.extract_text(report_path)
                self.emit_event(session_id, EventType.PDF_PARSED, {"file": report_path})
            elif report_path.endswith(".docx"):
                doc_text = DocxParser.extract_text(report_path)
                self.emit_event(session_id, EventType.DOCX_PARSED, {"file": report_path})
            doc_text = TextCleaner.clean(doc_text)

        # 2. Repository Analysis
        repo_url = input_data.get("repo_url")
        repo_detections = {}
        project_graph = ProjectGraph()
        repo_structure = {}
        repo_path = None

        if repo_url:
            try:
                target_dir = "./backend/data/cloned_repos"
                repo_name = repo_url.split("/")[-1].replace(".git", "")
                clone_path = os.path.join(target_dir, repo_name)
                
                if os.path.exists(clone_path):
                    await send_log(f"[Oracle] Using cached repository at {clone_path}...")
                    repo_path = clone_path
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
                    
                    await send_log("[Oracle] Building execution graph...")
                    project_graph = ProjectRelationshipEngine.infer_relationships(repo_path, repo_detections, repo_structure)
                    project_graph = GraphConfidenceEngine.refine_scores(project_graph)
                    self.emit_event(session_id, EventType.PROJECT_GRAPH_BUILT, {"nodes": len(project_graph.nodes), "edges": len(project_graph.edges)})
            except Exception as e:
                self.log_info(f"Repository analysis failed gracefully: {str(e)}")
                repo_path = None


        # ===== PHASE 2: Observable Signals Extraction =====
        observable_signals = []
        await send_log("[Oracle] Extracting observable engineering signals...", "info")
        if repo_path:
            observable_signals = ObservableSignalsEngine.extract_signals(repo_path, repo_structure, repo_detections, project_graph)
            self.emit_event(session_id, EventType.AGENT_PROGRESS, {
                "agent": "Oracle",
                "status": "running",
                "milestone": "Observable signals extracted",
                "signal_count": len(observable_signals),
                "critical_signals": len([
                    s for s in observable_signals
                    if getattr(s, "risk_level", None) == "high"
                    or (isinstance(s, dict) and s.get("risk_level") == "high")
                ]),
            })

        # ===== Architecture Inference (AST-based, deterministic) =====
        await send_log("[Oracle] Building architecture model from AST...", "info")
        arch_inference = ArchitectureInferenceEngine.infer_architecture(project_graph, repo_detections)
        
        # Template-based reasoning (preserved for backward compatibility)
        template_reasoning = ReasoningInferenceEngine.infer_reasoning(repo_detections)
        template_tradeoffs = ReasoningInferenceEngine.infer_tradeoffs(repo_detections)




        # ===== PHASE 2: Failure Scenario Analysis =====
        failure_scenarios = []
        await send_log("[Oracle] Analyzing failure scenarios through execution graph...", "info")
        if repo_path and observable_signals:
            failure_scenarios = ExecutionGraphFailureAnalyzer.analyze_failure_scenarios(
                repo_path, repo_structure, repo_detections, observable_signals, project_graph
            )
            self.emit_event(session_id, EventType.AGENT_PROGRESS, {
                "agent": "Oracle",
                "status": "running",
                "milestone": "Failure scenarios analyzed",
                "scenario_count": len(failure_scenarios),
                "critical_scenarios": len([
                    s for s in failure_scenarios
                    if getattr(s, "propagation_risk", None) == "critical"
                    or (isinstance(s, dict) and s.get("propagation_risk") == "critical")
                ]),
            })

        # ===== PHASE 2: Evidence-Grounded Viva Generation =====
        grounded_viva_targets = []
        await send_log("[Oracle] Generating code-grounded viva questions...", "info")
        if failure_scenarios and observable_signals:
            grounded_viva_targets = EvidenceGroundedVivaGenerator.generate_questions(
                failure_scenarios, observable_signals, repo_detections, repo_path
            )
            self.emit_event(session_id, EventType.AGENT_PROGRESS, {
                "agent": "Oracle",
                "status": "running",
                "milestone": "Evidence-grounded viva generated",
                "viva_count": len(grounded_viva_targets),
                "difficulty_breakdown": f"hard: {len([v for v in grounded_viva_targets if getattr(v, 'difficulty', None) == 'hard'])}, "
                                       f"medium: {len([v for v in grounded_viva_targets if getattr(v, 'difficulty', None) == 'medium'])}, "
                                       f"foundational: {len([v for v in grounded_viva_targets if getattr(v, 'difficulty', None) == 'foundational'])}",
            })

        # Fallback viva generation (backward compatibility)
        await send_log("[Oracle] Generating viva intelligence...", "info")
        viva_targets = VivaIntelligenceEngine.generate_targets(repo_detections, arch_inference)
        inconsistencies = VivaIntelligenceEngine.detect_inconsistencies(doc_text, repo_detections)
        complexity_mismatch = VivaIntelligenceEngine.detect_complexity_mismatch(arch_inference, repo_detections)

        # 4. Final Context Assembly
        # Use evidence-grounded viva if available, else fallback to template-based
        final_viva_targets = grounded_viva_targets if grounded_viva_targets else viva_targets
        
        context = StructuredContext(
            project_name=EvidenceModel(value="Project TWELVE", confidence=0.9, evidence=["Inferred from repo/docs"]),
            project_type=EvidenceModel(value="Intelligence System", confidence=0.8, evidence=["Technical analysis patterns"]),
            frontend_framework=repo_detections.get("frontend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            backend_framework=repo_detections.get("backend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            database_used=repo_detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            authentication_system=repo_detections.get("authentication_system", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            architecture_pattern=arch_inference,
            project_graph=project_graph,
            implementation_reasoning=template_reasoning,
            tradeoff_analysis=template_tradeoffs,
            viva_intelligence_targets=final_viva_targets,
            inconsistencies=inconsistencies,
            complexity_mismatch=complexity_mismatch
        )
        
        # 5. Implementation Intelligence Phase
        if repo_url and repo_path:
            self.log_info("Starting implementation flow analysis...")
            await send_log("[Oracle] Tracing active code logic flows...")
            context = ImplementationFlowEngine.analyze_implementation(repo_path, repo_structure, context)
            self.emit_event(session_id, EventType.IMPLEMENTATION_FLOW_DETECTED, {"nodes": len(context.execution_graph.nodes)})

        self.emit_event(session_id, EventType.AGENT_PROGRESS, {"agent": "Oracle", "status": "complete", "milestone": "Submission Intelligence"})
        await send_log("[Oracle] Submission intelligence complete.", "success")
        
        return context

