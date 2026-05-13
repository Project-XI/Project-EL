import os
from typing import Any, Dict, List, Optional
from .base import BaseAgent
from ..models.events import EventType
from ..models.context import StructuredContext, EvidenceModel, ProjectGraph
from ..services.parsing.pdf_parser import PDFParser
from ..services.parsing.docx_parser import DocxParser
from ..services.parsing.text_cleaner import TextCleaner
from ..services.parsing.entity_extractor import EntityExtractor
from ..services.github.repo_cloner import RepoCloner
from ..services.github.structure_analyzer import StructureAnalyzer
from ..services.github.tech_detector import TechDetector
from ..services.github.file_summarizer import FileSummarizer
from ..services.github.project_graph_builder import ProjectGraphBuilder
from ..services.llm import LLMService

class OracleAgent(BaseAgent):
    def __init__(self, prompt_version: str = "v1"):
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
            target_dir = "./backend/data/cloned_repos"
            repo_path = RepoCloner.clone(repo_url, target_dir)
            if repo_path:
                self.emit_event(session_id, EventType.REPO_CLONED, {"url": repo_url})
                
                repo_structure = StructureAnalyzer.analyze(repo_path)
                self.emit_event(session_id, EventType.STRUCTURE_ANALYZED, {"path": repo_path})
                
                repo_detections = TechDetector.detect_from_files(repo_path, repo_structure)
                self.emit_event(session_id, EventType.TECH_STACK_DETECTED, {"count": len(repo_detections)})
                
                file_summaries = FileSummarizer.summarize_structure(repo_structure)
                
                project_graph = ProjectGraphBuilder.build(repo_detections, repo_structure)
                self.emit_event(session_id, EventType.PROJECT_GRAPH_BUILT, {"nodes": len(project_graph.nodes)})

        # 4. Hybrid Synthesis (LLM Phase)
        # In a real implementation, we would load the prompt files and call self.llm_service
        self.log_info("Synthesizing context using hybrid model...")
        
        # Placeholder for LLM synthesis result
        # context = await self.synthesize_with_llm(...)
        
        # Mocking the synthesis for the first working version
        mock_context = self._create_mock_context(doc_entities, repo_detections, project_graph)
        
        self.emit_event(session_id, EventType.CONTEXT_READY, {"project_name": mock_context.project_name.value})
        
        return mock_context

    def _create_mock_context(self, doc_entities, repo_detections, project_graph) -> StructuredContext:
        """Helper to create a structured context from findings."""
        return StructuredContext(
            project_name=EvidenceModel(value="TWELVE Viva Platform", confidence=0.9, evidence=["Found in document title"]),
            project_type=EvidenceModel(value="Web Application", confidence=0.8, evidence=["Detected frontend and backend frameworks"]),
            frontend_framework=repo_detections.get("frontend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            backend_framework=repo_detections.get("backend_framework", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            database_used=repo_detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            authentication_system=repo_detections.get("authentication_system", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])),
            architecture_pattern=EvidenceModel(value="MERN Stack", confidence=0.9, evidence=["Evidence of React, Node, and MongoDB"]),
            algorithms_detected=doc_entities.get("algorithms", []),
            external_apis_used=doc_entities.get("apis", []),
            key_modules=[EvidenceModel(value=s["file"], confidence=0.7, evidence=[s["summary"]]) for s in []],
            possible_viva_topics=["JWT Authentication Flow", "React Component Lifecycle", "MongoDB Schema Design"],
            project_graph=project_graph
        )
