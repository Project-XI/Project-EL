import pytest
import numpy as np
from backend.src.services.face_detection import (
    FaceDetectionService,
    FaceEmbedding,
    ConflictAlert,
    CONFIDENCE_THRESHOLD,
)


def generate_embedding(base: float = 0.5, noise: float = 0.1) -> List[float]:
    np.random.seed(42)
    return [base + np.random.randn() * noise for _ in range(512)]


def create_similar_embedding(base_embedding: List[float], similarity: float) -> List[float]:
    base = np.array(base_embedding)
    target_norm = np.linalg.norm(base)
    
    np.random.seed(123)
    noise = np.random.randn(len(base)) * 0.1
    similar = base * similarity + noise
    similar = similar / np.linalg.norm(similar) * target_norm
    return similar.tolist()


class TestFaceDetectionService:
    def test_add_embedding(self):
        service = FaceDetectionService()
        emb = generate_embedding()
        result = service.add_embedding(emb, "R001", "Alice")
        
        assert isinstance(result, FaceEmbedding)
        assert result.roll_number == "R001"
        assert result.student_name == "Alice"
        assert len(service.embeddings) == 1

    def test_verify_identity_new_student(self):
        service = FaceDetectionService(threshold=0.9)
        emb1 = generate_embedding(base=1.0)
        emb2 = generate_embedding(base=0.0)
        
        is_valid1, alert1, sim1 = service.verify_identity(emb1, "R001")
        is_valid2, alert2, sim2 = service.verify_identity(emb2, "R002")
        
        assert is_valid1 is True
        assert alert1 is None
        assert len(service.embeddings) == 2

    def test_verify_identity_conflict_detection(self):
        service = FaceDetectionService(threshold=0.85)
        emb1 = generate_embedding(base=0.5)
        emb2 = create_similar_embedding(emb1, 0.92)
        
        service.verify_identity(emb1, "R001")
        is_valid, alert, similarity = service.verify_identity(emb2, "R002")
        
        assert is_valid is False
        assert alert is not None
        assert alert.new_roll_number == "R002"
        assert "R001" in alert.matched_roll_numbers
        assert similarity >= 0.85

    def test_conflict_alert_structure(self):
        service = FaceDetectionService()
        emb1 = generate_embedding(base=0.5)
        emb2 = create_similar_embedding(emb1, 0.95)
        
        service.verify_identity(emb1, "R001")
        _, alert, _ = service.verify_identity(emb2, "R002")
        
        assert isinstance(alert, ConflictAlert)
        assert isinstance(alert.conflict_id, str)
        assert len(alert.conflict_id) == 12
        assert alert.status == "pending_review"

    def test_can_grant_access_no_conflicts(self):
        service = FaceDetectionService()
        emb = generate_embedding()
        
        service.verify_identity(emb, "R001")
        can_access, reason = service.can_grant_access("R001")
        
        assert can_access is True
        assert reason is None

    def test_can_grant_access_with_conflict(self):
        service = FaceDetectionService()
        emb1 = generate_embedding(base=0.5)
        emb2 = create_similar_embedding(emb1, 0.92)
        
        service.verify_identity(emb1, "R001")
        _, alert, _ = service.verify_identity(emb2, "R002")
        
        can_access_new, reason = service.can_grant_access("R002")
        can_access_existing, _ = service.can_grant_access("R001")
        
        assert can_access_new is False
        assert "conflict" in reason.lower()
        assert alert.status == "pending_review"

    def test_resolve_alert(self):
        service = FaceDetectionService()
        emb1 = generate_embedding(base=0.5)
        emb2 = create_similar_embedding(emb1, 0.92)
        
        service.verify_identity(emb1, "R001")
        _, alert, _ = service.verify_identity(emb2, "R002")
        
        result = service.resolve_alert(alert.conflict_id, approved=True)
        
        assert result is True
        assert alert.status == "approved"

    def test_get_suspicious_identities(self):
        service = FaceDetectionService()
        emb1 = generate_embedding(base=0.5)
        emb2 = create_similar_embedding(emb1, 0.92)
        emb3 = create_similar_embedding(emb1, 0.90)
        
        service.verify_identity(emb1, "R001")
        service.verify_identity(emb2, "R002")
        _, alert, _ = service.verify_identity(emb3, "R003")
        
        suspicious = service.get_suspicious_identities()
        
        assert len(suspicious) > 0
        all_rolls = [roll for rolls in suspicious.values() for roll in rolls]
        assert "R001" in all_rolls

    def test_get_pending_alerts(self):
        service = FaceDetectionService()
        emb1 = generate_embedding(base=0.5)
        emb2 = create_similar_embedding(emb1, 0.92)
        
        service.verify_identity(emb1, "R001")
        _, alert, _ = service.verify_identity(emb2, "R002")
        
        service.resolve_alert(alert.conflict_id, approved=True)
        
        pending = service.get_pending_alerts()
        assert len(pending) == 0

    def test_cosine_similarity_identical(self):
        service = FaceDetectionService()
        vec = np.random.randn(512)
        vec = vec / np.linalg.norm(vec)
        
        similarity = service._cosine_similarity(vec, vec.copy())
        assert abs(similarity - 1.0) < 0.0001

    def test_cosine_similarity_orthogonal(self):
        service = FaceDetectionService()
        vec1 = np.array([1] + [0] * 511)
        vec2 = np.array([0] + [1] + [0] * 510)
        
        similarity = service._cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.0001

    def test_multi_roll_number_conflict(self):
        service = FaceDetectionService()
        emb1 = generate_embedding(base=0.5)
        emb2 = create_similar_embedding(emb1, 0.93)
        emb3 = create_similar_embedding(emb1, 0.91)
        
        service.verify_identity(emb1, "R001")
        service.verify_identity(emb2, "R002")
        is_valid, alert, _ = service.verify_identity(emb3, "R003")
        
        assert is_valid is False
        assert len(alert.matched_roll_numbers) >= 1