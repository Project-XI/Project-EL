"""
Context Enrichment Engine: Extracts deployment, architectural, and operational metadata
from repository documentation and configuration files to inform sophisticated reasoning.
"""

import os
import json
from typing import Dict, Any, List, Optional
from ...models.context import EvidenceModel


class ContextEnrichmentEngine:
    """
    Enriches the analysis context with metadata extracted from:
    - README files
    - Architecture documentation
    - Docker/Kubernetes configurations
    - CI/CD pipelines
    - Environment configurations
    - Monitoring/logging setups
    - Infrastructure patterns
    """

    @staticmethod
    def enrich_context(repo_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and synthesize metadata from the repository.
        
        Returns a context dict with:
        - project_purpose
        - operational_environment
        - deployment_assumptions
        - scalability_expectations
        - infrastructure_maturity
        - observability_setup
        - ci_cd_maturity
        - documentation_quality
        """
        enriched = {
            "project_purpose": ContextEnrichmentEngine._extract_project_purpose(repo_path),
            "operational_environment": ContextEnrichmentEngine._extract_operational_environment(repo_path),
            "deployment_assumptions": ContextEnrichmentEngine._extract_deployment_assumptions(repo_path),
            "scalability_expectations": ContextEnrichmentEngine._extract_scalability_expectations(repo_path),
            "infrastructure_maturity": ContextEnrichmentEngine._extract_infrastructure_maturity(repo_path),
            "observability_setup": ContextEnrichmentEngine._extract_observability_setup(repo_path),
            "ci_cd_maturity": ContextEnrichmentEngine._extract_ci_cd_maturity(repo_path),
            "documentation_quality": ContextEnrichmentEngine._extract_documentation_quality(repo_path),
        }
        return enriched

    @staticmethod
    def _extract_project_purpose(repo_path: str) -> EvidenceModel:
        """Extract project purpose from README and architecture docs."""
        purpose = "Unknown"
        confidence = 0.0
        evidence = []

        readme_path = os.path.join(repo_path, "README.md")
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:2000]  # First 2000 chars
                    
                # Simple heuristics
                if any(word in content.lower() for word in ["api", "server", "backend", "microservice"]):
                    purpose = "Backend API/Service"
                    confidence = 0.85
                    evidence = ["README indicates API/backend service focus"]
                elif any(word in content.lower() for word in ["dashboard", "ui", "frontend", "web app"]):
                    purpose = "Frontend/Dashboard"
                    confidence = 0.85
                    evidence = ["README indicates frontend/UI focus"]
                elif any(word in content.lower() for word in ["library", "package", "sdk"]):
                    purpose = "Library/Package"
                    confidence = 0.8
                    evidence = ["README indicates library/package"]
                else:
                    purpose = "General Purpose Project"
                    confidence = 0.5
                    evidence = ["Inferred from README content"]
            except Exception as e:
                evidence = [f"README parsing failed: {str(e)}"]

        return EvidenceModel(value=purpose, confidence=confidence, evidence=evidence)

    @staticmethod
    def _extract_operational_environment(repo_path: str) -> EvidenceModel:
        """Extract operational environment from Docker, K8s, and deployment configs."""
        environment = "Unknown"
        confidence = 0.0
        evidence = []

        # Check for Docker
        docker_compose = os.path.join(repo_path, "docker-compose.yml")
        dockerfile = os.path.join(repo_path, "Dockerfile")
        
        # Check for Kubernetes
        k8s_dir = os.path.join(repo_path, "k8s")
        helm_dir = os.path.join(repo_path, "helm")
        
        # Check for Cloud configs
        serverless_yml = os.path.join(repo_path, "serverless.yml")
        terraform_dir = os.path.join(repo_path, "terraform")

        deployment_indicators = []
        
        if os.path.exists(docker_compose):
            deployment_indicators.append("Docker Compose")
        if os.path.exists(dockerfile):
            deployment_indicators.append("Containerized")
        if os.path.exists(k8s_dir) or os.path.exists(helm_dir):
            deployment_indicators.append("Kubernetes/Orchestrated")
        if os.path.exists(serverless_yml):
            deployment_indicators.append("Serverless")
        if os.path.exists(terraform_dir):
            deployment_indicators.append("IaC (Terraform)")

        if deployment_indicators:
            environment = " + ".join(deployment_indicators)
            confidence = 0.9
            evidence = [f"Detected: {', '.join(deployment_indicators)}"]
        else:
            environment = "Traditional/Unknown"
            confidence = 0.3
            evidence = ["No containerization or orchestration detected"]

        return EvidenceModel(value=environment, confidence=confidence, evidence=evidence)

    @staticmethod
    def _extract_deployment_assumptions(repo_path: str) -> List[EvidenceModel]:
        """Extract assumptions about deployment, scaling, and runtime."""
        assumptions = []

        # Check environment files
        env_example = os.path.join(repo_path, ".env.example")
        if os.path.exists(env_example):
            try:
                with open(env_example, 'r') as f:
                    env_content = f.read()
                    
                if "DATABASE_URL" in env_content or "DB_" in env_content:
                    assumptions.append(EvidenceModel(
                        value="Assumes external database connectivity",
                        confidence=0.9,
                        evidence=["Database URL in environment config"]
                    ))
                if "REDIS" in env_content or "CACHE" in env_content:
                    assumptions.append(EvidenceModel(
                        value="Assumes Redis/caching layer availability",
                        confidence=0.85,
                        evidence=["Redis/cache config in environment"]
                    ))
                if "API_KEY" in env_content or "JWT" in env_content:
                    assumptions.append(EvidenceModel(
                        value="Assumes authentication/token infrastructure",
                        confidence=0.8,
                        evidence=["Auth credentials in environment config"]
                    ))
            except Exception:
                pass

        # Check for scaling indicators
        docker_compose_path = os.path.join(repo_path, "docker-compose.yml")
        if os.path.exists(docker_compose_path):
            try:
                with open(docker_compose_path, 'r') as f:
                    compose_content = f.read()
                    if "replicas" in compose_content or "scale" in compose_content.lower():
                        assumptions.append(EvidenceModel(
                            value="Architecture supports horizontal scaling",
                            confidence=0.8,
                            evidence=["Replication/scaling config detected"]
                        ))
            except Exception:
                pass

        return assumptions if assumptions else [
            EvidenceModel(
                value="Deployment context unclear",
                confidence=0.3,
                evidence=["Insufficient deployment configuration found"]
            )
        ]

    @staticmethod
    def _extract_scalability_expectations(repo_path: str) -> EvidenceModel:
        """Infer scalability expectations from architecture and config."""
        scalability = "Unknown"
        confidence = 0.0
        evidence = []

        # Check for load balancing
        has_lb = any(os.path.exists(os.path.join(repo_path, f)) 
                     for f in ["nginx.conf", "haproxy.cfg", "load-balancer.yml"])
        
        # Check for async/queue infrastructure
        has_async = any(os.path.exists(os.path.join(repo_path, f))
                       for f in ["celery.py", "queue.py", "bull.config.js"])
        
        # Check for caching
        has_caching = any(os.path.exists(os.path.join(repo_path, f))
                         for f in ["redis.conf", "cache.config.ts", "cache_config.py"])

        if has_lb and has_async:
            scalability = "High-scale expectations"
            confidence = 0.9
            evidence = ["Load balancing + async processing detected"]
        elif has_caching and has_async:
            scalability = "Medium-to-high scale"
            confidence = 0.8
            evidence = ["Caching and async patterns detected"]
        elif has_caching:
            scalability = "Medium scale"
            confidence = 0.7
            evidence = ["Caching layer indicates scale concerns"]
        else:
            scalability = "Single-instance/low-scale"
            confidence = 0.6
            evidence = ["No explicit scaling infrastructure detected"]

        return EvidenceModel(value=scalability, confidence=confidence, evidence=evidence)

    @staticmethod
    def _extract_infrastructure_maturity(repo_path: str) -> EvidenceModel:
        """Evaluate infrastructure maturity level."""
        maturity = "Basic"
        confidence = 0.5
        evidence = []

        has_docker = os.path.exists(os.path.join(repo_path, "Dockerfile"))
        has_k8s = os.path.exists(os.path.join(repo_path, "k8s"))
        has_helm = os.path.exists(os.path.join(repo_path, "helm"))
        has_terraform = os.path.exists(os.path.join(repo_path, "terraform"))
        has_ci_cd = any(os.path.exists(os.path.join(repo_path, d)) 
                        for d in [".github/workflows", ".gitlab-ci.yml", ".circleci"])

        maturity_score = sum([has_docker, has_k8s, has_helm, has_terraform, has_ci_cd])
        
        if maturity_score >= 4:
            maturity = "Enterprise-grade"
            confidence = 0.85
        elif maturity_score >= 3:
            maturity = "Intermediate"
            confidence = 0.8
        elif maturity_score >= 1:
            maturity = "Containerized"
            confidence = 0.7
        
        evidence = [f"Detected {maturity_score}/5 infrastructure components"]
        
        return EvidenceModel(value=maturity, confidence=confidence, evidence=evidence)

    @staticmethod
    def _extract_observability_setup(repo_path: str) -> EvidenceModel:
        """Extract observability and monitoring setup."""
        observability = []
        confidence = 0.0

        # Check for logging
        has_structured_logging = any(os.path.exists(os.path.join(repo_path, f)) 
                                     for f in ["logging.py", "logger.ts", "winston.config.js"])
        
        # Check for metrics
        has_metrics = any(os.path.exists(os.path.join(repo_path, f))
                         for f in ["prometheus.yml", "metrics.py", "statsd.js"])
        
        # Check for tracing
        has_tracing = any(os.path.exists(os.path.join(repo_path, f))
                         for f in ["jaeger.yml", "otel.config.ts", "opentelemetry.py"])
        
        # Check for health checks
        has_health = any("health" in str(os.listdir(repo_path)) for _ in [None])

        if has_structured_logging:
            observability.append("Structured logging")
        if has_metrics:
            observability.append("Metrics/Monitoring")
        if has_tracing:
            observability.append("Distributed tracing")
        if has_health:
            observability.append("Health checks")

        if observability:
            value = " + ".join(observability)
            confidence = 0.75
            evidence = [f"Detected observability components: {', '.join(observability)}"]
        else:
            value = "Minimal/No observability setup"
            confidence = 0.3
            evidence = ["No logging, metrics, or tracing infrastructure detected"]

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _extract_ci_cd_maturity(repo_path: str) -> EvidenceModel:
        """Extract CI/CD pipeline maturity."""
        ci_cd_features = []
        confidence = 0.0

        # Check for CI/CD platforms
        has_github_actions = os.path.exists(os.path.join(repo_path, ".github/workflows"))
        has_gitlab_ci = os.path.exists(os.path.join(repo_path, ".gitlab-ci.yml"))
        has_circleci = os.path.exists(os.path.join(repo_path, ".circleci"))
        has_travis = os.path.exists(os.path.join(repo_path, ".travis.yml"))

        if has_github_actions or has_gitlab_ci or has_circleci or has_travis:
            ci_cd_features.append("Automated CI/CD")
            confidence = 0.85

        # Check for test automation
        if has_github_actions:
            try:
                workflows_dir = os.path.join(repo_path, ".github/workflows")
                workflows = os.listdir(workflows_dir)
                if any("test" in w.lower() for w in workflows):
                    ci_cd_features.append("Automated testing")
                if any("deploy" in w.lower() for w in workflows):
                    ci_cd_features.append("Automated deployment")
            except Exception:
                pass

        if ci_cd_features:
            value = " + ".join(ci_cd_features)
            evidence = [f"CI/CD features: {', '.join(ci_cd_features)}"]
        else:
            value = "Manual processes"
            confidence = 0.4
            evidence = ["No automated CI/CD detected"]

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _extract_documentation_quality(repo_path: str) -> EvidenceModel:
        """Evaluate documentation quality and completeness."""
        doc_files = []
        confidence = 0.0

        for filename in os.listdir(repo_path):
            if filename.lower() in ["readme.md", "architecture.md", "api.md", "contributing.md", "setup.md"]:
                doc_files.append(filename)

        if len(doc_files) >= 3:
            value = "Well-documented"
            confidence = 0.8
            evidence = [f"Found {len(doc_files)} documentation files"]
        elif len(doc_files) >= 1:
            value = "Partially documented"
            confidence = 0.6
            evidence = [f"Found {len(doc_files)} documentation files"]
        else:
            value = "Minimally documented"
            confidence = 0.4
            evidence = ["Few/no documentation files found"]

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)
