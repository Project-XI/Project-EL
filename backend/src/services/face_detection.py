from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib

CONFIDENCE_THRESHOLD = 0.85
EMBEDDING_SIZE = 512


@dataclass
class FaceEmbedding:
    embedding: np.ndarray
    roll_number: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    student_name: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class ConflictAlert:
    conflict_id: str
    new_roll_number: str
    matched_roll_numbers: List[str]
    confidence_scores: List[float]
    timestamp: datetime
    status: str = "pending_review"
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "new_roll_number": self.new_roll_number,
            "matched_roll_numbers": self.matched_roll_numbers,
            "confidence_scores": self.confidence_scores,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "session_id": self.session_id,
        }


class FaceDetectionService:
    def __init__(self, threshold: float = CONFIDENCE_THRESHOLD):
        self.threshold = threshold
        self.embeddings: Dict[str, FaceEmbedding] = {}
        self.alerts: List[ConflictAlert] = []

    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        a_norm = self._normalize_embedding(a)
        b_norm = self._normalize_embedding(b)
        return float(np.dot(a_norm, b_norm))

    def _generate_conflict_id(self, roll_numbers: List[str]) -> str:
        sorted_rolls = sorted(roll_numbers)
        raw = f"{datetime.now(timezone.utc).isoformat()}:{','.join(sorted_rolls)}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def add_embedding(
        self,
        embedding: List[float],
        roll_number: str,
        student_name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> FaceEmbedding:
        emb = FaceEmbedding(
            embedding=np.array(embedding),
            roll_number=roll_number,
            student_name=student_name,
            session_id=session_id,
        )
        self.embeddings[roll_number] = emb
        return emb

    def verify_identity(
        self,
        embedding: List[float],
        roll_number: str,
        session_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[ConflictAlert], float]:
        new_embedding = np.array(embedding)
        best_matches: List[Tuple[str, float]] = []

        for existing_roll, existing_emb in self.embeddings.items():
            if existing_roll == roll_number:
                continue
            similarity = self._cosine_similarity(new_embedding, existing_emb.embedding)
            if similarity >= self.threshold:
                best_matches.append((existing_roll, similarity))

        best_matches.sort(key=lambda x: x[1], reverse=True)

        if best_matches:
            conflict_id = self._generate_conflict_id(
                [roll_number] + [r for r, _ in best_matches]
            )
            alert = ConflictAlert(
                conflict_id=conflict_id,
                new_roll_number=roll_number,
                matched_roll_numbers=[r for r, _ in best_matches],
                confidence_scores=[s for _, s in best_matches],
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
            )
            self.alerts.append(alert)
            return False, alert, best_matches[0][1]

        self.add_embedding(embedding, roll_number, session_id=session_id)
        return True, None, 0.0

    def get_conflicts_for_roll(self, roll_number: str) -> List[ConflictAlert]:
        return [
            alert
            for alert in self.alerts
            if roll_number in alert.matched_roll_numbers
            or alert.new_roll_number == roll_number
        ]

    def get_pending_alerts(self) -> List[ConflictAlert]:
        return [alert for alert in self.alerts if alert.status == "pending_review"]

    def resolve_alert(self, conflict_id: str, approved: bool) -> bool:
        for alert in self.alerts:
            if alert.conflict_id == conflict_id:
                alert.status = "approved" if approved else "rejected"
                return True
        return False

    def get_suspicious_identities(self) -> Dict[str, List[str]]:
        suspicious: Dict[str, List[str]] = {}
        for alert in self.alerts:
            if alert.status == "pending_review":
                key = tuple(sorted(set(alert.matched_roll_numbers)))
                if key not in suspicious:
                    suspicious[key] = []
                all_rolls = alert.matched_roll_numbers + [alert.new_roll_number]
                suspicious[key].extend(all_rolls)
        return {k: list(set(v)) for k, v in suspicious.items()}

    def can_grant_access(self, roll_number: str) -> Tuple[bool, Optional[str]]:
        conflicts = self.get_conflicts_for_roll(roll_number)
        for conflict in conflicts:
            if conflict.status == "pending_review":
                return False, f"Identity under review: conflict {conflict.conflict_id}"
        return True, None