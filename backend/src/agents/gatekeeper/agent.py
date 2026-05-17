from src.agents.base import BaseAgent


from typing import Any, Dict
from src.agents.base import BaseAgent
from src.models.events import EventType
from src.services.parsing.pdf_parser import PDFParser
from src.services.parsing.docx_parser import DocxParser
from src.services.parsing.text_cleaner import TextCleaner
from src.services.parsing.entity_extractor import EntityExtractor

class GatekeeperAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="GatekeeperAgent")

    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None) -> Dict[str, Any]:
        """
        Parses documents, extracts entities, and prepares the initial context.
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"Gatekeeper starting for session {session_id}")
        self.emit_event(session_id, EventType.SESSION_STARTED, {"agent": self.name})
        await send_log("[Gatekeeper] Session started. Parsing documents...", "info")

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
            await send_log(f"[Gatekeeper] Document parsed: {report_path}", "info")

        doc_entities = EntityExtractor.extract_entities(doc_text)
        
        initial_context = {
            "repo_url": input_data.get("repo_url"),
            "doc_text": doc_text,
            "doc_entities": doc_entities
        }
        
        await send_log("[Gatekeeper] Initial context prepared.", "info")
        self.emit_event(session_id, "AGENT_PROGRESS", {"agent": "Gatekeeper", "status": "complete", "milestone": "Initial Processing"})

        return initial_context
