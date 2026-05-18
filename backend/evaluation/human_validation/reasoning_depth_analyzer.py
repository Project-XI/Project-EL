"""Reasoning Depth Analyzer: Distinguishes builders from memorizers.

Analyzes whether candidate responses demonstrate:
- DEEP UNDERSTANDING: Built the system, understands WHY decisions were made
- SURFACE KNOWLEDGE: Memorized or learned from documentation/coursework

Uses adaptive follow-up questions to distinguish:
1. Builders can explain tradeoffs and reasoning
2. Builders can handle novel edge cases
3. Builders can identify when they don't know something
4. Memorizers give generic, textbook answers
5. Memorizers fail on follow-ups that require reasoning
6. Memorizers contradict themselves or resort to guessing
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .viva_session_conductor import (
    CandidateResponse,
    CandidateResponseQuality,
    VivaQuestion,
    VivaQuestionType,
    VivaSession,
)


class ReasoningDepth(str, Enum):
    """Assessment of how deep the reasoning is."""
    DEEP_BUILDER = "deep_builder"  # Clearly built the system
    PRACTICED_BUILDER = "practiced_builder"  # Built it, but answers rehearsed
    INFORMED_LEARNER = "informed_learner"  # Understands well but didn't build
    MEMORIZER = "memorizer"  # Memorized answers, limited reasoning
    GUESSER = "guesser"  # Guessing, contradicting, confused


class UnderstandingIndicator(str, Enum):
    """Specific signals indicating understanding level."""
    EXPLAINS_RATIONALE = "explains_rationale"  # "We did X because..."
    MENTIONS_TRADEOFFS = "mentions_tradeoffs"  # "This approach trades off A for B"
    HANDLES_EDGE_CASE = "handles_edge_case"  # Can identify edge cases
    IDENTIFIES_GAPS = "identifies_gaps"  # "We haven't solved that yet"
    ADMITS_UNCERTAINTY = "admits_uncertainty"  # "I'm not 100% sure on that"
    INTEGRATES_CONTEXT = "integrates_context"  # References other parts of system
    CITES_SPECIFIC_IMPLEMENTATION = "cites_specific"  # "In our code at..."


class MemorizationIndicator(str, Enum):
    """Specific signals indicating memorization."""
    TEXTBOOK_LANGUAGE = "textbook_language"  # "Best practice is..."
    GENERIC_ANSWER = "generic_answer"  # "We use the standard approach"
    FAILS_FOLLOW_UP = "fails_follow_up"  # Can't explain deeper
    CONTRADICTS_SELF = "contradicts_self"  # Changes answer or reverses logic
    PARROTS_QUESTION = "parrots_question"  # Repeats question back
    USES_BUZZWORDS = "uses_buzzwords"  # Technical jargon without specifics
    BLANK_ON_EDGE_CASE = "blank_on_edge_case"  # Can't handle "what if" questions


@dataclass
class ReasoningDepthAssessment:
    """Assessment of response reasoning depth."""
    
    question_id: str
    response_text: str
    
    # Understanding indicators found
    understanding_indicators: List[UnderstandingIndicator] = field(default_factory=list)
    memorization_indicators: List[MemorizationIndicator] = field(default_factory=list)
    
    # Scores
    reasoning_depth_score: float = 0.0  # 0-1: how deep is the reasoning?
    understanding_confidence: float = 0.0  # 0-1: how confident about understanding?
    memorization_likelihood: float = 0.0  # 0-1: likelihood this is memorized?
    
    # Assessment
    reasoning_depth: ReasoningDepth = ReasoningDepth.GUESSER
    explanation: str = ""
    recommended_follow_up: Optional[str] = None  # What follow-up would be revealing?
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "question_id": self.question_id,
            "reasoning_depth": self.reasoning_depth.value,
            "reasoning_depth_score": self.reasoning_depth_score,
            "understanding_confidence": self.understanding_confidence,
            "memorization_likelihood": self.memorization_likelihood,
            "understanding_indicators": [i.value for i in self.understanding_indicators],
            "memorization_indicators": [i.value for i in self.memorization_indicators],
            "explanation": self.explanation,
            "recommended_follow_up": self.recommended_follow_up,
        }


@dataclass
class CandidateProfile:
    """Profile of a candidate's understanding level."""
    
    candidate_id: str
    session_id: str
    
    # Overall assessment
    overall_reasoning_depth: ReasoningDepth = ReasoningDepth.GUESSER
    overall_understanding_score: float = 0.0  # 0-1
    overall_memorization_score: float = 0.0  # 0-1
    
    # Distribution across responses
    response_assessments: List[ReasoningDepthAssessment] = field(default_factory=list)
    
    # Evidence
    strong_indicators: List[str] = field(default_factory=list)  # Quotes showing understanding
    weak_indicators: List[str] = field(default_factory=list)  # Quotes showing memorization
    red_flags: List[str] = field(default_factory=list)  # Concerning patterns
    
    # Classification confidence
    builder_confidence: float = 0.0  # 0-1: how sure are we they're a builder?
    builder_vs_memorizer_ratio: float = 0.0  # Understanding / (Understanding + Memorization)
    
    # Verdict
    verdict: str = ""  # Summary judgment
    certainty: str = ""  # How certain are we? (high, medium, low)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "candidate_id": self.candidate_id,
            "session_id": self.session_id,
            "overall_reasoning_depth": self.overall_reasoning_depth.value,
            "overall_understanding_score": self.overall_understanding_score,
            "overall_memorization_score": self.overall_memorization_score,
            "builder_confidence": self.builder_confidence,
            "builder_vs_memorizer_ratio": self.builder_vs_memorizer_ratio,
            "response_count": len(self.response_assessments),
            "verdict": self.verdict,
            "certainty": self.certainty,
            "strong_indicators": self.strong_indicators,
            "weak_indicators": self.weak_indicators,
            "red_flags": self.red_flags,
        }


class ReasoningDepthAnalyzer:
    """Analyzes whether candidate shows deep understanding or just memorization."""
    
    def __init__(self, results_dir: Optional[Path | str] = None):
        self.results_dir = Path(results_dir or "evaluation/human_validation/reasoning_analysis")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_session(
        self,
        candidate_id: str,
        session: VivaSession,
    ) -> CandidateProfile:
        """Analyze a complete viva session to distinguish builder vs memorizer."""
        
        profile = CandidateProfile(
            candidate_id=candidate_id,
            session_id=session.session_id,
        )
        
        # Analyze each response
        for response in session.candidate_responses:
            # Find the question
            question = next(
                (q for q in session.questions_asked if q.question_id == response.question_id),
                None,
            )
            if not question:
                continue
            
            assessment = self._assess_response_depth(question, response)
            profile.response_assessments.append(assessment)
        
        # Aggregate profile
        profile = self._aggregate_profile(profile, session)
        
        return profile
    
    def _assess_response_depth(
        self,
        question: VivaQuestion,
        response: CandidateResponse,
    ) -> ReasoningDepthAssessment:
        """Assess reasoning depth of a single response."""
        
        assessment = ReasoningDepthAssessment(
            question_id=question.question_id,
            response_text=response.response_text,
        )
        
        # Detect understanding indicators
        assessment.understanding_indicators = self._find_understanding_indicators(
            response.response_text
        )
        
        # Detect memorization indicators
        assessment.memorization_indicators = self._find_memorization_indicators(
            response.response_text, question
        )
        
        # Score reasoning depth
        assessment.reasoning_depth_score = self._score_reasoning_depth(
            response, assessment.understanding_indicators, assessment.memorization_indicators
        )
        
        # Classify reasoning depth
        assessment.reasoning_depth = self._classify_reasoning_depth(
            assessment.reasoning_depth_score,
            response.quality,
            len(assessment.understanding_indicators),
            len(assessment.memorization_indicators),
        )
        
        # Calculate confidence scores
        understanding_count = len(assessment.understanding_indicators)
        memorization_count = len(assessment.memorization_indicators)
        total_indicators = understanding_count + memorization_count
        
        if total_indicators > 0:
            assessment.understanding_confidence = understanding_count / total_indicators
            assessment.memorization_likelihood = memorization_count / total_indicators
        
        # Generate explanation and follow-up recommendation
        assessment.explanation = self._generate_explanation(assessment)
        assessment.recommended_follow_up = self._recommend_follow_up(
            assessment.reasoning_depth, response.response_text
        )
        
        return assessment
    
    def _find_understanding_indicators(self, response_text: str) -> List[UnderstandingIndicator]:
        """Find specific signals of deep understanding."""
        
        indicators: List[UnderstandingIndicator] = []
        response_lower = response_text.lower()
        
        # Explains rationale
        if any(phrase in response_lower for phrase in ["because", "reason", "the idea is", "we chose", "motivation"]):
            indicators.append(UnderstandingIndicator.EXPLAINS_RATIONALE)
        
        # Mentions tradeoffs
        if any(phrase in response_lower for phrase in ["tradeoff", "trade-off", "pros and cons", "benefit", "cost", "downside", "drawback"]):
            indicators.append(UnderstandingIndicator.MENTIONS_TRADEOFFS)
        
        # Handles edge cases
        if any(phrase in response_lower for phrase in ["edge case", "corner case", "what if", "scenario", "happens when", "failure case"]):
            indicators.append(UnderstandingIndicator.HANDLES_EDGE_CASE)
        
        # Identifies gaps
        if any(phrase in response_lower for phrase in ["haven't", "not yet", "todo", "limitation", "gap", "open question"]):
            indicators.append(UnderstandingIndicator.IDENTIFIES_GAPS)
        
        # Admits uncertainty
        if any(phrase in response_lower for phrase in ["not sure", "uncertain", "unclear", "might be", "could be", "i think"]):
            indicators.append(UnderstandingIndicator.ADMITS_UNCERTAINTY)
        
        # Integrates context
        if any(phrase in response_lower for phrase in ["other", "integration", "depends on", "relates to", "interacts with", "component"]):
            indicators.append(UnderstandingIndicator.INTEGRATES_CONTEXT)
        
        # Cites specific implementation
        if any(phrase in response_lower for phrase in ["code", "file", "function", "class", "method", "line", "at line"]):
            indicators.append(UnderstandingIndicator.CITES_SPECIFIC_IMPLEMENTATION)
        
        return indicators
    
    def _find_memorization_indicators(
        self,
        response_text: str,
        question: VivaQuestion,
    ) -> List[MemorizationIndicator]:
        """Find specific signals of memorization without understanding."""
        
        indicators: List[MemorizationIndicator] = []
        response_lower = response_text.lower()
        
        # Textbook language
        if any(phrase in response_lower for phrase in ["best practice", "industry standard", "standard approach", "common pattern", "everyone does"]):
            indicators.append(MemorizationIndicator.TEXTBOOK_LANGUAGE)
        
        # Generic answer
        if len(response_text.split()) < 15 or any(phrase in response_lower for phrase in ["basically", "you know", "stuff like", "whatever"]):
            indicators.append(MemorizationIndicator.GENERIC_ANSWER)
        
        # Parrots question
        if response_text.lower().startswith(question.question_text[:20].lower()):
            indicators.append(MemorizationIndicator.PARROTS_QUESTION)
        
        # Uses buzzwords
        buzzwords = ["microservices", "cloud-native", "scalable", "resilient", "secure", "robust", "distributed"]
        buzzword_count = sum(1 for bw in buzzwords if bw in response_lower)
        if buzzword_count >= 2 and len(response_text.split()) < 30:
            indicators.append(MemorizationIndicator.USES_BUZZWORDS)
        
        return indicators
    
    def _score_reasoning_depth(
        self,
        response: CandidateResponse,
        understanding_indicators: List[UnderstandingIndicator],
        memorization_indicators: List[MemorizationIndicator],
    ) -> float:
        """Score how deep the reasoning is (0-1)."""
        
        # Base on response quality
        quality_scores = {
            CandidateResponseQuality.EXCELLENT: 0.9,
            CandidateResponseQuality.GOOD: 0.7,
            CandidateResponseQuality.ADEQUATE: 0.5,
            CandidateResponseQuality.WEAK: 0.2,
            CandidateResponseQuality.EVASIVE: 0.0,
            CandidateResponseQuality.CONTRADICTION: 0.0,
        }
        base_score = quality_scores.get(response.quality, 0.5)
        
        # Adjust for indicators
        understanding_boost = len(understanding_indicators) * 0.1  # +0.1 per indicator
        memorization_penalty = len(memorization_indicators) * 0.15  # -0.15 per indicator
        
        # Combine
        score = base_score + understanding_boost - memorization_penalty
        
        return max(0.0, min(1.0, score))
    
    def _classify_reasoning_depth(
        self,
        depth_score: float,
        response_quality: CandidateResponseQuality,
        understanding_count: int,
        memorization_count: int,
    ) -> ReasoningDepth:
        """Classify response into reasoning depth category."""
        
        if depth_score >= 0.8 and understanding_count >= 2:
            return ReasoningDepth.DEEP_BUILDER
        
        if depth_score >= 0.6 and understanding_count >= 1 and memorization_count == 0:
            return ReasoningDepth.PRACTICED_BUILDER
        
        if depth_score >= 0.5 and understanding_count >= 2 and memorization_count <= 1:
            return ReasoningDepth.INFORMED_LEARNER
        
        if depth_score >= 0.3 and memorization_count >= 1 and response_quality in [
            CandidateResponseQuality.GOOD,
            CandidateResponseQuality.ADEQUATE,
        ]:
            return ReasoningDepth.MEMORIZER
        
        return ReasoningDepth.GUESSER
    
    def _generate_explanation(self, assessment: ReasoningDepthAssessment) -> str:
        """Generate explanation of the reasoning depth assessment."""
        
        if assessment.reasoning_depth == ReasoningDepth.DEEP_BUILDER:
            return (
                f"Strong understanding evident. Response shows {len(assessment.understanding_indicators)} "
                f"understanding indicators (explains reasoning, mentions tradeoffs, handles edge cases). "
                f"No memorization signals detected."
            )
        
        elif assessment.reasoning_depth == ReasoningDepth.PRACTICED_BUILDER:
            return (
                f"Good understanding with articulate explanation. "
                f"Found {len(assessment.understanding_indicators)} understanding indicators. "
                f"Answer sounds rehearsed but reasoning is solid."
            )
        
        elif assessment.reasoning_depth == ReasoningDepth.INFORMED_LEARNER:
            return (
                f"Solid knowledge but possibly from learning/documentation rather than building. "
                f"Shows understanding ({len(assessment.understanding_indicators)} indicators) "
                f"but answers somewhat generic."
            )
        
        elif assessment.reasoning_depth == ReasoningDepth.MEMORIZER:
            return (
                f"Likely memorized or learned from documentation. "
                f"Found {len(assessment.memorization_indicators)} memorization indicators "
                f"({', '.join(i.value for i in assessment.memorization_indicators[:2])}). "
                f"Limited ability to reason beyond prepared answer."
            )
        
        else:
            return (
                f"Unclear understanding or guessing. "
                f"Response quality: {assessment.reasoning_depth_score:.1%}. "
                f"Would need follow-up questions to clarify."
            )
    
    def _recommend_follow_up(self, reasoning_depth: ReasoningDepth, response_text: str) -> Optional[str]:
        """Recommend a follow-up question that would be revealing."""
        
        if reasoning_depth == ReasoningDepth.DEEP_BUILDER:
            return None  # No need to probe further
        
        elif reasoning_depth == ReasoningDepth.PRACTICED_BUILDER:
            return "Walk us through a failure scenario - what goes wrong first, and why?"
        
        elif reasoning_depth == ReasoningDepth.INFORMED_LEARNER:
            return "What edge case or failure scenario wasn't obvious until you started implementing?"
        
        elif reasoning_depth == ReasoningDepth.MEMORIZER:
            return "What would you change if you built this today? What are the downsides of your approach?"
        
        else:
            return "Can you walk through the code flow step-by-step? Where does the critical logic happen?"
    
    def _aggregate_profile(
        self,
        profile: CandidateProfile,
        session: VivaSession,
    ) -> CandidateProfile:
        """Aggregate individual response assessments into overall profile."""
        
        if not profile.response_assessments:
            return profile
        
        # Calculate overall understanding and memorization scores
        avg_understanding = sum(a.understanding_confidence for a in profile.response_assessments) / len(
            profile.response_assessments
        )
        avg_memorization = sum(a.memorization_likelihood for a in profile.response_assessments) / len(
            profile.response_assessments
        )
        
        profile.overall_understanding_score = avg_understanding
        profile.overall_memorization_score = avg_memorization
        
        # Calculate ratio
        if avg_understanding + avg_memorization > 0:
            profile.builder_vs_memorizer_ratio = avg_understanding / (
                avg_understanding + avg_memorization
            )
        
        # Overall builder confidence
        profile.builder_confidence = max(0.0, avg_understanding - avg_memorization)
        
        # Classify overall reasoning depth
        deep_builders = sum(1 for a in profile.response_assessments if a.reasoning_depth == ReasoningDepth.DEEP_BUILDER)
        practiced_builders = sum(1 for a in profile.response_assessments if a.reasoning_depth == ReasoningDepth.PRACTICED_BUILDER)
        informed_learners = sum(1 for a in profile.response_assessments if a.reasoning_depth == ReasoningDepth.INFORMED_LEARNER)
        memorizers = sum(1 for a in profile.response_assessments if a.reasoning_depth == ReasoningDepth.MEMORIZER)
        guessers = sum(1 for a in profile.response_assessments if a.reasoning_depth == ReasoningDepth.GUESSER)
        
        total = len(profile.response_assessments)
        
        if deep_builders >= total * 0.6:
            profile.overall_reasoning_depth = ReasoningDepth.DEEP_BUILDER
        elif practiced_builders + deep_builders >= total * 0.6:
            profile.overall_reasoning_depth = ReasoningDepth.PRACTICED_BUILDER
        elif informed_learners >= total * 0.4:
            profile.overall_reasoning_depth = ReasoningDepth.INFORMED_LEARNER
        elif memorizers >= total * 0.5:
            profile.overall_reasoning_depth = ReasoningDepth.MEMORIZER
        else:
            profile.overall_reasoning_depth = ReasoningDepth.GUESSER
        
        # Extract strong and weak indicators
        all_understanding = [
            ind.value for a in profile.response_assessments for ind in a.understanding_indicators
        ]
        all_memorization = [
            ind.value for a in profile.response_assessments for ind in a.memorization_indicators
        ]
        
        profile.strong_indicators = list(set(all_understanding))[:3]
        profile.weak_indicators = list(set(all_memorization))[:3]
        
        # Identify red flags
        contradictions = sum(1 for r in session.candidate_responses if r.quality == CandidateResponseQuality.CONTRADICTION)
        if contradictions > 0:
            profile.red_flags.append(f"Contradicted self {contradictions} times")
        
        evasions = sum(1 for r in session.candidate_responses if r.quality == CandidateResponseQuality.EVASIVE)
        if evasions > 0:
            profile.red_flags.append(f"Evaded {evasions} questions")
        
        # Generate verdict
        profile = self._generate_verdict(profile)
        
        return profile
    
    def _generate_verdict(self, profile: CandidateProfile) -> CandidateProfile:
        """Generate final verdict on builder vs memorizer."""
        
        if profile.overall_reasoning_depth == ReasoningDepth.DEEP_BUILDER:
            profile.verdict = (
                f"Clear builder. Demonstrated deep understanding of implementation details, "
                f"tradeoffs, and failure scenarios. High confidence this candidate built the system."
            )
            profile.certainty = "high"
        
        elif profile.overall_reasoning_depth == ReasoningDepth.PRACTICED_BUILDER:
            profile.verdict = (
                f"Likely builder. Shows solid understanding and can explain reasoning, but answers "
                f"sound somewhat rehearsed. May be reviewing before interview."
            )
            profile.certainty = "high"
        
        elif profile.overall_reasoning_depth == ReasoningDepth.INFORMED_LEARNER:
            profile.verdict = (
                f"Knowledgeable but likely learned from docs/coursework rather than building. "
                f"Shows understanding but lacks specific implementation insights."
            )
            profile.certainty = "medium"
        
        elif profile.overall_reasoning_depth == ReasoningDepth.MEMORIZER:
            profile.verdict = (
                f"Likely memorized. Gives textbook-correct answers but can't reason deeply about "
                f"tradeoffs, edge cases, or implementation details. Low builder confidence."
            )
            profile.certainty = "medium"
        
        else:
            profile.verdict = (
                f"Uncertain understanding. Responses suggest guessing or lack of engagement. "
                f"Cannot confidently assess builder status."
            )
            profile.certainty = "low"
        
        return profile
    
    def save_profile(self, profile: CandidateProfile) -> Path:
        """Save the reasoning depth profile to disk."""
        
        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        filename = f"reasoning_depth_{profile.candidate_id}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        profile_dict = {
            **profile.to_dict(),
            "response_assessments": [a.to_dict() for a in profile.response_assessments],
            "timestamp": timestamp,
        }
        
        filepath.write_text(json.dumps(profile_dict, indent=2), encoding="utf-8")
        return filepath
