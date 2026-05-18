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
from src.services.intelligence.context_enrichment_engine import ContextEnrichmentEngine
from src.services.intelligence.implementation_quality_analyzer import ImplementationQualityAnalyzer
from src.services.intelligence.failure_path_intelligence_engine import FailurePathIntelligenceEngine
from src.services.intelligence.context_aware_tradeoff_engine import ContextAwareTradeoffEngine
from src.services.intelligence.senior_engineer_viva_generator import SeniorEngineerVivaGenerator
from src.services.intelligence.architecture_quality_scorer import ArchitectureQualityScorer

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

        # ===== NEW: Context Enrichment Layer =====
        await send_log("[Oracle] Enriching analysis context...", "info")
        context_enrichment = {}
        if repo_path:
            context_enrichment = ContextEnrichmentEngine.enrich_context(repo_path, repo_structure)
            self.emit_event(session_id, "CONTEXT_ENRICHED", {
                "project_purpose": context_enrichment.get("project_purpose", {}).get("value", "Unknown"),
                "operational_env": context_enrichment.get("operational_environment", {}).get("value", "Unknown"),
                "infrastructure_maturity": context_enrichment.get("infrastructure_maturity", {}).get("value", "Unknown"),
            })

        # ===== NEW: Implementation Quality Analysis =====
        await send_log("[Oracle] Analyzing implementation quality...", "info")
        quality_analysis = {}
        if repo_path:
            quality_analysis = ImplementationQualityAnalyzer.analyze_implementation_quality(repo_path, repo_structure)
            self.emit_event(session_id, "QUALITY_ANALYSIS_COMPLETE", {
                "dimensions_analyzed": len(quality_analysis),
                "top_strength": max(quality_analysis.items(), key=lambda x: x[1].confidence, default=("N/A", EvidenceModel(value="", confidence=0, evidence=[])))[0],
            })

        # ===== NEW: Architecture Inference & Old Logic =====
        await send_log("[Oracle] Running explainability engine...", "info")
        arch_inference = ArchitectureInferenceEngine.infer_architecture(project_graph, repo_detections)
        
        # Old template-based reasoning (kept for backward compatibility)
        template_reasoning = ReasoningInferenceEngine.infer_reasoning(repo_detections)
        template_tradeoffs = ReasoningInferenceEngine.infer_tradeoffs(repo_detections)

        # ===== NEW: Context-Aware Tradeoff Reasoning =====
        await send_log("[Oracle] Generating context-aware tradeoff analysis...", "info")
        context_aware_reasoning = []
        context_aware_tradeoffs = []
        if repo_path and context_enrichment:
            # First, analyze failures to inform tradeoff reasoning
            failure_analysis = FailurePathIntelligenceEngine.analyze_failure_paths(
                repo_path, repo_detections, quality_analysis, context_enrichment
            )
            self.emit_event(session_id, "FAILURE_PATHS_ANALYZED", {
                "scenarios_analyzed": len(failure_analysis),
            })
            
            # Generate context-aware reasoning
            context_aware_reasoning = ContextAwareTradeoffEngine.generate_context_aware_reasoning(
                repo_detections, quality_analysis, context_enrichment, failure_analysis
            )
            
            # Generate context-aware tradeoffs
            context_aware_tradeoffs = ContextAwareTradeoffEngine.generate_tradeoff_analysis(
                repo_detections, quality_analysis, context_enrichment, failure_analysis
            )
        else:
            failure_analysis = {}

        # ===== NEW: Senior Engineer Viva Generation =====
        await send_log("[Oracle] Generating senior-engineer viva targets...", "info")
        senior_viva_targets = []
        if repo_path and context_enrichment and quality_analysis:
            senior_viva_targets = SeniorEngineerVivaGenerator.generate_viva_targets(
                repo_detections,
                quality_analysis,
                context_enrichment,
                failure_analysis,
                context_aware_tradeoffs
            )
            self.emit_event(session_id, "SENIOR_VIVA_GENERATED", {
                "viva_target_count": len(senior_viva_targets),
            })

        # ===== NEW: Architecture Quality Scoring =====
        await send_log("[Oracle] Scoring architecture quality...", "info")
        quality_score = {}
        if repo_path and quality_analysis and context_enrichment:
            quality_score = ArchitectureQualityScorer.score_architecture_quality(
                quality_analysis,
                context_enrichment,
                failure_analysis,
                repo_detections
            )
            self.emit_event(session_id, "QUALITY_SCORE_COMPUTED", {
                "overall_score": quality_score.get("overall_score", 0),
                "overall_grade": quality_score.get("overall_grade", "Unknown"),
            })

        # Old viva generation (kept for backward compatibility)
        await send_log("[Oracle] Generating viva intelligence...", "info")
        viva_targets = VivaIntelligenceEngine.generate_targets(repo_detections, arch_inference)
        inconsistencies = VivaIntelligenceEngine.detect_inconsistencies(doc_text, repo_detections)
        complexity_mismatch = VivaIntelligenceEngine.detect_complexity_mismatch(arch_inference, repo_detections)

        # 4. Final Context Assembly
        context = StructuredContext(
            project_name=EvidenceModel(value="Project TWELVE", confidence=0.9, evidence=["Inferred from repo/docs"]),
            project_type=EvidenceModel(value="Intelligence System", confidence=0.8, evidence=["Technical analysis patterns"]),
            frontend_framework=repo_detections.get("frontend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            backend_framework=repo_detections.get("backend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            database_used=repo_detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            authentication_system=repo_detections.get("authentication_system", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            architecture_pattern=arch_inference,
            project_graph=project_graph,
            implementation_reasoning=context_aware_reasoning if context_aware_reasoning else template_reasoning,
            tradeoff_analysis=context_aware_tradeoffs if context_aware_tradeoffs else template_tradeoffs,
            viva_intelligence_targets=senior_viva_targets if senior_viva_targets else viva_targets,
            inconsistencies=inconsistencies,
            complexity_mismatch=complexity_mismatch
        )
        
        # Attach quality analysis and score to context
        context.quality_analysis = quality_analysis
        context.quality_score = quality_score
        context.context_enrichment = context_enrichment
        context.failure_analysis = failure_analysis

        # 5. Implementation Intelligence Phase
        if repo_url and repo_path:
            self.log_info("Starting implementation flow analysis...")
            await send_log("[Oracle] Tracing active code logic flows...")
            context = ImplementationFlowEngine.analyze_implementation(repo_path, repo_structure, context)
            self.emit_event(session_id, EventType.IMPLEMENTATION_FLOW_DETECTED, {"nodes": len(context.execution_graph.nodes)})

        self.emit_event(session_id, "AGENT_PROGRESS", {"agent": "Oracle", "status": "complete", "milestone": "Submission Intelligence"})
        await send_log("[Oracle] Submission intelligence complete.", "success")
        
        return context

