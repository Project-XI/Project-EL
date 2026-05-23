from typing import Any, Dict, Optional, List
from .base import BaseAgent
from ..models.events import EventType
from ..services.face_detection import FaceDetectionService

face_service = FaceDetectionService()

class OnboardingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Onboarding")

    async def process(self, session_id: str, student_data: Dict[str, Any]) -> bool:
        """
        Validates student identity and initializes viva sessions.
        Now includes face embedding comparison for multi-roll-number conflict detection.
        """
        self.log_info(f"Validating identity for student {student_data.get('student_id')}")
        
        face_embedding = student_data.get("face_embedding")
        roll_number = student_data.get("roll_number")
        
        if face_embedding:
            is_valid, conflict_alert, similarity = face_service.verify_identity(
                embedding=face_embedding,
                roll_number=roll_number,
                session_id=session_id,
            )
            
            self.emit_event(
                session_id=session_id,
                event_type=EventType.FACE_EMBEDDING_COMPARED,
                payload={
                    "roll_number": roll_number,
                    "similarity": similarity,
                    "embedding_size": len(face_embedding) if isinstance(face_embedding, list) else 0,
                },
            )
            
            if conflict_alert:
                self.emit_event(
                    session_id=session_id,
                    event_type=EventType.IDENTITY_CONFLICT_DETECTED,
                    payload=conflict_alert.to_dict(),
                )
                
                self.emit_event(
                    session_id=session_id,
                    event_type=EventType.CONFLICT_ALERT_CREATED,
                    payload={
                        "alert_id": conflict_alert.conflict_id,
                        "status": "pending_review",
                    },
                )
                
                self.emit_event(
                    session_id=session_id,
                    event_type=EventType.MANUAL_REVIEW_REQUIRED,
                    payload={
                        "conflict_id": conflict_alert.conflict_id,
                        "new_roll_number": conflict_alert.new_roll_number,
                        "matched_rolls": conflict_alert.matched_roll_numbers,
                    },
                )
                
                can_access, reason = face_service.can_grant_access(roll_number)
                if not can_access:
                    self.emit_event(
                        session_id=session_id,
                        event_type=EventType.ACCESS_DENIED_CONFLICT,
                        payload={
                            "roll_number": roll_number,
                            "reason": reason,
                            "conflict_id": conflict_alert.conflict_id,
                        },
                    )
                    return False
        else:
            is_valid = True
        
        if is_valid:
            self.emit_event(
                session_id=session_id,
                event_type=EventType.IDENTITY_VERIFIED,
                payload={"student_id": student_data.get("student_id")}
            )
            self.emit_event(
                session_id=session_id,
                event_type=EventType.SESSION_STARTED,
                payload={"status": "initialized"}
            )
            
        return is_valid
