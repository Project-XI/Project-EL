import pytest
from backend.src.services.audit_log import (
    AuditLogService,
    AuditEvent,
)


class TestAuditLogService:
    def test_log_verification_attempt(self):
        log = AuditLogService()
        event = log.log_verification_attempt(
            roll_number="R001",
            session_id="session-1",
            capture_info={"width": 640, "height": 480},
            result="verified",
            confidence=0.95,
        )
        
        assert isinstance(event, AuditEvent)
        assert event.event_type == "verification_attempt"
        assert event.roll_number == "R001"
        assert event.payload["result"] == "verified"
        assert event.payload["confidence"] == 0.95
        assert log.count() == 1

    def test_log_match(self):
        log = AuditLogService()
        event = log.log_match(
            roll_number="R001",
            session_id="session-1",
            similarity=0.92,
            confidence=0.89,
        )
        
        assert event.event_type == "face_match"
        assert event.payload["similarity"] == 0.92
        assert event.payload["confidence"] == 0.89

    def test_log_mismatch(self):
        log = AuditLogService()
        event = log.log_mismatch(
            roll_number="R001",
            session_id="session-1",
            similarity=0.35,
            confidence=0.25,
            threshold=0.85,
        )
        
        assert event.event_type == "face_mismatch"
        assert event.payload["threshold"] == 0.85

    def test_log_suspicious_event(self):
        log = AuditLogService()
        event = log.log_suspicious_event(
            roll_number="R002",
            session_id="session-2",
            reason="Same face as R001",
            conflict_id="abc123",
            matched_rolls=["R001"],
        )
        
        assert event.event_type == "suspicious_identity"
        assert event.payload["conflict_id"] == "abc123"
        assert "R001" in event.payload["matched_rolls"]

    def test_log_admin_override(self):
        log = AuditLogService()
        event = log.log_admin_override(
            roll_number="R001",
            session_id="session-1",
            conflict_id="abc123",
            reviewer_id="admin-1",
            approved=True,
            reason="Verified as legitimate",
        )
        
        assert event.event_type == "admin_override"
        assert event.payload["reviewer_id"] == "admin-1"
        assert event.payload["approved"] is True

    def test_log_examination_access(self):
        log = AuditLogService()
        event = log.log_examination_access(
            roll_number="R001",
            session_id="session-1",
            granted=True,
            reason=None,
        )
        
        assert event.event_type == "examination_access"
        assert event.payload["granted"] is True

    def test_get_timeline_all(self):
        log = AuditLogService()
        log.log_verification_attempt("R001", "session-1", {}, "verified", 0.95)
        log.log_match("R002", "session-2", 0.92, 0.89)
        
        timeline = log.get_timeline()
        
        assert len(timeline) == 2
        assert timeline[0]["event_type"] == "verification_attempt"
        assert timeline[1]["event_type"] == "face_match"

    def test_get_timeline_filter_by_roll(self):
        log = AuditLogService()
        log.log_verification_attempt("R001", "session-1", {}, "verified", 0.95)
        log.log_verification_attempt("R002", "session-2", {}, "verified", 0.90)
        
        timeline = log.get_timeline(roll_number="R001")
        
        assert len(timeline) == 1
        assert timeline[0]["roll_number"] == "R001"

    def test_get_events_by_type(self):
        log = AuditLogService()
        log.log_verification_attempt("R001", "session-1", {}, "verified", 0.95)
        log.log_verification_attempt("R002", "session-2", {}, "verified", 0.90)
        log.log_match("R001", "session-1", 0.92, 0.89)
        
        attempts = log.get_events_by_type("verification_attempt")
        
        assert len(attempts) == 2

    def test_get_session_timeline(self):
        log = AuditLogService()
        log.log_verification_attempt("R001", "session-1", {}, "verified", 0.95)
        log.log_match("R001", "session-1", 0.92, 0.89)
        log.log_verification_attempt("R002", "session-2", {}, "verified", 0.90)
        
        timeline = log.get_session_timeline("session-1")
        
        assert len(timeline) == 2

    def test_search(self):
        log = AuditLogService()
        log.log_suspicious_event("R001", "session-1", "Same face as R002", "conflict-1", ["R002"])
        log.log_verification_attempt("R003", "session-3", {}, "verified", 0.95)
        
        results = log.search("conflict")
        
        assert len(results) == 1
        assert "conflict-1" in results[0]["payload"]["conflict_id"]

    def test_audit_event_to_dict(self):
        log = AuditLogService()
        event = log.log_verification_attempt("R001", "session-1", {}, "verified", 0.95)
        
        d = event.to_dict()
        
        assert "event_id" in d
        assert "timestamp" in d
        assert "event_type" in d
        assert "roll_number" in d
        assert "payload" in d

    def test_clear(self):
        log = AuditLogService()
        log.log_verification_attempt("R001", "session-1", {}, "verified", 0.95)
        log.clear()
        
        assert log.count() == 0

    def test_deterministic_event_id(self):
        log = AuditLogService()
        import time
        from datetime import datetime, timezone
        
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        hash1 = log._generate_event_id("R001", "test", ts)
        hash2 = log._generate_event_id("R001", "test", ts)
        
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_full_audit_flow(self):
        log = AuditLogService()
        
        log.log_verification_attempt("R001", "session-1", {"width": 640}, "verified", 0.95)
        log.log_match("R001", "session-1", 0.92, 0.89)
        log.log_examination_access("R001", "session-1", True)
        
        log.log_verification_attempt("R002", "session-2", {"width": 640}, "mismatch", 0.45)
        log.log_mismatch("R002", "session-2", 0.35, 0.25, 0.85)
        log.log_suspicious_event("R002", "session-2", "Shared face", "conflict-1", ["R001"])
        log.log_admin_override("R002", "session-2", "conflict-1", "admin-1", False, "Different person")
        
        full_timeline = log.get_timeline()
        assert len(full_timeline) == 7  # 3 for session-1 + 4 for session-2
        
        session_timeline = log.get_session_timeline("session-1")
        assert len(session_timeline) == 3
        
        session_timeline_2 = log.get_session_timeline("session-2")
        assert len(session_timeline_2) == 4
        
        admin_overrides = log.get_events_by_type("admin_override")
        assert len(admin_overrides) == 1