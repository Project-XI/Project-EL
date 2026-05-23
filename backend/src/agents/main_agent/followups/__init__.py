"""
followups/__init__.py
─────────────────────
Public surface of the Follow-Up Question Strategy Engine package.
"""

from .strategy_engine import StrategyEngine, StrategyDecision, FollowUpCandidate
from .weak_answer_detector import WeakAnswerDetector, WeaknessSignal

__all__ = [
    "StrategyEngine",
    "StrategyDecision",
    "FollowUpCandidate",
    "WeakAnswerDetector",
    "WeaknessSignal",
]
