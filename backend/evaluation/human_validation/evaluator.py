"""
Human Comparative Evaluator

Framework for comparing ORACLE outputs against human expertise across multiple dimensions.
All comparisons are evidence-backed with explicit reasoning and code citations.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .models import (
    SignalComparison,
    FailureComparison,
    VivaComparison,
    ArchitecturalAssessment,
    ExecutionBehaviorComparison,
    HumanEvaluationSession,
    ComparativeValidationReport,
    EvaluatorRole,
    SignalRelevanceScore,
    FailureRealism,
    VivaQuestionRealism,
)


class HumanComparativeEvaluator:
    """
    Framework for structured human evaluation of ORACLE outputs.
    
    Purpose: Determine whether ORACLE reasoning aligns with expert human judgment
    across signals, failures, viva questions, and architectural analysis.
    
    All metrics are evidence-backed - no speculation.
    """
    
    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or Path("evaluation/human_validation/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, HumanEvaluationSession] = {}
    
    def create_session(
        self,
        repository_name: str,
        evaluator_role: EvaluatorRole,
        oracle_context_id: str,
    ) -> HumanEvaluationSession:
        """
        Create a new human evaluation session for a repository.
        
        Args:
            repository_name: Name of the repository being evaluated
            evaluator_role: Role/expertise of the evaluator
            oracle_context_id: Reference to ORACLE analysis being evaluated
        
        Returns:
            Empty HumanEvaluationSession ready for comparisons
        """
        session = HumanEvaluationSession(
            repository_name=repository_name,
            evaluator_role=evaluator_role,
            oracle_context_id=oracle_context_id,
        )
        
        session_key = f"{repository_name}_{evaluator_role.value}_{oracle_context_id}"
        self.sessions[session_key] = session
        
        return session
    
    def add_signal_comparison(
        self,
        session: HumanEvaluationSession,
        signal_name: str,
        oracle_detected: bool,
        oracle_confidence: float,
        human_considers_relevant: bool,
        relevance_score: SignalRelevanceScore,
        reasoning: str,
        code_evidence: Optional[str] = None,
    ) -> SignalComparison:
        """
        Record human evaluation of an ORACLE signal.
        
        Args:
            session: HumanEvaluationSession to add comparison to
            signal_name: Name of the signal
            oracle_detected: Whether ORACLE detected this signal
            oracle_confidence: ORACLE's confidence score (0.0-1.0)
            human_considers_relevant: Whether human considers it relevant
            relevance_score: Human's relevance assessment
            reasoning: Why human made this assessment
            code_evidence: Files/lines where this signal is evident
        
        Returns:
            Created SignalComparison
        """
        comparison = SignalComparison(
            signal_name=signal_name,
            oracle_detected=oracle_detected,
            oracle_confidence=oracle_confidence,
            evaluator_role=session.evaluator_role,
            human_considers_relevant=human_considers_relevant,
            relevance_score=relevance_score,
            reasoning=reasoning,
            code_evidence_cited=code_evidence,
        )
        
        session.signal_comparisons.append(comparison)
        return comparison
    
    def add_failure_comparison(
        self,
        session: HumanEvaluationSession,
        failure_name: str,
        oracle_detected: bool,
        oracle_severity: float,
        oracle_propagation_confidence: float,
        human_considers_realistic: bool,
        realism_score: FailureRealism,
        production_likelihood: float,
        reasoning: str,
        propagation_path_exists: bool,
        code_evidence: Optional[str] = None,
    ) -> FailureComparison:
        """
        Record human evaluation of an ORACLE failure scenario.
        
        Args:
            session: HumanEvaluationSession to add comparison to
            failure_name: Name of the failure scenario
            oracle_detected: Whether ORACLE detected this
            oracle_severity: ORACLE's severity assessment (0.0-1.0)
            oracle_propagation_confidence: ORACLE's confidence in propagation
            human_considers_realistic: Whether human finds it realistic
            realism_score: Human's realism assessment
            production_likelihood: Human's assessment of production likelihood (0.0-1.0)
            reasoning: Why human made this assessment
            propagation_path_exists: Whether human verified path through code
            code_evidence: Files/lines demonstrating this scenario
        
        Returns:
            Created FailureComparison
        """
        comparison = FailureComparison(
            failure_name=failure_name,
            oracle_detected=oracle_detected,
            oracle_severity=oracle_severity,
            oracle_propagation_confidence=oracle_propagation_confidence,
            evaluator_role=session.evaluator_role,
            human_considers_realistic=human_considers_realistic,
            realism_score=realism_score,
            production_likelihood=production_likelihood,
            reasoning=reasoning,
            propagation_path_exists=propagation_path_exists,
            code_evidence_cited=code_evidence,
        )
        
        session.failure_comparisons.append(comparison)
        return comparison
    
    def add_viva_comparison(
        self,
        session: HumanEvaluationSession,
        question_text: str,
        oracle_generated: bool,
        oracle_specificity_score: float,
        human_accepts_question: bool,
        realism_score: VivaQuestionRealism,
        grounding_code_locations: List[str],
        reasoning: str,
        tested_against_weak_answers: bool = False,
        weak_answer_detection_rate: Optional[float] = None,
    ) -> VivaComparison:
        """
        Record human evaluation of an ORACLE viva question.
        
        Args:
            session: HumanEvaluationSession to add comparison to
            question_text: The viva question
            oracle_generated: Whether ORACLE generated this
            oracle_specificity_score: ORACLE's specificity score (0.0-1.0)
            human_accepts_question: Would this appear in real interviews?
            realism_score: Human's realism assessment
            grounding_code_locations: Files/lines this question tests
            reasoning: Why human made this assessment
            tested_against_weak_answers: Whether question was tested against weak answers
            weak_answer_detection_rate: % of weak answers this question caught
        
        Returns:
            Created VivaComparison
        """
        comparison = VivaComparison(
            question_text=question_text,
            oracle_generated=oracle_generated,
            oracle_specificity_score=oracle_specificity_score,
            evaluator_role=session.evaluator_role,
            human_accepts_question=human_accepts_question,
            realism_score=realism_score,
            grounding_code_locations=grounding_code_locations,
            reasoning=reasoning,
            tested_against_weak_answers=tested_against_weak_answers,
            weak_answer_detection_rate=weak_answer_detection_rate,
        )
        
        session.viva_comparisons.append(comparison)
        return comparison
    
    def add_architectural_assessment(
        self,
        session: HumanEvaluationSession,
        oracle_analysis: str,
        oracle_confidence: float,
        human_assessment: str,
        human_agrees: bool,
        areas_disagreement: List[str],
        areas_oracle_missed: List[str],
        missing_concerns: List[str],
        reasoning: str,
        code_evidence: Optional[str] = None,
    ) -> ArchitecturalAssessment:
        """
        Record human architectural credibility assessment.
        """
        assessment = ArchitecturalAssessment(
            oracle_architectural_analysis=oracle_analysis,
            oracle_confidence_in_analysis=oracle_confidence,
            evaluator_role=session.evaluator_role,
            human_assessment=human_assessment,
            human_agrees_with_oracle=human_agrees,
            areas_of_disagreement=areas_disagreement,
            areas_oracle_missed=areas_oracle_missed,
            missing_architectural_concerns=missing_concerns,
            reasoning=reasoning,
            code_evidence=code_evidence,
        )
        
        session.architectural_assessment = assessment
        return assessment
    
    def add_execution_behavior_comparison(
        self,
        session: HumanEvaluationSession,
        analyzed_scenario: str,
        oracle_execution_trace: List[str],
        oracle_confidence: float,
        human_execution_trace: List[str],
        human_execution_accurate: bool,
        missing_steps: List[str],
        incorrectly_inferred_steps: List[str],
        reasoning: str,
        code_evidence: Optional[str] = None,
    ) -> ExecutionBehaviorComparison:
        """
        Record human evaluation of ORACLE execution behavior reasoning.
        """
        comparison = ExecutionBehaviorComparison(
            analyzed_scenario=analyzed_scenario,
            oracle_execution_trace=oracle_execution_trace,
            oracle_confidence=oracle_confidence,
            evaluator_role=session.evaluator_role,
            human_execution_trace=human_execution_trace,
            human_execution_accurate=human_execution_accurate,
            missing_steps=missing_steps,
            incorrectly_inferred_steps=incorrectly_inferred_steps,
            reasoning=reasoning,
            code_evidence=code_evidence,
        )
        
        session.execution_comparisons.append(comparison)
        return comparison
    
    def finalize_session(
        self,
        session: HumanEvaluationSession,
        oracle_usefulness: float,
        oracle_trustworthiness: float,
        overall_reasoning: str,
        duration_minutes: Optional[float] = None,
        notes: str = "",
    ) -> HumanEvaluationSession:
        """
        Finalize human evaluation session with overall assessments.
        
        Args:
            session: Session to finalize
            oracle_usefulness: 0.0-1.0, subjective utility assessment
            oracle_trustworthiness: 0.0-1.0, confidence in findings
            overall_reasoning: Overall assessment rationale
            duration_minutes: How long evaluation took
            notes: Additional notes
        
        Returns:
            Finalized session
        """
        session.oracle_usefulness = oracle_usefulness
        session.oracle_trustworthiness = oracle_trustworthiness
        session.overall_reasoning = overall_reasoning
        session.duration_minutes = duration_minutes
        session.notes = notes
        
        return session
    
    def save_session(self, session: HumanEvaluationSession) -> Path:
        """
        Save human evaluation session to JSON file.
        
        Returns:
            Path to saved file
        """
        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        filename = (
            f"human_eval_{session.repository_name}_"
            f"{session.evaluator_role.value}_{timestamp}.json"
        )
        filepath = self.results_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
        
        return filepath
    
    def generate_comparative_report(
        self,
        repository_name: str,
        sessions: List[HumanEvaluationSession],
    ) -> ComparativeValidationReport:
        """
        Generate aggregated comparative validation report across all evaluators.
        
        Args:
            repository_name: Name of repository
            sessions: List of human evaluation sessions to aggregate
        
        Returns:
            ComparativeValidationReport with aggregated metrics
        """
        if not sessions:
            raise ValueError("No sessions provided for report generation")
        
        # Aggregate signal metrics
        signal_agreements = []
        signal_false_positives = []
        signal_false_negatives = []
        signal_relevances = []
        
        for session in sessions:
            for comparison in session.signal_comparisons:
                signal_agreements.append(comparison.agreement)
                if comparison.oracle_detected and not comparison.human_considers_relevant:
                    signal_false_positives.append(True)
                if not comparison.oracle_detected and comparison.human_considers_relevant:
                    signal_false_negatives.append(True)
                
                if comparison.relevance_score == SignalRelevanceScore.CRITICAL:
                    signal_relevances.append(1.0)
                elif comparison.relevance_score == SignalRelevanceScore.RELEVANT:
                    signal_relevances.append(0.75)
                elif comparison.relevance_score == SignalRelevanceScore.TANGENTIAL:
                    signal_relevances.append(0.5)
                else:
                    signal_relevances.append(0.0)
        
        # Aggregate failure metrics
        failure_agreements = []
        failure_false_positives = []
        failure_realism_matches = []
        failure_severity_deltas = []
        
        for session in sessions:
            for comparison in session.failure_comparisons:
                failure_agreements.append(comparison.agreement)
                if comparison.oracle_detected and not comparison.human_considers_realistic:
                    failure_false_positives.append(True)
                
                if comparison.realism_agreement:
                    failure_realism_matches.append(True)
                
                failure_severity_deltas.append(abs(comparison.severity_delta))
        
        # Aggregate viva metrics
        viva_acceptances = []
        viva_realisms = []
        viva_groundings = []
        
        for session in sessions:
            for comparison in session.viva_comparisons:
                viva_acceptances.append(comparison.human_accepts_question)
                viva_realisms.append(comparison.realism_match)
                viva_groundings.append(len(comparison.grounding_code_locations) > 0)
        
        # Calculate rates (with fallback to 0.0 if no data)
        signal_agreement_rate = (
            sum(signal_agreements) / len(signal_agreements)
            if signal_agreements
            else 0.0
        )
        signal_false_positive_rate = (
            len(signal_false_positives) / len(sessions)
            if sessions
            else 0.0
        )
        signal_false_negative_rate = (
            len(signal_false_negatives) / len(sessions)
            if sessions
            else 0.0
        )
        signal_avg_relevance = (
            sum(signal_relevances) / len(signal_relevances)
            if signal_relevances
            else 0.0
        )
        
        failure_agreement_rate = (
            sum(failure_agreements) / len(failure_agreements)
            if failure_agreements
            else 0.0
        )
        failure_false_positive_rate = (
            len(failure_false_positives) / len(sessions)
            if sessions
            else 0.0
        )
        failure_realism_match_rate = (
            sum(failure_realism_matches) / len(failure_realism_matches)
            if failure_realism_matches
            else 0.0
        )
        failure_avg_severity_delta = (
            sum(failure_severity_deltas) / len(failure_severity_deltas)
            if failure_severity_deltas
            else 0.0
        )
        
        viva_acceptance_rate = (
            sum(viva_acceptances) / len(viva_acceptances)
            if viva_acceptances
            else 0.0
        )
        viva_realism_rate = (
            sum(viva_realisms) / len(viva_realisms)
            if viva_realisms
            else 0.0
        )
        viva_grounding_rate = (
            sum(viva_groundings) / len(viva_groundings)
            if viva_groundings
            else 0.0
        )
        
        # Aggregate architectural metrics
        arch_credibilities = []
        arch_agreements = []
        
        for session in sessions:
            if session.architectural_assessment:
                arch_credibilities.append(session.architectural_assessment.credibility_score)
                arch_agreements.append(session.architectural_assessment.human_agrees_with_oracle)
        
        architectural_credibility = (
            sum(arch_credibilities) / len(arch_credibilities)
            if arch_credibilities
            else None
        )
        architectural_agreement_rate = (
            sum(arch_agreements) / len(arch_agreements)
            if arch_agreements
            else None
        )
        
        # Aggregate execution behavior metrics
        exec_accuracies = []
        for session in sessions:
            for comparison in session.execution_comparisons:
                exec_accuracies.append(comparison.step_accuracy)
        
        execution_step_accuracy = (
            sum(exec_accuracies) / len(exec_accuracies)
            if exec_accuracies
            else None
        )
        
        # Calculate overall trustworthiness
        overall_usefulness = sum(s.oracle_usefulness for s in sessions) / len(sessions)
        overall_trustworthiness = sum(s.oracle_trustworthiness for s in sessions) / len(sessions)
        
        # Identify issues (hallucination clusters, weak areas)
        hallucination_clusters = self._identify_hallucination_patterns(sessions)
        weak_reasoning_areas = self._identify_weak_reasoning(sessions)
        missing_analysis = self._identify_missing_analysis(sessions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            signal_false_positive_rate,
            failure_false_positive_rate,
            viva_realism_rate,
            hallucination_clusters,
        )
        
        report = ComparativeValidationReport(
            repository_name=repository_name,
            total_evaluations=len(sessions),
            signal_agreement_rate=signal_agreement_rate,
            signal_false_positive_rate=signal_false_positive_rate,
            signal_false_negative_rate=signal_false_negative_rate,
            signal_avg_relevance=signal_avg_relevance,
            failure_agreement_rate=failure_agreement_rate,
            failure_false_positive_rate=failure_false_positive_rate,
            failure_realism_match_rate=failure_realism_match_rate,
            failure_avg_severity_delta=failure_avg_severity_delta,
            viva_acceptance_rate=viva_acceptance_rate,
            viva_realism_rate=viva_realism_rate,
            viva_grounding_rate=viva_grounding_rate,
            architectural_credibility=architectural_credibility,
            architectural_agreement_rate=architectural_agreement_rate,
            execution_step_accuracy=execution_step_accuracy,
            oracle_overall_usefulness=overall_usefulness,
            oracle_overall_trustworthiness=overall_trustworthiness,
            hallucination_clusters=hallucination_clusters,
            weak_reasoning_areas=weak_reasoning_areas,
            missing_analysis_areas=missing_analysis,
            recommendations=recommendations,
        )
        
        return report
    
    def save_report(self, report: ComparativeValidationReport) -> Path:
        """
        Save comparative validation report to JSON file.
        
        Returns:
            Path to saved file
        """
        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        filename = f"comparative_report_{report.repository_name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, "w") as f:
            f.write(report.to_json())
        
        return filepath
    
    @staticmethod
    def _identify_hallucination_patterns(sessions: List[HumanEvaluationSession]) -> List[str]:
        """Identify common hallucination patterns across evaluations."""
        hallucinations = {}
        
        for session in sessions:
            for comparison in session.signal_comparisons:
                if comparison.oracle_detected and not comparison.human_considers_relevant:
                    hallucinations[comparison.signal_name] = hallucinations.get(comparison.signal_name, 0) + 1
            
            for comparison in session.failure_comparisons:
                if comparison.oracle_detected and not comparison.human_considers_realistic:
                    hallucinations[comparison.failure_name] = hallucinations.get(comparison.failure_name, 0) + 1
        
        # Return most common hallucinations (2+ evaluators reported)
        return [name for name, count in hallucinations.items() if count >= 2]
    
    @staticmethod
    def _identify_weak_reasoning(sessions: List[HumanEvaluationSession]) -> List[str]:
        """Identify areas where ORACLE's reasoning is weak."""
        weak_areas = {}
        
        for session in sessions:
            # Weak signal reasoning
            for comparison in session.signal_comparisons:
                if not comparison.agreement and comparison.oracle_confidence > 0.5:
                    weak_areas[f"Signal: {comparison.signal_name}"] = (
                        weak_areas.get(f"Signal: {comparison.signal_name}", 0) + 1
                    )
            
            # Weak failure reasoning
            for comparison in session.failure_comparisons:
                if not comparison.realism_agreement and comparison.oracle_propagation_confidence > 0.5:
                    weak_areas[f"Failure: {comparison.failure_name}"] = (
                        weak_areas.get(f"Failure: {comparison.failure_name}", 0) + 1
                    )
        
        return [area for area, count in weak_areas.items() if count >= 2]
    
    @staticmethod
    def _identify_missing_analysis(sessions: List[HumanEvaluationSession]) -> List[str]:
        """Identify significant analysis gaps."""
        missing = {}
        
        for session in sessions:
            if session.architectural_assessment:
                for area in session.architectural_assessment.areas_oracle_missed:
                    missing[area] = missing.get(area, 0) + 1
        
        return [area for area, count in missing.items() if count >= 2]
    
    @staticmethod
    def _generate_recommendations(
        signal_fp_rate: float,
        failure_fp_rate: float,
        viva_realism: float,
        hallucinations: List[str],
    ) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        if signal_fp_rate > 0.3:
            recommendations.append(
                f"Signal false-positive rate ({signal_fp_rate:.1%}) is high. "
                "Refine signal confidence thresholds or detection patterns."
            )
        
        if failure_fp_rate > 0.25:
            recommendations.append(
                f"Failure hallucination rate ({failure_fp_rate:.1%}) exceeds acceptable. "
                "Validate propagation paths more rigorously."
            )
        
        if viva_realism < 0.75:
            recommendations.append(
                f"Viva realism rate ({viva_realism:.1%}) is low. "
                "Filter out textbook and speculative questions."
            )
        
        if hallucinations:
            recommendations.append(
                f"Common hallucinations detected: {', '.join(hallucinations[:3])}. "
                "Add patterns to rejection filters."
            )
        
        return recommendations
