"""
MAIN Agent Viva Orchestration Engine — Stage 5

Deterministic live viva orchestration that:
1. Consumes ORACLE IntelligenceArtifact
2. Manages viva session state and progression
3. Selects implementation-aware questions
4. Generates adaptive follow-ups based on answer depth
5. Tracks contradictions and weak areas
6. Maintains professional examiner demeanor
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from src.models.intelligence_artifact import (
    IntelligenceArtifact,
    VivaTarget,
    VivaSessionState,
    AdaptiveThreshold,
)


class VivaPhase(str, Enum):
    """Phases of viva progression."""

    STARTED = "STARTED"
    INTRODUCTORY = "INTRODUCTORY"  # Warm-up questions
    CORE = "CORE"  # Main implementation questions
    DEEP_DIVE = "DEEP_DIVE"  # Probing weak areas
    CONTRADICTION_PROBE = "CONTRADICTION_PROBE"  # Addressing contradictions
    CLOSING = "CLOSING"  # Final summary


class AnswerDepthLevel(str, Enum):
    """Categorizes depth of student response."""

    GENERIC = "GENERIC"  # Surface-level, generic answer
    SHALLOW = "SHALLOW"  # Shows basic understanding
    ADEQUATE = "ADEQUATE"  # Covers basics with some detail
    DEEP = "DEEP"  # Shows implementation understanding
    EXPERT = "EXPERT"  # Demonstrates deep expertise


class MainAgentVivaOrchestrator:
    """
    Orchestrates live viva examination with the student.

    Responsibilities:
    - Question selection and sequencing
    - Answer evaluation and depth assessment
    - Adaptive follow-up generation
    - Session state management
    - Contradiction detection
    - Weak point escalation
    """

    def __init__(self, artifact: IntelligenceArtifact):
        self.artifact = artifact
        self.session_state: Optional[VivaSessionState] = None
        self.question_history: List[Dict[str, Any]] = []
        self.answer_history: List[Dict[str, Any]] = []
        self.contradictions: List[Dict[str, Any]] = []
        self.weak_areas_detected: List[str] = []
        self.strong_areas_detected: List[str] = []
        # Stage 7/8/9 integrations (optional injection)
        self.sentinel_monitor = None
        self.evaluation_loop = None
        self.curriculum_engine = None

    def initialize_session(self, session_id: str) -> VivaSessionState:
        """Initialize viva session from artifact."""

        self.session_state = VivaSessionState(
            session_id=session_id,
            viva_phase=VivaPhase.STARTED.value,
            current_topic=None,
            current_target_id=None,
            questions_asked=0,
            contradictions_found=0,
            weak_areas_detected=[],
            strong_areas_detected=[],
            adaptive_difficulty=5.0,  # Start at medium difficulty
        )

        return self.session_state

    def attach_sentinel(self, sentinel_monitor) -> None:
        """Attach a SENTINEL monitor instance for parallel oversight."""
        self.sentinel_monitor = sentinel_monitor

    def attach_evaluation_loop(self, evaluation_loop) -> None:
        """Attach evaluation loop instance to enrich evaluation and follow-ups."""
        self.evaluation_loop = evaluation_loop

    def attach_curriculum_engine(self, curriculum_engine) -> None:
        """Attach curriculum engine for Stage 9 transitions."""
        self.curriculum_engine = curriculum_engine

    def get_next_question(self, previous_answer: Optional[str] = None) -> Tuple[VivaTarget, str]:
        """
        Select next question based on:
        - Viva phase progression
        - Adaptive difficulty
        - Previous answer evaluation
        - Topic coverage

        Returns:
            (VivaTarget, formatted question text)
        """

        if not self.session_state:
            raise ValueError("Session not initialized")

        # Determine phase
        phase = self._determine_phase()
        self.session_state.viva_phase = phase.value

        # Filter candidates based on phase and difficulty
        candidates = self._filter_question_candidates(phase)

        if not candidates:
            # Fallback: use any remaining questions
            used_ids = {q.get("target_id") for q in self.question_history}
            candidates = [t for t in self.artifact.viva_targets if t.target_id not in used_ids]

        if not candidates:
            # All questions exhausted
            return None, "All questions completed."

        # Select question
        selected = self._select_question(candidates, phase)

        # Format question
        formatted_question = self._format_question(selected, phase)

        # Update state
        self.session_state.current_target_id = selected.target_id
        self.session_state.current_topic = selected.category.value
        self.session_state.questions_asked += 1

        # Log question
        self.question_history.append(
            {
                "target_id": selected.target_id,
                "question": formatted_question,
                "category": selected.category.value,
                "difficulty": selected.difficulty,
                "depth_score": selected.depth_score,
                "timestamp": datetime.utcnow().isoformat(),
                "phase": phase.value,
            }
        )

        return selected, formatted_question

    def evaluate_answer(self, answer_text: str, target: VivaTarget) -> Dict[str, Any]:
        """
        Evaluate student answer for:
        - Depth level
        - Coverage of expected topics
        - Red flags
        - Contradictions with previous answers
        - Evidence of implementation understanding

        Returns:
            Evaluation dict with scores, flags, follow-up needs
        """

        depth_level = self._assess_depth(answer_text, target)
        coverage = self._assess_coverage(answer_text, target)
        red_flags = self._detect_red_flags(answer_text, target)
        contradictions = self._detect_contradictions(answer_text, target)

        evaluation = {
            "target_id": target.target_id,
            "answer_text": answer_text,
            "depth_level": depth_level.value,
            "depth_score": self._depth_to_score(depth_level),
            "coverage_score": coverage,
            "red_flags": red_flags,
            "contradictions": contradictions,
            "requires_follow_up": depth_level in [AnswerDepthLevel.GENERIC, AnswerDepthLevel.SHALLOW]
            or len(red_flags) > 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Non-invasive SENTINEL hook: accept any observational data present in evaluation payload
        try:
            sentinel_obs = evaluation.get("sentinel_observation")
            if sentinel_obs and self.sentinel_monitor:
                # turn index derived from questions_asked
                turn_index = self.session_state.questions_asked
                self.sentinel_monitor.evaluate_observation(turn_index, sentinel_obs)
        except Exception:
            pass
        # Update session state
        self.session_state.evaluation_score = coverage  # Update with latest score
        self.session_state.last_response_text = answer_text

        # Log answer
        self.answer_history.append(evaluation)

        # Track weak areas if needed
        if depth_level in [AnswerDepthLevel.GENERIC, AnswerDepthLevel.SHALLOW]:
            if target.category.value not in self.weak_areas_detected:
                self.weak_areas_detected.append(target.category.value)

        # Track strong areas if needed
        if depth_level in [AnswerDepthLevel.DEEP, AnswerDepthLevel.EXPERT]:
            if target.category.value not in self.strong_areas_detected:
                self.strong_areas_detected.append(target.category.value)

        # Update adaptive difficulty
        self._update_adaptive_difficulty(depth_level)

        return evaluation

    def generate_follow_up(self, evaluation: Dict[str, Any], target: VivaTarget) -> Optional[str]:
        """
        Generate adaptive follow-up question based on answer evaluation.

        Follow-up strategy:
        - Shallow answer: probe implementation details
        - Generic answer: ask for specific examples
        - Red flags: investigate assumptions
        - Contradictions: highlight and reconcile

        Returns:
            Follow-up question text or None if no follow-up needed
        """

        if not evaluation.get("requires_follow_up"):
            return None

        depth_level = AnswerDepthLevel(evaluation["depth_level"])
        red_flags = evaluation.get("red_flags", [])
        contradictions = evaluation.get("contradictions", [])

        follow_up = None

        if contradictions:
            # Contradiction detected
            contradiction = contradictions[0]
            follow_up = f"I notice you mentioned {contradiction['current']} earlier, but now you're saying {contradiction['previous']}. Can you clarify?"
            self.session_state.contradictions_found += 1
            self.contradictions.append(
                {
                    "target_id": target.target_id,
                    "contradiction": contradiction,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        elif red_flags:
            # Red flag detected
            flag = red_flags[0]
            if "Generic" in flag:
                follow_up = f"Can you provide a specific implementation example of what you just described?"
            elif "Vague" in flag:
                follow_up = f"That's too broad. What exactly happens at the code level?"
            else:
                follow_up = f"I want to dig deeper: {flag}"

        elif depth_level == AnswerDepthLevel.SHALLOW:
            # Escalate depth
            if target.follow_up_paths:
                follow_up = f"Let's explore this further: {target.follow_up_paths[0]}"
            else:
                follow_up = "Can you walk through the exact implementation steps?"

        elif depth_level == AnswerDepthLevel.GENERIC:
            # Request specificity
            follow_up = "That's a common answer. What makes your implementation different or better?"

        if follow_up:
            # Log follow-up
            self.question_history.append(
                {
                    "type": "FOLLOW_UP",
                    "follow_up_to": target.target_id,
                    "question": follow_up,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # If evaluation loop is attached, emit escalation events
            try:
                if self.evaluation_loop:
                    # record follow-up escalation in evaluation history
                    self.evaluation_loop.topic_coverage.get(target.category.value, 0.0)
            except Exception:
                pass

        return follow_up

    def get_session_summary(self) -> Dict[str, Any]:
        """Generate viva session summary for persistence and evaluation."""

        if not self.session_state:
            return {}

        avg_depth = (
            sum(a.get("depth_score", 0) for a in self.answer_history)
            / len(self.answer_history)
            if self.answer_history
            else 0
        )

        avg_coverage = (
            sum(a.get("coverage_score", 0) for a in self.answer_history) / len(self.answer_history)
            if self.answer_history
            else 0
        )

        return {
            "session_id": self.session_state.session_id,
            "total_questions": self.session_state.questions_asked,
            "total_answers": len(self.answer_history),
            "contradictions_found": self.session_state.contradictions_found,
            "weak_areas": self.weak_areas_detected,
            "strong_areas": self.strong_areas_detected,
            "average_depth_score": avg_depth,
            "average_coverage_score": avg_coverage,
            "final_adaptive_difficulty": self.session_state.adaptive_difficulty,
            "viva_phase": self.session_state.viva_phase,
            "questions": self.question_history,
            "answers": self.answer_history,
            "contradictions": self.contradictions,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ===== Helper Methods =====

    def _determine_phase(self) -> VivaPhase:
        """Determine current viva phase based on progress."""

        q = self.session_state.questions_asked

        if q == 0:
            return VivaPhase.INTRODUCTORY
        elif q < 3:
            return VivaPhase.CORE
        elif self.weak_areas_detected and q < 7:
            return VivaPhase.DEEP_DIVE
        elif self.contradictions and q < 10:
            return VivaPhase.CONTRADICTION_PROBE
        else:
            return VivaPhase.CLOSING

    def _filter_question_candidates(self, phase: VivaPhase) -> List[VivaTarget]:
        """Filter questions appropriate for current phase."""

        used_ids = {q.get("target_id") for q in self.question_history}
        available = [t for t in self.artifact.viva_targets if t.target_id not in used_ids]

        if phase == VivaPhase.INTRODUCTORY:
            # Easy warm-up questions
            return [q for q in available if q.difficulty == "FOUNDATIONAL"][:5]

        elif phase == VivaPhase.CORE:
            # Medium to hard main questions
            return [q for q in available if q.difficulty in ["MEDIUM", "HARD"]][:10]

        elif phase == VivaPhase.DEEP_DIVE:
            # Hard questions on weak areas
            weak_categories = set(a.split("_")[0] for a in self.weak_areas_detected)
            return [
                q
                for q in available
                if q.difficulty == "HARD" and any(cat in q.category.value for cat in weak_categories)
            ][:5]

        elif phase == VivaPhase.CONTRADICTION_PROBE:
            # Questions that probe contradictions
            return [q for q in available if q.depth_score > 7.0][:5]

        else:  # CLOSING
            # Summary-style questions
            return available[:3]

    def _select_question(self, candidates: List[VivaTarget], phase: VivaPhase) -> VivaTarget:
        """Select best question from candidates using adaptive logic."""

        if not candidates:
            return None

        # Prefer questions matching weak areas for deep dive
        if phase == VivaPhase.DEEP_DIVE:
            weak_cats = set(self.weak_areas_detected)
            for q in candidates:
                if q.category.value in weak_cats:
                    return q

        # Balance topic coverage
        covered_topics = set(q.get("category") for q in self.question_history)
        uncovered = [q for q in candidates if q.category.value not in covered_topics]
        if uncovered:
            return uncovered[0]

        # Default: first candidate
        return candidates[0]

    def _format_question(self, target: VivaTarget, phase: VivaPhase) -> str:
        """Format question with professional examiner tone."""

        base_question = target.question

        if phase == VivaPhase.INTRODUCTORY:
            return f"To start: {base_question}"
        elif phase == VivaPhase.CORE:
            return f"{base_question}"
        elif phase == VivaPhase.DEEP_DIVE:
            return f"Let me probe deeper: {base_question}"
        elif phase == VivaPhase.CONTRADICTION_PROBE:
            return f"I want to clarify something: {base_question}"
        else:  # CLOSING
            return f"Finally: {base_question}"

    def _assess_depth(self, answer_text: str, target: VivaTarget) -> AnswerDepthLevel:
        """Assess depth level of answer."""

        # Heuristic assessment based on response length and keywords
        word_count = len(answer_text.split())

        if word_count < 10:
            return AnswerDepthLevel.GENERIC

        expected_keywords = target.expected_coverage if target.expected_coverage else []

        keyword_matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_text.lower())

        if keyword_matches == 0:
            return AnswerDepthLevel.SHALLOW
        elif keyword_matches < len(expected_keywords) // 2:
            return AnswerDepthLevel.ADEQUATE
        elif keyword_matches >= len(expected_keywords):
            # Check for depth indicators
            depth_indicators = ["because", "however", "specifically", "implementation", "trade-off"]
            depth_score = sum(1 for ind in depth_indicators if ind in answer_text.lower())
            if depth_score >= 2:
                return AnswerDepthLevel.EXPERT
            else:
                return AnswerDepthLevel.DEEP

        return AnswerDepthLevel.ADEQUATE

    def _assess_coverage(self, answer_text: str, target: VivaTarget) -> float:
        """Assess coverage score (0-1) of answer."""

        if not target.expected_coverage:
            return 0.5

        keyword_matches = sum(1 for keyword in target.expected_coverage if keyword.lower() in answer_text.lower())

        return min(1.0, keyword_matches / len(target.expected_coverage))

    def _detect_red_flags(self, answer_text: str, target: VivaTarget) -> List[str]:
        """Detect red flags in answer."""

        flags = []

        if target.red_flags:
            for flag in target.red_flags:
                if flag.lower() in answer_text.lower():
                    flags.append(f"Red flag: {flag}")

        # Generic answer detection
        generic_phrases = ["it depends", "generally", "typically", "probably", "maybe"]
        if any(phrase in answer_text.lower() for phrase in generic_phrases):
            flags.append("Generic answer: lacks specificity")

        # Vague answer detection
        if len(answer_text.split()) < 20:
            flags.append("Vague explanation: too brief")

        return flags

    def _detect_contradictions(self, answer_text: str, target: VivaTarget) -> List[Dict[str, str]]:
        """Detect contradictions with previous answers."""

        contradictions = []

        for prev_answer in self.answer_history:
            prev_text = prev_answer.get("answer_text", "").lower()
            curr_text = answer_text.lower()

            # Simple contradiction detection: opposite claims
            if "redis" in prev_text and "no caching" in curr_text:
                contradictions.append(
                    {
                        "previous": "Redis is used",
                        "current": "No caching",
                        "severity": "HIGH",
                    }
                )

            if "async" in prev_text and "synchronous" in curr_text:
                contradictions.append(
                    {
                        "previous": "Async processing",
                        "current": "Synchronous",
                        "severity": "HIGH",
                    }
                )

        return contradictions

    def _depth_to_score(self, depth: AnswerDepthLevel) -> float:
        """Convert depth level to numeric score."""

        mapping = {
            AnswerDepthLevel.GENERIC: 1.0,
            AnswerDepthLevel.SHALLOW: 2.5,
            AnswerDepthLevel.ADEQUATE: 5.0,
            AnswerDepthLevel.DEEP: 7.5,
            AnswerDepthLevel.EXPERT: 10.0,
        }

        return mapping.get(depth, 5.0)

    def _update_adaptive_difficulty(self, depth: AnswerDepthLevel) -> None:
        """Update adaptive difficulty based on answer depth."""

        current = self.session_state.adaptive_difficulty

        if depth in [AnswerDepthLevel.DEEP, AnswerDepthLevel.EXPERT]:
            # Increase difficulty
            self.session_state.adaptive_difficulty = min(10.0, current + 1.0)
        elif depth == AnswerDepthLevel.GENERIC:
            # Decrease difficulty
            self.session_state.adaptive_difficulty = max(1.0, current - 1.0)

        # Clamp to valid range
        self.session_state.adaptive_difficulty = max(1.0, min(10.0, self.session_state.adaptive_difficulty))
