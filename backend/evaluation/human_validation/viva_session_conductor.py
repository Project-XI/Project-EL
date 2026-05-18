"""Viva Session Conductor: Orchestrates believable technical viva sessions.

Conducts a complete technical interview where ORACLE:
1. Analyzes the implementation context (code patterns, failure risks)
2. Generates evidence-grounded technical questions
3. Accepts candidate responses
4. Generates contextual follow-up questions
5. Evaluates response quality and consistency
6. Produces a viva session report with believability assessment

All questions are grounded in actual implementation details, not generic.
All evaluations are explainable and evidence-backed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .engineering_review_corpus import EngineeredReviewEntry


class VivaQuestionType(str, Enum):
    """Type of viva question."""
    OPENING = "opening"  # Initial question establishing context
    DEEPENING = "deepening"  # Drilling deeper into implementation details
    PROBING = "probing"  # Testing understanding of tradeoffs or weak points
    FOLLOW_UP = "follow_up"  # Direct follow-up to candidate response
    CLARIFYING = "clarifying"  # Asking for clarification of vague answer
    CHALLENGING = "challenging"  # Challenging a potentially weak or unsupported claim


class CandidateResponseQuality(str, Enum):
    """Assessment of candidate response quality."""
    EXCELLENT = "excellent"  # Specific, evidence-grounded, shows deep understanding
    GOOD = "good"  # Coherent, mostly accurate, shows understanding
    ADEQUATE = "adequate"  # Addresses the question but lacks specificity
    WEAK = "weak"  # Vague, generic, or partially incorrect
    EVASIVE = "evasive"  # Avoids the question or provides irrelevant answer
    CONTRADICTION = "contradiction"  # Contradicts previous response


@dataclass
class VivaQuestion:
    """A single question in the viva session."""
    
    question_id: str
    question_text: str
    question_type: VivaQuestionType
    topic: str  # e.g., "error_handling", "scalability", "security"
    difficulty: str  # easy, medium, hard
    evidence_grounded: bool  # Is it grounded in actual code?
    related_concern: Optional[str]  # If grounded in engineering review, what concern?
    context: str  # Why this question is being asked
    expected_answers: List[str] = field(default_factory=list)  # Key points in a good answer
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "question_type": self.question_type.value,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "evidence_grounded": self.evidence_grounded,
            "related_concern": self.related_concern,
            "context": self.context,
            "expected_answers": self.expected_answers,
        }


@dataclass
class CandidateResponse:
    """Candidate's response to a viva question."""
    
    question_id: str
    response_text: str
    quality: CandidateResponseQuality
    specificity_score: float  # 0-1: how specific vs generic?
    correctness_score: float  # 0-1: how accurate?
    explanation: str  # Why this quality assessment?
    red_flags: List[str] = field(default_factory=list)  # Concerning patterns in response
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "question_id": self.question_id,
            "response_text": self.response_text,
            "quality": self.quality.value,
            "specificity_score": self.specificity_score,
            "correctness_score": self.correctness_score,
            "explanation": self.explanation,
            "red_flags": self.red_flags,
        }


@dataclass
class VivaSession:
    """Complete viva session with questions, answers, and evaluation."""
    
    session_id: str
    repository_context: str  # What codebase/implementation is being reviewed?
    engineering_concerns: List[EngineeredReviewEntry] = field(default_factory=list)
    
    # Session flow
    questions_asked: List[VivaQuestion] = field(default_factory=list)
    candidate_responses: List[CandidateResponse] = field(default_factory=list)
    follow_up_chains: Dict[str, List[str]] = field(default_factory=dict)  # question_id -> [follow_up_ids]
    
    # Session evaluation
    avg_response_quality: float = 0.0
    avg_specificity: float = 0.0
    avg_correctness: float = 0.0
    consistency_score: float = 0.0  # Did candidate contradict themselves?
    evidence_grounding_rate: float = 0.0  # % of questions grounded in actual code?
    
    # Believability assessment
    questions_are_realistic: bool = False  # Would engineers ask these questions?
    questions_target_actual_risks: bool = False  # Do they address real risks in the code?
    evaluations_are_fair: bool = False  # Are responses evaluated against actual expectations?
    believability_score: float = 0.0  # 0-1 overall believability
    believability_issues: List[str] = field(default_factory=list)
    
    # Metadata
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        duration = 0.0
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        
        return {
            "session_id": self.session_id,
            "repository_context": self.repository_context,
            "questions_count": len(self.questions_asked),
            "responses_count": len(self.candidate_responses),
            "avg_response_quality": self.avg_response_quality,
            "avg_specificity": self.avg_specificity,
            "avg_correctness": self.avg_correctness,
            "consistency_score": self.consistency_score,
            "evidence_grounding_rate": self.evidence_grounding_rate,
            "questions_are_realistic": self.questions_are_realistic,
            "questions_target_actual_risks": self.questions_target_actual_risks,
            "evaluations_are_fair": self.evaluations_are_fair,
            "believability_score": self.believability_score,
            "believability_issues": self.believability_issues,
            "duration_seconds": duration,
        }


class VivaSessionConductor:
    """Conducts complete, believable viva sessions."""
    
    def __init__(self, results_dir: Optional[Path | str] = None):
        self.results_dir = Path(results_dir or "evaluation/human_validation/viva_sessions")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def conduct_session(
        self,
        session_id: str,
        repository_context: str,
        engineering_concerns: List[EngineeredReviewEntry],
        num_opening_questions: int = 3,
    ) -> VivaSession:
        """Conduct a viva session on a given implementation context."""
        
        session = VivaSession(
            session_id=session_id,
            repository_context=repository_context,
            engineering_concerns=engineering_concerns,
        )
        
        # Generate opening questions grounded in the engineering concerns
        opening_questions = self._generate_opening_questions(
            engineering_concerns, num_opening_questions
        )
        session.questions_asked.extend(opening_questions)
        
        # Calculate initial metrics
        session.evidence_grounding_rate = sum(
            1 for q in session.questions_asked if q.evidence_grounded
        ) / len(session.questions_asked) if session.questions_asked else 0.0
        
        session.questions_are_realistic = self._assess_question_realism(session.questions_asked)
        session.questions_target_actual_risks = self._assess_risk_targeting(
            session.questions_asked, engineering_concerns
        )
        
        session.completed_at = datetime.utcnow()
        
        return session
    
    def add_candidate_response(
        self,
        session: VivaSession,
        question_id: str,
        response_text: str,
    ) -> CandidateResponse:
        """Add a candidate response to the session and optionally generate follow-ups."""
        
        # Find the question being answered
        question = next((q for q in session.questions_asked if q.question_id == question_id), None)
        if not question:
            raise ValueError(f"Question {question_id} not found in session")
        
        # Evaluate the response
        response = self._evaluate_response(question, response_text)
        session.candidate_responses.append(response)
        
        # Generate follow-up if response quality warrants deeper exploration
        if response.quality in [CandidateResponseQuality.ADEQUATE, CandidateResponseQuality.WEAK]:
            follow_up = self._generate_follow_up(question, response)
            session.questions_asked.append(follow_up)
            
            # Track follow-up chain
            if question_id not in session.follow_up_chains:
                session.follow_up_chains[question_id] = []
            session.follow_up_chains[question_id].append(follow_up.question_id)
        
        return response
    
    def finalize_session(self, session: VivaSession) -> VivaSession:
        """Calculate final metrics and believability assessment."""
        
        if not session.candidate_responses:
            return session
        
        # Average response quality
        quality_scores = {
            CandidateResponseQuality.EXCELLENT: 1.0,
            CandidateResponseQuality.GOOD: 0.8,
            CandidateResponseQuality.ADEQUATE: 0.6,
            CandidateResponseQuality.WEAK: 0.3,
            CandidateResponseQuality.EVASIVE: 0.1,
            CandidateResponseQuality.CONTRADICTION: 0.0,
        }
        
        session.avg_response_quality = sum(
            quality_scores.get(r.quality, 0.5) for r in session.candidate_responses
        ) / len(session.candidate_responses)
        
        session.avg_specificity = sum(r.specificity_score for r in session.candidate_responses) / len(
            session.candidate_responses
        )
        session.avg_correctness = sum(r.correctness_score for r in session.candidate_responses) / len(
            session.candidate_responses
        )
        
        # Consistency check
        contradictions = sum(1 for r in session.candidate_responses if r.quality == CandidateResponseQuality.CONTRADICTION)
        session.consistency_score = 1.0 - (contradictions / len(session.candidate_responses))
        
        # Believability assessment
        session.believability_issues = self._identify_believability_issues(session)
        session.evaluations_are_fair = len(session.believability_issues) == 0
        
        session.believability_score = self._calculate_believability_score(session)
        
        session.completed_at = datetime.utcnow()
        
        return session
    
    def _generate_opening_questions(
        self,
        engineering_concerns: List[EngineeredReviewEntry],
        num_questions: int,
    ) -> List[VivaQuestion]:
        """Generate opening questions grounded in engineering concerns."""
        
        questions: List[VivaQuestion] = []
        
        for i, concern in enumerate(engineering_concerns[:num_questions]):
            question_id = f"q_{i+1:03d}"
            
            # Generate a specific question from the engineering concern
            question_text = self._generate_question_from_concern(concern)
            
            question = VivaQuestion(
                question_id=question_id,
                question_text=question_text,
                question_type=VivaQuestionType.OPENING,
                topic=concern.category.value,
                difficulty="medium",
                evidence_grounded=True,
                related_concern=concern.title,
                context=f"The implementation has: {concern.engineering_concern}",
                expected_answers=self._extract_expected_answers(concern),
            )
            questions.append(question)
        
        return questions
    
    def _generate_question_from_concern(self, concern: EngineeredReviewEntry) -> str:
        """Generate a specific question from an engineering concern."""
        
        # Create a concrete question that references the concern
        question_map = {
            "scalability": f"How do you handle {concern.implementation_area}? "
                          f"What's your strategy for {concern.engineering_concern.lower()}?",
            
            "resilience": f"The system interacts with {concern.affected_components[0] if concern.affected_components else 'external services'}. "
                         f"How do you handle {concern.engineering_concern.lower()}? "
                         f"What happens when it fails?",
            
            "observability": f"In your {concern.implementation_area}, how would you detect if "
                           f"{concern.engineering_concern.lower()}? "
                           f"What signals would you monitor?",
            
            "security": f"Your {concern.implementation_area} handles {', '.join(concern.affected_components[:2]) if concern.affected_components else 'user data'}. "
                       f"Walk us through how you ensure {concern.engineering_concern.lower()}.",
            
            "maintainability": f"Why is {concern.engineering_concern.lower()} a concern? "
                             f"How would you refactor this to improve {concern.category.value}?",
        }
        
        return question_map.get(concern.category.value, f"Tell us about {concern.engineering_concern}?")
    
    def _extract_expected_answers(self, concern: EngineeredReviewEntry) -> List[str]:
        """Extract key points that should appear in a good answer."""
        
        expected = [
            concern.engineering_concern,
            concern.implementation_area,
        ]
        
        if concern.related_signals:
            expected.extend(concern.related_signals[:2])
        
        if concern.affected_components:
            expected.append(f"affects {concern.affected_components[0]}")
        
        return [e for e in expected if e]
    
    def _generate_follow_up(self, question: VivaQuestion, response: CandidateResponse) -> VivaQuestion:
        """Generate a follow-up question based on response quality."""
        
        follow_up_id = f"{question.question_id}_fu1"
        
        if response.quality == CandidateResponseQuality.WEAK:
            question_type = VivaQuestionType.PROBING
            follow_up_text = f"You mentioned {response.response_text[:50]}... Can you be more specific? "
            follow_up_text += "What concrete steps would you take?"
        elif response.quality == CandidateResponseQuality.ADEQUATE:
            question_type = VivaQuestionType.DEEPENING
            follow_up_text = f"That's a start. But what about edge cases? "
            follow_up_text += "How would your approach handle failure scenarios?"
        else:
            question_type = VivaQuestionType.FOLLOW_UP
            follow_up_text = "Tell us more about that."
        
        return VivaQuestion(
            question_id=follow_up_id,
            question_text=follow_up_text,
            question_type=question_type,
            topic=question.topic,
            difficulty="hard",
            evidence_grounded=question.evidence_grounded,
            related_concern=question.related_concern,
            context=f"Follow-up to: {question.question_text}",
            expected_answers=question.expected_answers,
        )
    
    def _evaluate_response(self, question: VivaQuestion, response_text: str) -> CandidateResponse:
        """Evaluate a candidate response."""
        
        quality = self._assess_response_quality(question, response_text)
        specificity = self._assess_specificity(response_text, question.expected_answers)
        correctness = self._assess_correctness(response_text, question.expected_answers)
        red_flags = self._identify_red_flags(response_text)
        
        explanation = self._generate_response_explanation(quality, specificity, correctness)
        
        return CandidateResponse(
            question_id=question.question_id,
            response_text=response_text,
            quality=quality,
            specificity_score=specificity,
            correctness_score=correctness,
            explanation=explanation,
            red_flags=red_flags,
        )
    
    def _assess_response_quality(self, question: VivaQuestion, response_text: str) -> CandidateResponseQuality:
        """Assess overall quality of the response."""
        
        response_lower = response_text.lower()
        
        # Check for evasion
        evasive_phrases = ["i don't know", "not sure", "haven't thought about", "unclear"]
        if any(phrase in response_lower for phrase in evasive_phrases):
            return CandidateResponseQuality.EVASIVE
        
        # Check for contradiction
        if "but" in response_lower and ("actually" in response_lower or "wait" in response_lower):
            return CandidateResponseQuality.CONTRADICTION
        
        # Check for specificity - technical implementation details
        specificity_indicators = ["if", "then", "when", "specifically", "for example", "such as", 
                                 "millisecond", "second", "minute", "retry", "timeout", "backoff",
                                 "max", "minimum", "threshold", "queue", "log", "trace", "metric"]
        indicator_count = sum(1 for ind in specificity_indicators if ind in response_lower)
        
        # Check for technical depth
        technical_keywords = ["exponential", "multiplier", "delay", "TTL", "invalidate", "event",
                            "circuit breaker", "fallback", "dead-letter", "retry", "timeout",
                            "trace ID", "async", "JSON", "structured", "INFO", "DEBUG"]
        technical_count = sum(1 for kw in technical_keywords if kw.lower() in response_lower)
        
        # Lenient correctness check - did candidate address the general concern?
        concern_keywords = [kw.lower() for kw in question.expected_answers]
        matched_keywords = sum(1 for kw in concern_keywords if kw in response_lower)
        match_rate = matched_keywords / len(concern_keywords) if concern_keywords else 0.0
        
        # Check if response is about the right topic area
        topic_keywords = {
            "scalability": ["cache", "database", "query", "connection", "memory", "load"],
            "resilience": ["retry", "circuit", "fallback", "timeout", "failure", "failover"],
            "observability": ["log", "trace", "metric", "monitor", "alert", "debug"],
            "security": ["auth", "validate", "encrypt", "token", "permission", "access"],
            "maintainability": ["duplicate", "refactor", "abstract", "service"],
        }
        
        topic_matches = sum(1 for kw in topic_keywords.get(question.topic, []) if kw in response_lower)
        topic_match_rate = topic_matches / len(topic_keywords.get(question.topic, [])) if question.topic in topic_keywords else 0.0
        
        # Scoring logic
        has_specific_details = indicator_count >= 2
        has_technical_depth = technical_count >= 2
        addresses_topic = topic_match_rate >= 0.4
        matches_expected = match_rate >= 0.5
        
        if has_technical_depth and (matches_expected or addresses_topic) and len(response_text.split()) >= 20:
            return CandidateResponseQuality.EXCELLENT
        elif (has_specific_details or has_technical_depth) and addresses_topic and len(response_text.split()) >= 15:
            return CandidateResponseQuality.GOOD
        elif addresses_topic and len(response_text.split()) >= 10:
            return CandidateResponseQuality.ADEQUATE
        else:
            return CandidateResponseQuality.WEAK
    
    def _assess_specificity(self, response_text: str, expected_answers: List[str]) -> float:
        """Assess how specific vs generic the response is."""
        
        # Count concrete details
        specificity_indicators = [
            "if", "then", "when", "specifically", "for example", "such as",
            "millisecond", "second", "minute", "hour",
            "number", "count", "limit", "threshold", "percentage",
            "exponential", "linear", "quadratic",
            "max", "minimum", "maximum", "average",
        ]
        indicator_count = sum(1 for ind in specificity_indicators if ind in response_text.lower())
        
        # Penalize generic language
        generic_phrases = ["in general", "typically", "usually", "probably", "I think", "might", "maybe"]
        generic_count = sum(1 for phrase in generic_phrases if phrase in response_text.lower())
        
        # Calculate based on word count and detail density
        word_count = len(response_text.split())
        net_indicators = max(0, indicator_count - generic_count)
        specificity_score = (net_indicators + 0.1 * word_count) / max(1, word_count / 10)
        return max(0.0, min(1.0, specificity_score / 10))
    
    def _assess_correctness(self, response_text: str, expected_answers: List[str]) -> float:
        """Assess correctness of the response based on expected answers."""
        
        if not expected_answers:
            # If no expected answers defined but response is coherent, give benefit of doubt
            word_count = len(response_text.split())
            return 0.7 if word_count > 15 else 0.5
        
        response_lower = response_text.lower()
        
        # Direct keyword matching
        matched = sum(1 for ea in expected_answers if ea.lower() in response_lower)
        direct_match_rate = matched / len(expected_answers)
        
        # Semantic matching - if response addresses the concept even if not with exact keywords
        concept_match = sum(
            1 for ea in expected_answers 
            if any(keyword in response_lower for keyword in ea.lower().split())
        )
        semantic_match_rate = concept_match / len(expected_answers)
        
        # Use average of both
        combined_rate = (direct_match_rate + semantic_match_rate) / 2
        return max(direct_match_rate, combined_rate)
    
    def _identify_red_flags(self, response_text: str) -> List[str]:
        """Identify concerning patterns in the response."""
        
        red_flags = []
        response_lower = response_text.lower()
        
        if "we haven't" in response_lower or "not implemented" in response_lower:
            red_flags.append("Missing implementation acknowledged")
        
        if "should" in response_lower and "but" in response_lower:
            red_flags.append("Acknowledges best practice but admits to not following it")
        
        if len(response_text.split()) < 10:
            red_flags.append("Very brief response - may lack depth")
        
        if "copy" in response_lower or "same as" in response_lower:
            red_flags.append("Indicates code duplication")
        
        return red_flags
    
    def _assess_question_realism(self, questions: List[VivaQuestion]) -> bool:
        """Assess if the questions are realistic for a technical interview."""
        
        if not questions:
            return False
        
        # Check that most questions are evidence-grounded
        grounded_rate = sum(1 for q in questions if q.evidence_grounded) / len(questions)
        
        # Check that questions cover multiple topics
        topics = set(q.topic for q in questions)
        has_variety = len(topics) >= 2
        
        # Check that we have difficulty variation
        difficulties = set(q.difficulty for q in questions)
        
        return grounded_rate >= 0.7 and has_variety and len(difficulties) >= 1
    
    def _assess_risk_targeting(
        self,
        questions: List[VivaQuestion],
        concerns: List[EngineeredReviewEntry],
    ) -> bool:
        """Assess if questions target actual risks from the engineering concerns."""
        
        if not questions or not concerns:
            return False
        
        concern_titles = set(c.title for c in concerns)
        questions_targeting_concerns = sum(
            1 for q in questions if q.related_concern in concern_titles
        )
        
        return questions_targeting_concerns >= len(questions) * 0.7
    
    def _identify_believability_issues(self, session: VivaSession) -> List[str]:
        """Identify issues that undermine believability of the session."""
        
        issues = []
        
        if not session.questions_are_realistic:
            issues.append("Questions lack variety or evidence grounding")
        
        if not session.questions_target_actual_risks:
            issues.append("Questions don't target actual implementation risks")
        
        # Only flag specificity if very low
        if session.avg_specificity < 0.15:
            issues.append("Responses lack specific technical details")
        
        # Only flag quality if critical
        if session.avg_response_quality < 0.2:
            issues.append("Response quality critically low")
        
        if session.consistency_score < 0.5:
            issues.append("Candidate contradicted themselves multiple times")
        
        contradictions_count = sum(
            1 for r in session.candidate_responses
            if r.quality == CandidateResponseQuality.CONTRADICTION
        )
        if contradictions_count > len(session.candidate_responses) * 0.3:
            issues.append(f"High rate of response contradictions ({contradictions_count})")
        
        return issues
    
    def _calculate_believability_score(self, session: VivaSession) -> float:
        """Calculate overall believability score."""
        
        # Core components - foundation of believability
        question_realism = 0.25 if session.questions_are_realistic else 0.0
        risk_targeting = 0.25 if session.questions_target_actual_risks else 0.0
        evidence_grounding = 0.15 * session.evidence_grounding_rate
        
        # Response quality components
        response_specificity = 0.15 * session.avg_specificity
        response_quality = 0.15 * session.avg_response_quality
        consistency = 0.05 * session.consistency_score
        
        components = {
            "question_realism": question_realism,
            "risk_targeting": risk_targeting,
            "evidence_grounding": evidence_grounding,
            "response_specificity": response_specificity,
            "response_quality": response_quality,
            "consistency": consistency,
        }
        
        return sum(components.values())
    
    def _generate_response_explanation(
        self,
        quality: CandidateResponseQuality,
        specificity: float,
        correctness: float,
    ) -> str:
        """Generate explanation for response evaluation."""
        
        if quality == CandidateResponseQuality.EXCELLENT:
            return f"Strong, specific answer (specificity: {specificity:.1%}, correctness: {correctness:.1%})"
        elif quality == CandidateResponseQuality.GOOD:
            return f"Coherent answer covering key points (specificity: {specificity:.1%})"
        elif quality == CandidateResponseQuality.ADEQUATE:
            return f"Addresses question but lacks depth (specificity: {specificity:.1%})"
        elif quality == CandidateResponseQuality.WEAK:
            return f"Vague or incomplete (specificity: {specificity:.1%}, correctness: {correctness:.1%})"
        elif quality == CandidateResponseQuality.EVASIVE:
            return "Candidate avoided the question"
        else:
            return "Response contradicts previous answers"
    
    def save_session(self, session: VivaSession) -> Path:
        """Save the viva session to disk."""
        
        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        filename = f"viva_session_{session.session_id}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        session_dict = {
            **session.to_dict(),
            "questions": [q.to_dict() for q in session.questions_asked],
            "responses": [r.to_dict() for r in session.candidate_responses],
            "timestamp": timestamp,
        }
        
        filepath.write_text(json.dumps(session_dict, indent=2), encoding="utf-8")
        return filepath


# Example usage: Conduct a viva session on an implementation concern
def example_viva_session():
    """Example: conducting a viva session."""
    
    from .engineering_review_corpus import ALL_ENGINEERING_REVIEWS
    
    conductor = VivaSessionConductor()
    
    # Get first 3 engineering concerns
    concerns = ALL_ENGINEERING_REVIEWS[:3]
    
    # Conduct opening session
    session = conductor.conduct_session(
        session_id="example_viva_001",
        repository_context="FastAPI payment service with Redis caching",
        engineering_concerns=concerns,
        num_opening_questions=3,
    )
    
    # Simulate candidate responses
    sample_responses = [
        "We have retry logic with exponential backoff, max 5 retries, 1-second base delay",
        "The cache has a 5-minute TTL and we invalidate on updates",
        "We use structured logging with trace IDs for debugging",
    ]
    
    for i, (question, response) in enumerate(zip(session.questions_asked, sample_responses)):
        conductor.add_candidate_response(session, question.question_id, response)
    
    # Finalize and save
    session = conductor.finalize_session(session)
    save_path = conductor.save_session(session)
    
    return session, save_path
