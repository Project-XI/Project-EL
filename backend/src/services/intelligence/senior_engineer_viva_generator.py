"""
Senior Engineer Viva Generator: Creates implementation-aware viva questions 
that resemble senior-engineer code reviews rather than textbook questions.
"""

from typing import Dict, Any, List
from ...models.context import VivaTarget, EvidenceModel


class SeniorEngineerVivaGenerator:
    """
    Generates viva intelligence questions at senior-engineer level:
    - Architecture review questions
    - Failure scenario questions
    - Scalability and performance questions
    - Security and resilience questions
    - Operational and maintainability questions
    - Technology tradeoff questions
    """

    @staticmethod
    def generate_viva_targets(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any],
        failure_analysis: Dict[str, EvidenceModel],
        tradeoff_analysis: List[EvidenceModel]
    ) -> List[VivaTarget]:
        """
        Generate comprehensive viva targets focused on engineering depth.
        """
        targets = []

        # ===== Architecture Review Questions =====
        targets.extend(SeniorEngineerVivaGenerator._generate_architecture_questions(
            detections, quality_analysis, context_enrichment
        ))

        # ===== Failure Scenario Questions =====
        targets.extend(SeniorEngineerVivaGenerator._generate_failure_questions(
            failure_analysis, quality_analysis
        ))

        # ===== Scalability & Performance Questions =====
        targets.extend(SeniorEngineerVivaGenerator._generate_scalability_questions(
            context_enrichment, quality_analysis, detections
        ))

        # ===== Security Questions =====
        targets.extend(SeniorEngineerVivaGenerator._generate_security_questions(
            detections, quality_analysis
        ))

        # ===== Operational Questions =====
        targets.extend(SeniorEngineerVivaGenerator._generate_operational_questions(
            context_enrichment, quality_analysis
        ))

        # ===== Technology Choice Questions =====
        targets.extend(SeniorEngineerVivaGenerator._generate_technology_questions(
            detections, tradeoff_analysis, context_enrichment
        ))

        return targets

    @staticmethod
    def _generate_architecture_questions(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> List[VivaTarget]:
        """Architecture and design-level questions."""
        questions = []

        separation = quality_analysis.get("architecture_separation", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Clear layered" in separation.value or "Partial layering" in separation.value:
            questions.append(VivaTarget(
                topic="Architecture & Design",
                question_target="Layered Architecture",
                difficulty="medium",
                importance_score=0.85,
                focus="Walk me through your architectural layers. How do you enforce separation between models, services, and controllers?"
            ))

        api_quality = quality_analysis.get("api_design_quality", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Swagger" in api_quality.value or "API versioning" in api_quality.value:
            questions.append(VivaTarget(
                topic="API Design",
                question_target="REST API Design",
                difficulty="medium",
                importance_score=0.8,
                focus="How do you design your API contracts for backward compatibility? What's your versioning strategy?"
            ))

        if "Pagination" in api_quality.value:
            questions.append(VivaTarget(
                topic="API Performance",
                question_target="Pagination & Filtering",
                difficulty="medium",
                importance_score=0.75,
                focus="Explain your pagination strategy. What's the performance impact of large offsets?"
            ))

        code_reuse = quality_analysis.get("code_duplication", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Potential duplication" in code_reuse.value:
            questions.append(VivaTarget(
                topic="Code Quality",
                question_target="Code Reusability",
                difficulty="hard",
                importance_score=0.7,
                focus="I noticed repetitive patterns in your codebase. How would you extract and consolidate them?"
            ))

        return questions

    @staticmethod
    def _generate_failure_questions(
        failure_analysis: Dict[str, EvidenceModel],
        quality_analysis: Dict[str, EvidenceModel]
    ) -> List[VivaTarget]:
        """Failure scenario and resilience questions."""
        questions = []

        db_risk = failure_analysis.get("database_failure_risk", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "HIGH" in str(db_risk.value) or "CRITICAL" in str(db_risk.value):
            questions.append(VivaTarget(
                topic="Database Resilience",
                question_target="Database Failure Handling",
                difficulty="hard",
                importance_score=0.95,
                focus="What happens if your database becomes unavailable? Walk through the failure scenario and recovery."
            ))

        cache = quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Redis" in cache.value or "Memcached" in cache.value:
            questions.append(VivaTarget(
                topic="Cache Management",
                question_target="Cache Failure Impact",
                difficulty="hard",
                importance_score=0.9,
                focus="If your cache layer fails suddenly, what breaks? How do you prevent cache stampede?"
            ))

        auth = quality_analysis.get("authentication_consistency", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Centralized" in auth.value:
            questions.append(VivaTarget(
                topic="Authentication Security",
                question_target="Middleware Failure",
                difficulty="hard",
                importance_score=0.9,
                focus="What happens if your auth middleware throws an exception on every request? How does the system respond?"
            ))

        resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Circuit breaker" not in resilience.value:
            questions.append(VivaTarget(
                topic="External Dependencies",
                question_target="Upstream Failure Propagation",
                difficulty="hard",
                importance_score=0.85,
                focus="If an external API becomes slow/unresponsive, what happens to your application?"
            ))

        return questions

    @staticmethod
    def _generate_scalability_questions(
        context_enrichment: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        detections: Dict[str, Any]
    ) -> List[VivaTarget]:
        """Scalability and performance questions."""
        questions = []

        scale = context_enrichment.get("scalability_expectations", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])).value
        
        if "High-scale" in scale or "Medium-to-high" in scale:
            cache = quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
            if "No caching" in cache.value or cache.confidence < 0.3:
                questions.append(VivaTarget(
                    topic="Scalability & Performance",
                    question_target="Database Query Optimization",
                    difficulty="hard",
                    importance_score=0.9,
                    focus="Your project targets high scale but lacks caching. How will you handle database load at 10x current traffic?"
                ))

        backend = detections.get("backend_framework", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "FastAPI" in backend.value or "Node.js" in backend.value:
            questions.append(VivaTarget(
                topic="Async Performance",
                question_target="Async I/O Efficiency",
                difficulty="hard",
                importance_score=0.8,
                focus="How many concurrent requests can your system handle? Where's the bottleneck - DB, compute, or I/O?"
            ))

        questions.append(VivaTarget(
            topic="Database Performance",
            question_target="Query Optimization",
            difficulty="medium",
            importance_score=0.75,
            focus="Show me your most expensive queries. How are they optimized? What indexes are in place?"
        ))

        return questions

    @staticmethod
    def _generate_security_questions(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel]
    ) -> List[VivaTarget]:
        """Security-focused questions."""
        questions = []

        auth = detections.get("authentication_system", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "JWT" in auth.value:
            questions.append(VivaTarget(
                topic="Authentication Security",
                question_target="JWT Security",
                difficulty="hard",
                importance_score=0.9,
                focus="How do you handle JWT token expiration and refresh? What's your strategy for token revocation?"
            ))

        auth_quality = quality_analysis.get("authentication_consistency", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "RBAC" not in auth_quality.value:
            questions.append(VivaTarget(
                topic="Authorization",
                question_target="Access Control",
                difficulty="medium",
                importance_score=0.85,
                focus="How do you ensure users can only access their own data? Show me an example of your permission checks."
            ))

        error_handling = quality_analysis.get("error_handling_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Error logging" in error_handling.value:
            questions.append(VivaTarget(
                topic="Security Monitoring",
                question_target="Error Logging & Secrets",
                difficulty="hard",
                importance_score=0.8,
                focus="What gets logged when errors occur? How do you prevent accidentally logging sensitive data?"
            ))

        questions.append(VivaTarget(
            topic="API Security",
            question_target="Rate Limiting & CORS",
            difficulty="medium",
            importance_score=0.75,
            focus="How do you prevent abuse of your APIs? What's your rate limiting strategy?"
        ))

        return questions

    @staticmethod
    def _generate_operational_questions(
        context_enrichment: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel]
    ) -> List[VivaTarget]:
        """Operational and maintainability questions."""
        questions = []

        observability = quality_analysis.get("observability_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Logging" not in observability.value:
            questions.append(VivaTarget(
                topic="Observability",
                question_target="Logging & Debugging",
                difficulty="medium",
                importance_score=0.8,
                focus="How do you debug production issues? What logging infrastructure is in place?"
            ))

        if "Metrics" not in observability.value:
            questions.append(VivaTarget(
                topic="Monitoring",
                question_target="Operational Metrics",
                difficulty="medium",
                importance_score=0.75,
                focus="What metrics do you monitor in production? How do you detect degradation?"
            ))

        ci_cd = context_enrichment.get("ci_cd_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Automated deployment" in ci_cd.value:
            questions.append(VivaTarget(
                topic="Deployment & CI/CD",
                question_target="Deployment Strategy",
                difficulty="medium",
                importance_score=0.75,
                focus="Walk me through your deployment pipeline. How do you handle database migrations in production?"
            ))

        doc_quality = context_enrichment.get("documentation_quality", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Minimally documented" in doc_quality.value or "Unknown" in doc_quality.value:
            questions.append(VivaTarget(
                topic="Maintainability",
                question_target="Documentation",
                difficulty="low",
                importance_score=0.6,
                focus="How would you onboard a new team member? What documentation exists?"
            ))

        return questions

    @staticmethod
    def _generate_technology_questions(
        detections: Dict[str, Any],
        tradeoff_analysis: List[EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> List[VivaTarget]:
        """Technology choice and tradeoff questions."""
        questions = []

        db = detections.get("database_used", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "MongoDB" in db.value:
            questions.append(VivaTarget(
                topic="Database Design",
                question_target="NoSQL Tradeoffs",
                difficulty="hard",
                importance_score=0.85,
                focus="Why did you choose MongoDB? How do you handle transactions across documents?"
            ))

        elif "PostgreSQL" in db.value:
            questions.append(VivaTarget(
                topic="Database Design",
                question_target="RDBMS Optimization",
                difficulty="hard",
                importance_score=0.8,
                focus="How do you leverage PostgreSQL's advanced features (JSONB, full-text search, etc.)?"
            ))

        # Tradeoff-specific questions
        if tradeoff_analysis:
            for tradeoff in tradeoff_analysis[:2]:  # Top 2 tradeoffs
                if "Consistency" in tradeoff.value or "Cache" in tradeoff.value:
                    questions.append(VivaTarget(
                        topic="Architecture Tradeoffs",
                        question_target=tradeoff.value.split(":")[0],
                        difficulty="hard",
                        importance_score=0.8,
                        focus=f"You're making a tradeoff between {tradeoff.value.lower()}. Explain your decision."
                    ))

        questions.append(VivaTarget(
            topic="Framework Choice",
            question_target="Backend Framework Evaluation",
            difficulty="medium",
            importance_score=0.7,
            focus="If you were starting this project today, would you choose the same tech stack? Why or why not?"
        ))

        return questions
