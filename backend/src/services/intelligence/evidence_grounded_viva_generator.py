"""
Evidence-Grounded Viva Intelligence Generator:
Creates viva questions based on actual failure scenarios, execution graph patterns,
and implementation-specific evidence from the codebase.

Philosophy: Questions should resemble senior-engineer code reviews, not textbook trivia.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from ...models.context import VivaTarget


@dataclass
class CodeGroundedVivaQuestion:
    """
    A viva question grounded in specific code evidence.
    """
    topic: str
    question: str
    implementation_context: str  # What in the code prompted this question
    evidence_files: List[str]
    expected_knowledge: str  # What engineer should understand
    difficulty: str


class EvidenceGroundedVivaGenerator:
    """
    Generates viva questions based on:
    - Actual failure scenarios detected
    - Observable signals and risk patterns
    - Execution graph dependencies
    - Implementation evidence
    - Operational context
    
    All questions must be traceable to specific code patterns.
    """

    @staticmethod
    def generate_questions(
        failure_scenarios: List[Any],
        observable_signals: Dict[str, List[Any]],
        detections: Dict[str, Any],
        repo_path: str
    ) -> List[VivaTarget]:
        """
        Generate viva targets from concrete evidence.
        """
        questions = []

        # 1. Failure scenario questions
        questions.extend(
            EvidenceGroundedVivaGenerator._generate_failure_scenario_questions(failure_scenarios)
        )

        # 2. Observable signal questions
        questions.extend(
            EvidenceGroundedVivaGenerator._generate_signal_based_questions(observable_signals)
        )

        # 3. Technology-specific questions
        questions.extend(
            EvidenceGroundedVivaGenerator._generate_technology_questions(detections)
        )

        # 4. Architecture pattern questions
        questions.extend(
            EvidenceGroundedVivaGenerator._generate_architecture_questions(observable_signals)
        )

        return questions

    @staticmethod
    def _generate_failure_scenario_questions(failure_scenarios: List[Any]) -> List[VivaTarget]:
        """Questions based on detected failure scenarios."""
        questions = []

        for scenario in failure_scenarios:
            if scenario.propagation_risk == "critical":
                question_text = f"Walk me through what happens when {scenario.trigger.lower()}. " \
                               f"How does your system respond? What code paths are affected?"
                
                questions.append(VivaTarget(
                    topic=scenario.scenario_name,
                    question_target=f"Runtime Behavior - {scenario.scenario_name}",
                    difficulty="hard",
                    importance_score=0.95 if scenario.propagation_risk == "critical" else 0.85,
                    focus=question_text
                ))

            elif scenario.propagation_risk == "high":
                if not scenario.recovery_possible:
                    question_text = f"How does your system handle {scenario.trigger.lower()}? " \
                                   f"What's your recovery strategy?"
                else:
                    question_text = f"If {scenario.trigger.lower()}, what's the recovery mechanism? " \
                                   f"Show me the code that implements it."

                questions.append(VivaTarget(
                    topic=scenario.scenario_name,
                    question_target=f"Resilience - {scenario.scenario_name}",
                    difficulty="hard",
                    importance_score=0.85,
                    focus=question_text
                ))

        return questions

    @staticmethod
    def _generate_signal_based_questions(observable_signals: Dict[str, List[Any]]) -> List[VivaTarget]:
        """Questions based on observable signals and detected risks."""
        questions = []

        # Error handling signals
        error_signals = observable_signals.get("error_handling", [])
        for signal in error_signals:
            if signal.risk_level == "high" or signal.risk_level == "medium":
                question = VivaTarget(
                    topic="Error Handling",
                    question_target=signal.signal_name,
                    difficulty="medium",
                    importance_score=0.8,
                    focus=f"Your codebase shows: {signal.description}. How do you ensure all errors are handled consistently?"
                )
                questions.append(question)

        # Resilience signals
        resilience_signals = observable_signals.get("resilience_patterns", [])
        if not any("Circuit Breaker" in str(s.signal_name) for s in resilience_signals):
            question = VivaTarget(
                topic="Fault Tolerance",
                question_target="Missing Circuit Breaker",
                difficulty="hard",
                importance_score=0.85,
                focus="I don't see circuit breaker patterns in your code. How do you prevent cascading failures when external dependencies become slow?"
            )
            questions.append(question)

        # Auth signals
        auth_signals = observable_signals.get("auth_consistency", [])
        if not any("Centralized" in str(s.signal_name) for s in auth_signals):
            question = VivaTarget(
                topic="Authentication",
                question_target="Auth Consistency",
                difficulty="hard",
                importance_score=0.9,
                focus="I see auth checks scattered across your codebase. How do you ensure authentication is enforced consistently across all endpoints?"
            )
            questions.append(question)

        # Observability signals
        obs_signals = observable_signals.get("observability", [])
        if not any("Tracing" in str(s.signal_name) for s in obs_signals):
            question = VivaTarget(
                topic="Observability",
                question_target="Distributed Tracing",
                difficulty="medium",
                importance_score=0.7,
                focus="How do you debug multi-service issues in production? What's your tracing strategy?"
            )
            questions.append(question)

        return questions

    @staticmethod
    def _generate_technology_questions(detections: Dict[str, Any]) -> List[VivaTarget]:
        """Questions grounded in specific tech choices."""
        questions = []

        # Database-specific
        db = detections.get("database_used", {})
        if db and hasattr(db, 'value'):
            if "MongoDB" in str(db.value):
                questions.append(VivaTarget(
                    topic="Database Design",
                    question_target="NoSQL Transactions",
                    difficulty="hard",
                    importance_score=0.8,
                    focus="You're using MongoDB. How do you handle transactions across multiple documents? What's your strategy for maintaining consistency?"
                ))

            elif "PostgreSQL" in str(db.value):
                questions.append(VivaTarget(
                    topic="Database Performance",
                    question_target="Query Optimization",
                    difficulty="hard",
                    importance_score=0.75,
                    focus="Show me your most expensive PostgreSQL queries. How are they optimized? What indexes are in place?"
                ))

        # Backend framework
        backend = detections.get("backend_framework", {})
        if backend and hasattr(backend, 'value'):
            if "FastAPI" in str(backend.value):
                questions.append(VivaTarget(
                    topic="Async Performance",
                    question_target="FastAPI Concurrency",
                    difficulty="hard",
                    importance_score=0.75,
                    focus="You're using FastAPI. How many concurrent requests can your system handle before saturating? Where's the bottleneck - I/O, CPU, or connection limits?"
                ))

        return questions

    @staticmethod
    def _generate_architecture_questions(observable_signals: Dict[str, List[Any]]) -> List[VivaTarget]:
        """Questions grounded in observable architecture patterns."""
        questions = []

        arch_signals = observable_signals.get("architecture", [])
        for signal in arch_signals:
            if "Partial Layer Separation" in str(signal.signal_name):
                questions.append(VivaTarget(
                    topic="Architecture Design",
                    question_target="Layer Separation",
                    difficulty="medium",
                    importance_score=0.7,
                    focus=f"Your code shows: {signal.description}. Walk me through how you separate concerns between business logic, persistence, and presentation layers."
                ))

        return questions

    @staticmethod
    def format_viva_targets_for_interview(viva_targets: List[VivaTarget]) -> str:
        """Format viva targets into interview guide."""
        report = []
        report.append("=" * 80)
        report.append("CODE-GROUNDED VIVA INTERVIEW GUIDE")
        report.append("=" * 80)
        report.append("")

        # Group by difficulty
        by_difficulty = {"easy": [], "medium": [], "hard": []}
        for target in viva_targets:
            by_difficulty[target.difficulty].append(target)

        for difficulty in ["easy", "medium", "hard"]:
            if by_difficulty[difficulty]:
                report.append(f"\n{difficulty.upper()} QUESTIONS")
                report.append("-" * 40)

                for i, target in enumerate(by_difficulty[difficulty], 1):
                    report.append(f"\n{i}. [{target.topic}] {target.question_target}")
                    report.append(f"   Focus: {target.focus}")
                    report.append(f"   Importance: {int(target.importance_score * 100)}%")

        report.append("\n" + "=" * 80)
        return "\n".join(report)
