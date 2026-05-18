"""Comparative Evaluation Runner: Compare ORACLE Intelligence Against Human Reviewers

This module orchestrates the comparison of ORACLE-generated analysis against real human
engineering evaluations. It computes agreement metrics, identifies hallucinations, and
measures trustworthiness.

Process:
1. Run ORACLE analysis on a repository
2. Collect human evaluations (from dataset)
3. Compare signal-by-signal, scenario-by-scenario, question-by-question
4. Compute precision/recall agreement metrics
5. Generate trustworthiness assessment
6. Flag hallucinations and speculative reasoning
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

from human_evaluator_models import (
    ComparativeSignalAnalysis,
    ComparativeFailureAnalysis,
    ComparativeVivaAnalysis,
    ComparativeAgreementMetrics,
    HumanSignalEvaluation,
    HumanFailureScenarioEvaluation,
    HumanVivaQuestionEvaluation,
    HumanReviewDatapoint,
    ReviewerRole,
    SignalAccuracy,
    FailureScenarioAccuracy,
    VivaQuestionQuality,
    ExecutionBehaviorSignal,
    ExecutionGraphFailureTrace,
    OperationalRealism,
)
from failure_corpus import FAILURE_CORPUS, FailureCorpusRepository


logger = logging.getLogger(__name__)


class ComparativeSignalEvaluator:
    """Evaluates ORACLE signal detection against human assessments"""
    
    def compare_signal(
        self,
        oracle_signal_name: str,
        oracle_confidence: float,
        human_evaluations: List[HumanSignalEvaluation],
    ) -> ComparativeSignalAnalysis:
        """Compare single ORACLE signal against multiple human evaluations"""
        
        analysis = ComparativeSignalAnalysis(
            signal_name=oracle_signal_name,
            oracle_detected=True,
            human_mentioned=any(
                eval.human_verdict in [SignalAccuracy.ACCURATE, SignalAccuracy.INCOMPLETE]
                for eval in human_evaluations
            ),
            human_evaluations=human_evaluations,
        )
        
        # Calculate agreement metrics
        total_humans = len(human_evaluations)
        
        accurate_count = sum(
            1 for eval in human_evaluations
            if eval.human_verdict == SignalAccuracy.ACCURATE
        )
        
        hallucinated_count = sum(
            1 for eval in human_evaluations
            if eval.human_verdict == SignalAccuracy.HALLUCINATED
        )
        
        analysis.accuracy_rate = accurate_count / total_humans if total_humans > 0 else 0.0
        
        # Check if consensus
        if analysis.accuracy_rate >= 0.75:
            analysis.oracle_was_correct = True
            analysis.consensus = f"Signal {oracle_signal_name} accurately identified ({analysis.accuracy_rate:.1%} agreement)"
        elif hallucinated_count / total_humans >= 0.75:
            analysis.oracle_was_correct = False
            analysis.consensus = f"Signal is hallucinated ({hallucinated_count}/{total_humans} humans flagged)"
            analysis.false_positive = True
        else:
            analysis.consensus = f"Mixed evaluation: {accurate_count} accurate, {hallucinated_count} hallucinated"
        
        # Importance alignment: correlation between ORACLE confidence and human realism scores
        human_importance = sum(eval.realism_score for eval in human_evaluations) / total_humans
        analysis.importance_alignment = min(oracle_confidence, human_importance) / max(oracle_confidence, human_importance) if max(oracle_confidence, human_importance) > 0 else 0.0
        
        return analysis
    
    def evaluate_signal_set(
        self,
        oracle_signals: Dict[str, float],  # signal_name -> confidence
        human_signal_evaluations: Dict[str, List[HumanSignalEvaluation]],
    ) -> Tuple[List[ComparativeSignalAnalysis], Dict[str, Any]]:
        """Evaluate full set of signals"""
        
        analyses = []
        metrics = {
            "total_oracle_signals": len(oracle_signals),
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "precision": 0.0,
            "recall": 0.0,
            "agreement_rate": 0.0,
        }
        
        # Analyze each oracle signal
        for signal_name, confidence in oracle_signals.items():
            human_evals = human_signal_evaluations.get(signal_name, [])
            if human_evals:
                analysis = self.compare_signal(signal_name, confidence, human_evals)
                analyses.append(analysis)
                
                if analysis.oracle_was_correct:
                    metrics["true_positives"] += 1
                elif analysis.false_positive:
                    metrics["false_positives"] += 1
        
        # Check for human-identified signals oracle missed
        for signal_name, human_evals in human_signal_evaluations.items():
            if signal_name not in oracle_signals:
                # Check if humans agreed this should have been found
                important_evals = [e for e in human_evals if e.realism_score > 0.7]
                if len(important_evals) > len(human_evals) * 0.5:  # Majority said it's important
                    metrics["false_negatives"] += 1
        
        # Calculate precision/recall
        tp = metrics["true_positives"]
        fp = metrics["false_positives"]
        fn = metrics["false_negatives"]
        
        if tp + fp > 0:
            metrics["precision"] = tp / (tp + fp)
        if tp + fn > 0:
            metrics["recall"] = tp / (tp + fn)
        
        metrics["agreement_rate"] = sum(
            1 for a in analyses if a.oracle_was_correct
        ) / len(analyses) if analyses else 0.0
        
        return analyses, metrics


class ComparativeFailureEvaluator:
    """Evaluates ORACLE failure scenario analysis against human assessments"""
    
    def compare_failure_scenario(
        self,
        oracle_scenario_name: str,
        oracle_severity: str,
        human_evaluations: List[HumanFailureScenarioEvaluation],
    ) -> ComparativeFailureAnalysis:
        """Compare single failure scenario"""
        
        analysis = ComparativeFailureAnalysis(
            scenario_name=oracle_scenario_name,
            oracle_identified=True,
            human_identified=any(
                eval.human_verdict in [
                    FailureScenarioAccuracy.REALISTIC,
                    FailureScenarioAccuracy.OVERLY_PESSIMISTIC,
                ]
                for eval in human_evaluations
            ),
            human_evaluations=human_evaluations,
        )
        
        total_humans = len(human_evaluations)
        
        realistic_count = sum(
            1 for eval in human_evaluations
            if eval.human_verdict == FailureScenarioAccuracy.REALISTIC
        )
        
        speculative_count = sum(
            1 for eval in human_evaluations
            if eval.human_verdict == FailureScenarioAccuracy.SPECULATIVE
        )
        
        analysis.realism_rate = realistic_count / total_humans if total_humans > 0 else 0.0
        
        # Check severity alignment
        severity_alignment_count = sum(
            1 for eval in human_evaluations
            if eval.actual_severity == oracle_severity
        )
        analysis.severity_alignment = severity_alignment_count / total_humans
        
        # Propagation and recovery accuracy
        analysis.propagation_accuracy = sum(
            eval.propagation_realism for eval in human_evaluations
        ) / total_humans if total_humans > 0 else 0.0
        
        analysis.recovery_accuracy = sum(
            eval.recovery_realism for eval in human_evaluations
        ) / total_humans if total_humans > 0 else 0.0
        
        # Determine verdict
        if analysis.realism_rate >= 0.7:
            analysis.oracle_was_realistic = True
            analysis.consensus = f"Scenario realistic ({analysis.realism_rate:.1%})"
        elif speculative_count / total_humans >= 0.7:
            analysis.oracle_was_realistic = False
            analysis.consensus = f"Scenario speculative ({speculative_count}/{total_humans} flagged)"
        else:
            analysis.consensus = "Mixed evaluation of realism"
        
        return analysis
    
    def evaluate_failure_set(
        self,
        oracle_scenarios: Dict[str, str],  # scenario_name -> severity
        human_scenario_evaluations: Dict[str, List[HumanFailureScenarioEvaluation]],
    ) -> Tuple[List[ComparativeFailureAnalysis], Dict[str, Any]]:
        """Evaluate full set of failure scenarios"""
        
        analyses = []
        metrics = {
            "total_oracle_scenarios": len(oracle_scenarios),
            "realistic": 0,
            "speculative": 0,
            "realism_rate": 0.0,
            "severity_accuracy": 0.0,
            "propagation_accuracy": 0.0,
        }
        
        for scenario_name, severity in oracle_scenarios.items():
            human_evals = human_scenario_evaluations.get(scenario_name, [])
            if human_evals:
                analysis = self.compare_failure_scenario(
                    scenario_name, severity, human_evals
                )
                analyses.append(analysis)
                
                if analysis.oracle_was_realistic:
                    metrics["realistic"] += 1
                else:
                    metrics["speculative"] += 1
        
        if metrics["total_oracle_scenarios"] > 0:
            metrics["realism_rate"] = metrics["realistic"] / metrics["total_oracle_scenarios"]
            metrics["severity_accuracy"] = sum(
                a.severity_alignment for a in analyses
            ) / len(analyses) if analyses else 0.0
            metrics["propagation_accuracy"] = sum(
                a.propagation_accuracy for a in analyses
            ) / len(analyses) if analyses else 0.0
        
        return analyses, metrics


class ComparativeVivaEvaluator:
    """Evaluates ORACLE viva questions against human assessments"""
    
    def compare_viva_question(
        self,
        oracle_question: str,
        human_evaluations: List[HumanVivaQuestionEvaluation],
    ) -> ComparativeVivaAnalysis:
        """Compare single viva question"""
        
        analysis = ComparativeVivaAnalysis(
            question_text=oracle_question,
            human_evaluations=human_evaluations,
        )
        
        total_humans = len(human_evaluations)
        
        # Detect quality issues
        generic_count = sum(
            1 for eval in human_evaluations
            if VivaQuestionQuality.TEXTBOOK_GENERIC in eval.human_verdict
        )
        
        implementation_count = sum(
            1 for eval in human_evaluations
            if (VivaQuestionQuality.IMPLEMENTATION_DEEP_DIVE in eval.human_verdict
                or VivaQuestionQuality.ARCHITECTURAL_INSIGHT in eval.human_verdict)
        )
        
        # Quality metrics
        analysis.quality_rate = (total_humans - generic_count) / total_humans if total_humans > 0 else 0.0
        
        analysis.code_specificity = sum(
            eval.code_specificity_score for eval in human_evaluations
        ) / total_humans if total_humans > 0 else 0.0
        
        analysis.distinguishes_levels = sum(
            1 for eval in human_evaluations
            if eval.distinguishes_senior_engineer
        ) / total_humans if total_humans > 0 else 0.0
        
        analysis.would_ask_in_interview = sum(
            1 for eval in human_evaluations
            if not any(bad_quality in eval.human_verdict for bad_quality in [
                VivaQuestionQuality.TEXTBOOK_GENERIC,
                VivaQuestionQuality.TOO_SIMPLE,
                VivaQuestionQuality.TOO_VAGUE,
            ])
        ) / total_humans if total_humans > 0 else 0.0
        
        if generic_count / total_humans >= 0.75:
            analysis.textbook_pattern_detected = True
            analysis.oracle_question_good = False
            analysis.consensus = f"Question detected as textbook/generic ({generic_count}/{total_humans} flagged)"
        elif analysis.quality_rate >= 0.7:
            analysis.oracle_question_good = True
            analysis.consensus = f"Good question ({analysis.quality_rate:.1%} rated as quality)"
        else:
            analysis.consensus = "Mixed quality evaluation"
        
        return analysis
    
    def evaluate_viva_questions(
        self,
        oracle_questions: List[str],
        human_question_evaluations: Dict[str, List[HumanVivaQuestionEvaluation]],
    ) -> Tuple[List[ComparativeVivaAnalysis], Dict[str, Any]]:
        """Evaluate full set of viva questions"""
        
        analyses = []
        metrics = {
            "total_questions": len(oracle_questions),
            "quality_questions": 0,
            "generic_questions": 0,
            "avg_quality_rate": 0.0,
            "avg_code_specificity": 0.0,
            "avg_distinguish_levels": 0.0,
        }
        
        for question in oracle_questions:
            human_evals = human_question_evaluations.get(question, [])
            if human_evals:
                analysis = self.compare_viva_question(question, human_evals)
                analyses.append(analysis)
                
                if analysis.oracle_question_good:
                    metrics["quality_questions"] += 1
                else:
                    metrics["generic_questions"] += 1
        
        if analyses:
            metrics["avg_quality_rate"] = sum(a.quality_rate for a in analyses) / len(analyses)
            metrics["avg_code_specificity"] = sum(a.code_specificity for a in analyses) / len(analyses)
            metrics["avg_distinguish_levels"] = sum(a.distinguishes_levels for a in analyses) / len(analyses)
        
        return analyses, metrics


class TrustworthinessAuditor:
    """Audits ORACLE reasoning for unsupported assumptions and hallucinations"""
    
    def audit_signal_analysis(
        self,
        signal_analyses: List[ComparativeSignalAnalysis],
    ) -> Dict[str, Any]:
        """Audit signal analysis for hallucinations and weak reasoning"""
        
        audit = {
            "hallucinations": [],
            "weak_confidence": [],
            "unsupported_assumptions": [],
            "score": 1.0,
        }
        
        for analysis in signal_analyses:
            if analysis.false_positive:
                audit["hallucinations"].append({
                    "signal": analysis.signal_name,
                    "reason": "Detected by ORACLE but rejected by humans",
                })
                audit["score"] *= 0.9
            
            if analysis.importance_alignment < 0.5:
                audit["weak_confidence"].append({
                    "signal": analysis.signal_name,
                    "oracle_confidence": max(a.oracle_confidence for a in analysis.human_evaluations) if analysis.human_evaluations else 0,
                    "human_importance": sum(a.realism_score for a in analysis.human_evaluations) / len(analysis.human_evaluations) if analysis.human_evaluations else 0,
                })
                audit["score"] *= 0.95
        
        return audit
    
    def audit_failure_analysis(
        self,
        failure_analyses: List[ComparativeFailureAnalysis],
    ) -> Dict[str, Any]:
        """Audit failure analysis for speculative reasoning"""
        
        audit = {
            "speculative_scenarios": [],
            "unrealistic_severity": [],
            "poor_propagation_models": [],
            "score": 1.0,
        }
        
        for analysis in failure_analyses:
            if not analysis.oracle_was_realistic:
                audit["speculative_scenarios"].append({
                    "scenario": analysis.scenario_name,
                    "realism_rate": analysis.realism_rate,
                })
                audit["score"] *= 0.8
            
            if analysis.severity_alignment < 0.5:
                audit["unrealistic_severity"].append({
                    "scenario": analysis.scenario_name,
                    "alignment": analysis.severity_alignment,
                })
                audit["score"] *= 0.9
            
            if analysis.propagation_accuracy < 0.6:
                audit["poor_propagation_models"].append({
                    "scenario": analysis.scenario_name,
                    "accuracy": analysis.propagation_accuracy,
                })
                audit["score"] *= 0.85
        
        return audit
    
    def audit_viva_quality(
        self,
        viva_analyses: List[ComparativeVivaAnalysis],
    ) -> Dict[str, Any]:
        """Audit viva questions for generic/textbook patterns"""
        
        audit = {
            "textbook_questions": [],
            "non_specific_questions": [],
            "weak_engineering_questions": [],
            "score": 1.0,
        }
        
        for analysis in viva_analyses:
            if analysis.textbook_pattern_detected:
                audit["textbook_questions"].append({
                    "question": analysis.question_text[:50] + "...",
                    "quality_rate": analysis.quality_rate,
                })
                audit["score"] *= 0.85
            
            if analysis.code_specificity < 0.5:
                audit["non_specific_questions"].append({
                    "question": analysis.question_text[:50] + "...",
                    "specificity": analysis.code_specificity,
                })
                audit["score"] *= 0.9
            
            if not analysis.distinguishes_levels:
                audit["weak_engineering_questions"].append({
                    "question": analysis.question_text[:50] + "...",
                })
                audit["score"] *= 0.8
        
        return audit
    
    def generate_comprehensive_audit(
        self,
        signal_analyses: List[ComparativeSignalAnalysis],
        failure_analyses: List[ComparativeFailureAnalysis],
        viva_analyses: List[ComparativeVivaAnalysis],
    ) -> Dict[str, Any]:
        """Generate comprehensive trustworthiness audit"""
        
        signal_audit = self.audit_signal_analysis(signal_analyses)
        failure_audit = self.audit_failure_analysis(failure_analyses)
        viva_audit = self.audit_viva_quality(viva_analyses)
        
        overall_trustworthiness = (
            signal_audit["score"] * 0.33 +
            failure_audit["score"] * 0.33 +
            viva_audit["score"] * 0.34
        )
        
        return {
            "overall_trustworthiness_score": max(0.0, min(1.0, overall_trustworthiness)),
            "ready_for_production": overall_trustworthiness >= 0.80,
            "signal_audit": signal_audit,
            "failure_audit": failure_audit,
            "viva_audit": viva_audit,
            "timestamp": datetime.now().isoformat(),
        }


class ComparativeEvaluationRunner:
    """Orchestrates full comparative evaluation"""
    
    def __init__(self):
        self.signal_evaluator = ComparativeSignalEvaluator()
        self.failure_evaluator = ComparativeFailureEvaluator()
        self.viva_evaluator = ComparativeVivaEvaluator()
        self.auditor = TrustworthinessAuditor()
    
    def run_comparative_evaluation(
        self,
        repository_name: str,
        oracle_analysis: Dict[str, Any],  # ORACLE generated analysis
        human_evaluation_dataset: List[HumanReviewDatapoint],
    ) -> ComparativeAgreementMetrics:
        """Run full comparative evaluation"""
        
        logger.info(f"Starting comparative evaluation for {repository_name}")
        
        # Extract human evaluations by category
        human_signal_evals = self._extract_signal_evaluations(human_evaluation_dataset)
        human_failure_evals = self._extract_failure_evaluations(human_evaluation_dataset)
        human_viva_evals = self._extract_viva_evaluations(human_evaluation_dataset)
        
        # Compare signals
        signal_analyses, signal_metrics = self.signal_evaluator.evaluate_signal_set(
            oracle_analysis.get("signals", {}),
            human_signal_evals,
        )
        
        # Compare failures
        failure_analyses, failure_metrics = self.failure_evaluator.evaluate_failure_set(
            oracle_analysis.get("failure_scenarios", {}),
            human_failure_evals,
        )
        
        # Compare viva
        viva_analyses, viva_metrics = self.viva_evaluator.evaluate_viva_questions(
            oracle_analysis.get("viva_questions", []),
            human_viva_evals,
        )
        
        # Audit trustworthiness
        audit = self.auditor.generate_comprehensive_audit(
            signal_analyses,
            failure_analyses,
            viva_analyses,
        )
        
        # Build metrics report
        metrics = ComparativeAgreementMetrics(
            repository_name=repository_name,
            evaluation_date=datetime.now(),
            total_human_datapoints=len(human_evaluation_dataset),
            
            signals_human_mentioned=signal_metrics.get("human_signals", 0),
            signals_oracle_detected=signal_metrics.get("total_oracle_signals", 0),
            signals_true_positives=signal_metrics.get("true_positives", 0),
            signals_false_positives=signal_metrics.get("false_positives", 0),
            signals_false_negatives=signal_metrics.get("false_negatives", 0),
            signal_precision=signal_metrics.get("precision", 0.0),
            signal_recall=signal_metrics.get("recall", 0.0),
            signal_agreement=signal_metrics.get("agreement_rate", 0.0),
            
            scenarios_human_mentioned=failure_metrics.get("human_scenarios", 0),
            scenarios_oracle_identified=failure_metrics.get("total_oracle_scenarios", 0),
            scenarios_true_positives=failure_metrics.get("realistic", 0),
            scenarios_false_positives=failure_metrics.get("speculative", 0),
            scenarios_realism_agreement=failure_metrics.get("realism_rate", 0.0),
            failure_precision=failure_metrics.get("realistic", 0) / max(1, failure_metrics.get("total_oracle_scenarios", 1)),
            
            viva_questions_generated=viva_metrics.get("total_questions", 0),
            viva_questions_evaluated=len(viva_analyses),
            viva_quality_rate=viva_metrics.get("avg_quality_rate", 0.0),
            viva_specificity=viva_metrics.get("avg_code_specificity", 0.0),
            viva_distinguishes_levels=viva_metrics.get("avg_distinguish_levels", 0.0),
            
            oracle_trustworthiness=audit["overall_trustworthiness_score"],
            ready_for_production=audit["ready_for_production"],
            hallucinations_detected=[h["signal"] for h in audit["signal_audit"]["hallucinations"]],
            speculation_detected=[s["scenario"] for s in audit["failure_audit"]["speculative_scenarios"]],
        )
        
        logger.info(f"Evaluation complete: {metrics.oracle_trustworthiness:.1%} trustworthy")
        return metrics
    
    def _extract_signal_evaluations(
        self,
        datapoints: List[HumanReviewDatapoint],
    ) -> Dict[str, List[HumanSignalEvaluation]]:
        """Extract signal evaluations from human datapoints"""
        # This would be populated from actual human evaluation data
        return {}
    
    def _extract_failure_evaluations(
        self,
        datapoints: List[HumanReviewDatapoint],
    ) -> Dict[str, List[HumanFailureScenarioEvaluation]]:
        """Extract failure evaluations from human datapoints"""
        return {}
    
    def _extract_viva_evaluations(
        self,
        datapoints: List[HumanReviewDatapoint],
    ) -> Dict[str, List[HumanVivaQuestionEvaluation]]:
        """Extract viva evaluations from human datapoints"""
        return {}
