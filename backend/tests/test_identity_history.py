import pytest
from datetime import datetime, timezone
from backend.src.services.identity_history import (
    IdentityHistoryStore,
    IdentityRecord,
)


class TestIdentityHistoryStore:
    def test_add_record_stores_successfully(self):
        store = IdentityHistoryStore()
        embedding = [0.1, 0.2, 0.3]
        
        record = store.add_record(
            roll_number="R001",
            embedding=embedding,
            session_id="session-1",
        )
        
        assert isinstance(record, IdentityRecord)
        assert record.roll_number == "R001"
        assert record.session_id == "session-1"
        assert store.count() == 1

    def test_get_history_for_roll(self):
        store = IdentityHistoryStore()
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.2, 0.3, 0.4]
        
        store.add_record("R001", embedding1, "session-1")
        store.add_record("R001", embedding2, "session-2")
        store.add_record("R002", embedding1, "session-3")
        
        history = store.get_history_for_roll("R001")
        
        assert len(history) == 2
        assert all(r.roll_number == "R001" for r in history)

    def test_get_record_by_id(self):
        store = IdentityHistoryStore()
        record = store.add_record("R001", [0.1, 0.2, 0.3], "session-1")
        
        found = store.get_record(record.record_id)
        
        assert found == record
        assert store.get_record("nonexistent") is None

    def test_get_sessions_for_roll(self):
        store = IdentityHistoryStore()
        store.add_record("R001", [0.1, 0.2, 0.3], "session-1")
        store.add_record("R001", [0.2, 0.3, 0.4], "session-2")
        store.add_record("R001", [0.3, 0.4, 0.5], "session-3")
        
        sessions = store.get_sessions_for_roll("R001")
        
        assert len(sessions) == 3
        assert "session-1" in sessions
        assert "session-2" in sessions
        assert "session-3" in sessions

    def test_get_records_by_session(self):
        store = IdentityHistoryStore()
        store.add_record("R001", [0.1], "session-1")
        store.add_record("R002", [0.2], "session-1")
        store.add_record("R003", [0.3], "session-2")
        
        records = store.get_records_by_session("session-1")
        
        assert len(records) == 2
        assert all(r.session_id == "session-1" for r in records)

    def test_get_verification_events(self):
        store = IdentityHistoryStore()
        ts1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2024, 1, 2, 11, 0, 0, tzinfo=timezone.utc)
        
        store.add_record("R001", [0.1], "session-1", ts1, "verified", 0.95)
        store.add_record("R001", [0.2], "session-2", ts2, "mismatch", 0.45)
        
        events = store.get_verification_events("R001")
        
        assert len(events) == 2
        assert events[0]["session_id"] == "session-1"
        assert events[1]["verification_result"] == "mismatch"

    def test_get_verification_events_all_rolls(self):
        store = IdentityHistoryStore()
        store.add_record("R001", [0.1], "session-1")
        store.add_record("R002", [0.2], "session-2")
        
        events = store.get_verification_events()
        
        assert len(events) == 2

    def test_embedding_hash_deterministic(self):
        store = IdentityHistoryStore()
        embedding = [0.1, 0.2, 0.3]
        
        hash1 = store._hash_embedding(embedding)
        hash2 = store._hash_embedding(embedding)
        
        assert hash1 == hash2

    def test_record_id_deterministic(self):
        store = IdentityHistoryStore()
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        id1 = store._generate_record_id("R001", "session-1", ts)
        id2 = store._generate_record_id("R001", "session-1", ts)
        
        assert id1 == id2

    def test_has_embedding(self):
        store = IdentityHistoryStore()
        record = store.add_record("R001", [0.1, 0.2, 0.3], "session-1")
        
        assert store.has_embedding(record.embedding_hash)
        assert not store.has_embedding("nonexistent_hash")

    def test_identity_record_to_dict(self):
        store = IdentityHistoryStore()
        record = store.add_record("R001", [0.1], "session-1")
        
        d = record.to_dict()
        
        assert "record_id" in d
        assert "roll_number" in d
        assert "embedding_hash" in d
        assert "session_id" in d
        assert "exam_timestamp" in d
        assert d["roll_number"] == "R001"

    def test_full_history_flow(self):
        store = IdentityHistoryStore()
        
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.4, 0.5, 0.6]
        embedding3 = [0.7, 0.8, 0.9]
        
        store.add_record("R001", embedding1, "exam-1", datetime.now(timezone.utc), "verified", 0.95)
        store.add_record("R001", embedding2, "exam-2", datetime.now(timezone.utc), "verified", 0.92)
        store.add_record("R002", embedding3, "exam-3", datetime.now(timezone.utc), "verified", 0.88)
        
        r001_history = store.get_history_for_roll("R001")
        assert len(r001_history) == 2
        
        all_records = store.get_all_records()
        assert len(all_records) == 3
        
        sessions = store.get_sessions_for_roll("R001")
        assert len(sessions) == 2
        
        events = store.get_verification_events("R001")
        assert len(events) == 2

    def test_clear(self):
        store = IdentityHistoryStore()
        store.add_record("R001", [0.1], "session-1")
        store.clear()
        
        assert store.count() == 0
        assert store.get_history_for_roll("R001") == []