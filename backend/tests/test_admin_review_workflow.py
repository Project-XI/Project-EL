import pytest
from datetime import datetime, timezone
from backend.src.services.admin_review_workflow import (
    AdminReviewWorkflow,
    ReviewConflict,
)
from backend.src.services.audit_log import AuditLogService
from backend.src.services.identity_history import IdentityHistoryStore


class TestAdminReviewWorkflow:
    def test_flag_conflict_creates_pending_review(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        conflict = workflow.flag_conflict(
            roll_number="R002",
            matched_roll_numbers=["R001"],
            confidence_scores=[0.92],
            session_id="session-1",
        )

        assert isinstance(conflict, ReviewConflict)
        assert conflict.roll_number == "R002"
        assert conflict.matched_roll_numbers == ["R001"]
        assert conflict.status == "pending_review"
        assert conflict.conflict_id is not None
        assert len(conflict.conflict_id) == 12

    def test_get_pending_conflicts(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")
        workflow.flag_conflict("R003", ["R001", "R002"], [0.89, 0.91], "session-2")

        pending = workflow.get_pending_conflicts()

        assert len(pending) == 2

    def test_approve_conflict(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")

        result = workflow.approve_conflict(
            conflict_id=conflict.conflict_id,
            reviewer_id="admin-1",
            reason="Verified as same person",
        )

        assert result is True
        conflict = workflow.get_conflict_by_id(conflict.conflict_id)
        assert conflict.status == "approved"
        assert conflict.reviewer_id == "admin-1"
        assert conflict.review_reason == "Verified as same person"
        assert conflict.review_timestamp is not None

    def test_reject_conflict(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")

        result = workflow.reject_conflict(
            conflict_id=conflict.conflict_id,
            reviewer_id="admin-2",
            reason="Different person detected",
        )

        assert result is True
        conflict = workflow.get_conflict_by_id(conflict.conflict_id)
        assert conflict.status == "rejected"
        assert conflict.reviewer_id == "admin-2"

    def test_approve_nonexistent_conflict(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        result = workflow.approve_conflict("nonexistent", "admin-1", "reason")

        assert result is False

    def test_get_conflict_details(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())
        history = IdentityHistoryStore()
        history.add_record("R001", [0.1, 0.2, 0.3], "session-old")

        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=history)
        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")

        details = workflow.get_conflict_details(conflict.conflict_id)

        assert details is not None
        assert "conflict" in details
        assert "prior_embeddings" in details
        assert "new_embedding_history" in details
        assert details["conflict"]["conflict_id"] == conflict.conflict_id

    def test_get_override_actions(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        conflict1 = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")
        conflict2 = workflow.flag_conflict("R003", ["R001"], [0.89], "session-2")
        workflow.approve_conflict(conflict1.conflict_id, "admin-1", "approved")
        workflow.reject_conflict(conflict2.conflict_id, "admin-2", "rejected")

        actions = workflow.get_override_actions()

        assert len(actions) == 2
        assert any(a["status"] == "approved" for a in actions)
        assert any(a["status"] == "rejected" for a in actions)

    def test_audit_log_records_admin_override(self):
        audit_log = AuditLogService()
        workflow = AdminReviewWorkflow(audit_log=audit_log, identity_history=IdentityHistoryStore())

        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")
        workflow.approve_conflict(conflict.conflict_id, "admin-1", "approved")

        override_events = audit_log.get_events_by_type("admin_override")
        assert len(override_events) == 1
        assert override_events[0]["payload"]["approved"] is True
        assert override_events[0]["payload"]["reviewer_id"] == "admin-1"

    def test_audit_log_records_examination_access_on_approve(self):
        audit_log = AuditLogService()
        workflow = AdminReviewWorkflow(audit_log=audit_log, identity_history=IdentityHistoryStore())

        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")
        workflow.approve_conflict(conflict.conflict_id, "admin-1", "approved")

        access_events = audit_log.get_events_by_type("examination_access")
        approved_events = [e for e in access_events if e["payload"]["granted"] is True]
        assert len(approved_events) >= 1

    def test_audit_log_records_examination_access_on_reject(self):
        audit_log = AuditLogService()
        workflow = AdminReviewWorkflow(audit_log=audit_log, identity_history=IdentityHistoryStore())

        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")
        workflow.reject_conflict(conflict.conflict_id, "admin-1", "rejected")

        access_events = audit_log.get_events_by_type("examination_access")
        denied_events = [e for e in access_events if e["payload"]["granted"] is False]
        assert len(denied_events) >= 1

    def test_clear_resolved(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        conflict1 = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")
        conflict2 = workflow.flag_conflict("R003", ["R001"], [0.89], "session-2")
        workflow.approve_conflict(conflict1.conflict_id, "admin-1", "approved")

        workflow.clear_resolved()

        assert len(workflow.get_pending_conflicts()) == 1
        assert workflow.get_conflict_by_id(conflict2.conflict_id) is not None

    def test_get_conflict_by_id(self):
        workflow = AdminReviewWorkflow(audit_log=AuditLogService(), identity_history=IdentityHistoryStore())

        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "session-1")

        found = workflow.get_conflict_by_id(conflict.conflict_id)
        not_found = workflow.get_conflict_by_id("nonexistent")

        assert found is conflict
        assert not_found is None

    def test_full_admin_review_flow(self):
        audit_log = AuditLogService()
        history = IdentityHistoryStore()
        history.add_record("R001", [0.1, 0.2, 0.3], "exam-1")

        workflow = AdminReviewWorkflow(audit_log=audit_log, identity_history=history)

        conflict = workflow.flag_conflict("R002", ["R001"], [0.92], "exam-2")
        assert conflict.status == "pending_review"

        pending = workflow.get_pending_conflicts()
        assert len(pending) == 1

        details = workflow.get_conflict_details(conflict.conflict_id)
        assert details is not None
        assert "prior_embeddings" in details

        result = workflow.approve_conflict(conflict.conflict_id, "admin-1", "Same person verified")
        assert result is True

        override_log = workflow.get_override_actions()
        assert len(override_log) == 1
        assert override_log[0]["status"] == "approved"