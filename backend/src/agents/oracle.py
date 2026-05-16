import os
from typing import Any, Dict, List, Optional
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
from src.services.intelligence.architecture_inference_engine import ArchitectureInferenceEngine
from src.services.intelligence.reasoning_inference_engine import ReasoningInferenceEngine
from src.services.intelligence.viva_intelligence_engine import VivaIntelligenceEngine
from src.services.intelligence.graph_confidence_engine import GraphConfidenceEngine
from src.services.intelligence.implementation_flow_engine import ImplementationFlowEngine
from src.services.llm import LLMService

class OracleAgent(BaseAgent):
    def __init__(self, prompt_version: str = "v2"):
        super().__init__(name="ORACLE")
        self.prompt_version = prompt_version
        self.llm_service = LLMService()

    async def process(self, session_id: str, input_data: Dict[str, Any]) -> StructuredContext:
        """
        Orchestrates the project intelligence pipeline.
        input_data: {"report_path": str, "repo_url": str}
        """
        self.log_info(f"Starting analysis for session {session_id}")
        self.emit_event(session_id, EventType.SESSION_STARTED, {"agent": self.name})

        # 1. Document Parsing
        report_path = input_data.get("report_path")
        doc_text = ""
        if report_path:
            self.emit_event(session_id, EventType.FILE_RECEIVED, {"file": report_path})
            if report_path.endswith(".pdf"):
                doc_text = PDFParser.extract_text(report_path)
                self.emit_event(session_id, EventType.PDF_PARSED, {"file": report_path})
            elif report_path.endswith(".docx"):
                doc_text = DocxParser.extract_text(report_path)
                self.emit_event(session_id, EventType.DOCX_PARSED, {"file": report_path})
            
            doc_text = TextCleaner.clean(doc_text)

        # 2. Rule-based Entity Extraction from Document
        doc_entities = EntityExtractor.extract_entities(doc_text)

        # 3. Repository Analysis
        repo_url = input_data.get("repo_url")
        repo_detections = {}
        project_graph = ProjectGraph()
        repo_structure = {}
        file_summaries = []

        if repo_url:
            try:
                target_dir = "./backend/data/cloned_repos"
                repo_path = RepoCloner.clone(repo_url, target_dir)
                if repo_path:
                    self.emit_event(session_id, EventType.REPO_CLONED, {"url": repo_url})
                    
                    repo_structure = StructureAnalyzer.analyze(repo_path)
                    self.emit_event(session_id, EventType.STRUCTURE_ANALYZED, {"path": repo_path})
                    
                    repo_detections = TechDetector.detect_from_files(repo_path, repo_structure)
                    self.emit_event(session_id, EventType.TECH_STACK_DETECTED, {"count": len(repo_detections)})
                    
                    file_summaries = FileSummarizer.summarize_structure(repo_structure)
                    
                    # Structural Intelligence
                    project_graph = ProjectRelationshipEngine.infer_relationships(repo_path, repo_detections, repo_structure)
                    project_graph = GraphConfidenceEngine.refine_scores(project_graph)
                    self.emit_event(session_id, EventType.PROJECT_GRAPH_BUILT, {"nodes": len(project_graph.nodes), "edges": len(project_graph.edges)})
            except Exception as e:
                self.log_info(f"Repository analysis failed gracefully: {str(e)}")
                # We continue with whatever doc_text we have
                repo_path = None

        # 4. Intelligence Synthesis
        arch_inference = ArchitectureInferenceEngine.infer_architecture(project_graph, repo_detections)
        reasoning = ReasoningInferenceEngine.infer_reasoning(repo_detections)
        tradeoffs = ReasoningInferenceEngine.infer_tradeoffs(repo_detections)
        viva_targets = VivaIntelligenceEngine.generate_targets(repo_detections, arch_inference)
        inconsistencies = VivaIntelligenceEngine.detect_inconsistencies(doc_text, repo_detections)
        complexity_mismatch = VivaIntelligenceEngine.detect_complexity_mismatch(arch_inference, repo_detections)

        # Final Synthesis Context
        context = StructuredContext(
            project_name=EvidenceModel(value="Project TWELVE", confidence=0.9, evidence=["Inferred from repo/docs"]),
            project_type=EvidenceModel(value="Intelligence System", confidence=0.8, evidence=["Technical analysis patterns"]),
            frontend_framework=repo_detections.get("frontend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            backend_framework=repo_detections.get("backend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            database_used=repo_detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            authentication_system=repo_detections.get("authentication_system", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            architecture_pattern=arch_inference,
            project_graph=project_graph,
            implementation_reasoning=reasoning,
            tradeoff_analysis=tradeoffs,
            viva_intelligence_targets=viva_targets,
            inconsistencies=inconsistencies,
            complexity_mismatch=complexity_mismatch
        )

        # 5. NEW: Implementation Intelligence Phase
        if repo_url and repo_path:
            self.log_info("Starting implementation flow analysis...")
            context = ImplementationFlowEngine.analyze_implementation(repo_path, repo_structure, context)
            self.emit_event(session_id, EventType.IMPLEMENTATION_FLOW_DETECTED, {"nodes": len(context.execution_graph.nodes)})

        self.emit_event(session_id, EventType.CONTEXT_READY, {"project_name": context.project_name.value})
        
        return context
