"""
test_oracle_adapter.py
──────────────────────
Comprehensive test suite for the ORACLE Integration Adapter.

Test categories (per Issue #7 acceptance criteria)
───────────────────────────────────────────────────
1. Valid payload normalization
2. Malformed payload rejection
3. Schema compatibility (legacy/future shapes)
4. Evidence mapping regression
5. Deterministic output
6. Adapter isolation (MAIN never sees ORACLE internals)

Run:
    export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
    backend/venv/bin/python3 -m pytest backend/tests/test_oracle_adapter.py -v
"""

from __future__ import annotations

import copy
import pytest

# ── Helpers — minimal valid ORACLE payload factory ────────────────────────────

def _evidence(value: str, confidence: float = 0.9, evidence: list | None = None) -> dict:
    return {"value": value, "confidence": confidence, "evidence": evidence or []}


def _viva(topic: str, question_target: str, category: str = "Architecture") -> dict:
    return {
        "topic": topic,
        "question_target": question_target,
        "difficulty": "medium",
        "importance_score": 0.8,
        "depth_score": 7.0,
        "focus": f"Explain {question_target}",
        "category": category,
        "related_node": "api_gateway",
        "confidence": 0.85,
        "reasoning_summary": "Test target",
        "evidence": ["line 42 of routes.py"],
    }


def _min_valid_payload(**overrides) -> dict:
    """Return a minimal valid ORACLE payload dict."""
    base = {
        "project_name":        _evidence("Test Project"),
        "project_type":        _evidence("Web Application"),
        "backend_framework":   _evidence("FastAPI"),
        "frontend_framework":  _evidence("React"),
        "database_used":       _evidence("PostgreSQL"),
        "authentication_system": _evidence("JWT"),
        "architecture_pattern": _evidence("REST API"),
        "viva_intelligence_targets": [_viva("Architecture", "REST Constraints")],
        "implementation_viva_targets": [],
        "failure_paths": [],
        "runtime_risks": [],
        "inconsistencies": [],
        "middleware_chain": [],
        "security_flows": [],
        "execution_graph": {
            "nodes": [{"id": "n1", "label": "Route", "type": "ROUTE", "metadata": {}}],
            "edges": [{"source": "n1", "target": "n1", "relationship": "calls", "confidence": 0.9, "evidence": []}],
            "middleware": ["cors"],
            "db_calls": ["query_user"],
            "auth_points": ["verify_token"],
            "risk_flags": [],
            "failure_paths": [],
        },
        "complexity_mismatch": _evidence("No major mismatch detected", 1.0, []),
    }
    base.update(overrides)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# 1. VALID PAYLOAD NORMALIZATION
# ══════════════════════════════════════════════════════════════════════════════

class TestValidPayloadNormalization:

    def test_project_identity_fields_mapped(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(_min_valid_payload())
        assert out.project_name == "Test Project"
        assert out.project_type == "Web Application"
        assert out.architecture_pattern == "REST API"

    def test_observable_signals_populated(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(_min_valid_payload())
        keys = {s.key for s in out.observable_signals}
        assert "backend_framework" in keys
        assert "frontend_framework" in keys

    def test_observable_signal_values_correct(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(_min_valid_payload())
        be = next(s for s in out.observable_signals if s.key == "backend_framework")
        assert be.value == "FastAPI"
        assert 0.0 <= be.confidence <= 1.0

    def test_viva_targets_normalized(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(_min_valid_payload())
        assert len(out.viva_targets) == 1
        t = out.viva_targets[0]
        assert t.topic == "Architecture"
        assert t.question_target == "REST Constraints"

    def test_execution_graph_summary_counts(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(_min_valid_payload())
        assert out.execution_node_count == 1
        assert out.execution_edge_count == 1
        assert out.middleware_count == 1
        assert out.auth_point_count == 1

    def test_no_adapter_warnings_on_valid_payload(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(_min_valid_payload())
        assert out.adapter_warnings == []

    def test_complexity_mismatch_not_detected_for_no_mismatch(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(_min_valid_payload())
        assert out.complexity_mismatch_detected is False

    def test_complexity_mismatch_detected_when_present(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            complexity_mismatch=_evidence("High Complexity Claim vs Minimal Implementation", 0.7)
        )
        out = OracleAdapter.from_dict(payload)
        assert out.complexity_mismatch_detected is True
        assert "High Complexity" in out.complexity_mismatch_note

    def test_schema_version_is_set(self):
        from src.agents.main_agent.integration import OracleAdapter
        from src.agents.main_agent.integration.oracle_schema import ADAPTER_SCHEMA_VERSION
        out = OracleAdapter.from_dict(_min_valid_payload())
        assert out.schema_version == ADAPTER_SCHEMA_VERSION

    def test_both_viva_lists_merged_and_deduplicated(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            viva_intelligence_targets=[_viva("Architecture", "Unique Legacy")],
            implementation_viva_targets=[_viva("Security", "JWT Lifecycle"), _viva("Architecture", "Unique Legacy")],
        )
        out = OracleAdapter.from_dict(payload)
        targets_by_qt = [t.question_target for t in out.viva_targets]
        # Dedup: "Unique Legacy" should appear once
        assert targets_by_qt.count("Unique Legacy") == 1
        assert any(t.question_target == "JWT Lifecycle" for t in out.viva_targets)

    def test_failure_paths_from_evidence_models(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            failure_paths=[{"value": "DB timeout cascade", "confidence": 0.8, "evidence": ["line 99"]}]
        )
        out = OracleAdapter.from_dict(payload)
        assert len(out.failure_scenarios) == 1
        assert "DB timeout" in out.failure_scenarios[0].description

    def test_runtime_risks_become_failure_scenarios(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            runtime_risks=[{"value": "Memory leak in handler", "severity": "HIGH", "confidence": 0.75, "evidence": []}]
        )
        out = OracleAdapter.from_dict(payload)
        assert any("Memory leak" in s.description for s in out.failure_scenarios)

    def test_inconsistencies_normalized(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            inconsistencies=[{
                "issue": "Redis mentioned but absent",
                "severity": "medium",
                "confidence": 0.85,
                "evidence": ["doc line 5"],
            }]
        )
        out = OracleAdapter.from_dict(payload)
        assert len(out.inconsistencies) == 1
        assert "Redis" in out.inconsistencies[0].issue


# ══════════════════════════════════════════════════════════════════════════════
# 2. MALFORMED PAYLOAD REJECTION
# ══════════════════════════════════════════════════════════════════════════════

class TestMalformedPayloadRejection:

    def test_non_dict_returns_safe_fallback(self):
        from src.agents.main_agent.integration import OracleAdapter
        for bad in [None, [], "string", 42, object()]:
            out = OracleAdapter.from_dict(bad)
            assert isinstance(out.adapter_warnings, list)
            assert len(out.adapter_warnings) > 0

    def test_missing_required_key_returns_safe_fallback(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        del payload["backend_framework"]
        out = OracleAdapter.from_dict(payload)
        assert len(out.adapter_warnings) > 0

    def test_required_field_not_dict_returns_safe_fallback(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        payload["project_name"] = "raw string not a dict"
        out = OracleAdapter.from_dict(payload)
        assert len(out.adapter_warnings) > 0

    def test_evidence_model_missing_value_key_returns_safe_fallback(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        payload["project_name"] = {"confidence": 0.9, "evidence": []}  # no 'value'
        out = OracleAdapter.from_dict(payload)
        assert len(out.adapter_warnings) > 0

    def test_safe_fallback_has_sensible_defaults(self):
        from src.agents.main_agent.integration import OracleAdapter
        out = OracleAdapter.from_dict(None)
        assert out.project_name == "Unknown"
        assert out.viva_targets == []
        assert out.failure_scenarios == []
        assert out.observable_signals == []


# ══════════════════════════════════════════════════════════════════════════════
# 3. SCHEMA COMPATIBILITY (legacy/future shapes)
# ══════════════════════════════════════════════════════════════════════════════

class TestSchemaCompatibility:

    def test_legacy_viva_only_field_accepted(self):
        """Payload with only viva_intelligence_targets (no implementation_viva_targets)."""
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        del payload["implementation_viva_targets"]
        out = OracleAdapter.from_dict(payload)
        assert len(out.viva_targets) == 1

    def test_project_graph_shimmed_to_execution_graph(self):
        """Payload using old project_graph key should still produce graph summary."""
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        del payload["execution_graph"]
        payload["project_graph"] = {
            "nodes": [{"id": "n1", "label": "X", "type": "ROUTE", "metadata": {}}],
            "edges": [],
        }
        out = OracleAdapter.from_dict(payload)
        assert out.execution_node_count == 1

    def test_flat_string_failure_paths_coerced(self):
        """Old ORACLE builds that emitted failure_paths as List[str]."""
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(failure_paths=["DB went down", "Auth timed out"])
        out = OracleAdapter.from_dict(payload)
        assert len(out.failure_scenarios) == 2

    def test_missing_evidence_list_in_evidence_model_handled(self):
        """EvidenceModel dicts without 'evidence' key."""
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        payload["backend_framework"] = {"value": "FastAPI", "confidence": 0.95}  # no 'evidence'
        out = OracleAdapter.from_dict(payload)
        be = next((s for s in out.observable_signals if s.key == "backend_framework"), None)
        assert be is not None
        assert be.value == "FastAPI"

    def test_lowercase_runtime_risk_severity_coerced(self):
        """Old payloads using lowercase severity strings."""
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            runtime_risks=[{"value": "OOM risk", "severity": "critical", "confidence": 0.9, "evidence": []}]
        )
        out = OracleAdapter.from_dict(payload)
        assert any(s.description == "OOM risk" for s in out.failure_scenarios)


# ══════════════════════════════════════════════════════════════════════════════
# 4. EVIDENCE MAPPING REGRESSION
# ══════════════════════════════════════════════════════════════════════════════

class TestEvidenceMapping:

    def test_viva_target_evidence_preserved(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            viva_intelligence_targets=[{
                **_viva("Security", "JWT Lifecycle"),
                "evidence": ["jwt middleware detected at line 88", "token expiry = 3600s"],
            }],
            implementation_viva_targets=[],
        )
        out = OracleAdapter.from_dict(payload)
        t = next(t for t in out.viva_targets if t.question_target == "JWT Lifecycle")
        assert len(t.evidence) == 2
        assert t.evidence[0].text == "jwt middleware detected at line 88"

    def test_observable_signal_evidence_preserved(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        payload["backend_framework"]["evidence"] = ["import fastapi found in main.py:3"]
        out = OracleAdapter.from_dict(payload)
        be = next(s for s in out.observable_signals if s.key == "backend_framework")
        assert be.evidence[0].text == "import fastapi found in main.py:3"

    def test_failure_scenario_evidence_preserved(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            failure_paths=[{"value": "Cache miss storm", "confidence": 0.8, "evidence": ["redis timeout line 42"]}]
        )
        out = OracleAdapter.from_dict(payload)
        fs = next(s for s in out.failure_scenarios if "Cache miss" in s.description)
        assert fs.evidence[0].text == "redis timeout line 42"

    def test_inconsistency_evidence_preserved(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            inconsistencies=[{
                "issue": "Redis missing",
                "severity": "medium",
                "confidence": 0.9,
                "evidence": ["doc mentions Redis", "requirements.txt has no redis"],
            }]
        )
        out = OracleAdapter.from_dict(payload)
        inc = out.inconsistencies[0]
        assert len(inc.evidence) == 2


# ══════════════════════════════════════════════════════════════════════════════
# 5. DETERMINISTIC OUTPUT
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterministicOutput:

    def test_same_input_produces_same_output(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        out1 = OracleAdapter.from_dict(copy.deepcopy(payload))
        out2 = OracleAdapter.from_dict(copy.deepcopy(payload))
        assert out1.model_dump() == out2.model_dump()

    def test_adapter_does_not_mutate_input(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload()
        original = copy.deepcopy(payload)
        OracleAdapter.from_dict(payload)
        assert payload == original

    def test_empty_lists_yield_empty_outputs(self):
        from src.agents.main_agent.integration import OracleAdapter
        payload = _min_valid_payload(
            viva_intelligence_targets=[],
            implementation_viva_targets=[],
            failure_paths=[],
            runtime_risks=[],
            inconsistencies=[],
        )
        out = OracleAdapter.from_dict(payload)
        assert out.viva_targets == []
        assert out.failure_scenarios == []
        assert out.inconsistencies == []


# ══════════════════════════════════════════════════════════════════════════════
# 6. ADAPTER ISOLATION
# ══════════════════════════════════════════════════════════════════════════════

class TestAdapterIsolation:

    def test_output_type_is_normalized_not_structured_context(self):
        """MAIN must never receive a StructuredContext object."""
        from src.agents.main_agent.integration import OracleAdapter
        from src.agents.main_agent.integration.oracle_schema import NormalizedOracleOutput
        out = OracleAdapter.from_dict(_min_valid_payload())
        assert isinstance(out, NormalizedOracleOutput)

    def test_output_has_no_oracle_internal_types(self):
        """NormalizedOracleOutput fields must not contain ORACLE-internal objects."""
        from src.agents.main_agent.integration import OracleAdapter
        from src.models.context import StructuredContext, EvidenceModel, VivaTarget
        out = OracleAdapter.from_dict(_min_valid_payload())
        dumped = out.model_dump()
        # Recursively check no pydantic ORACLE model sneaked through
        def _has_oracle_type(obj):
            if isinstance(obj, (StructuredContext, EvidenceModel, VivaTarget)):
                return True
            if isinstance(obj, dict):
                return any(_has_oracle_type(v) for v in obj.values())
            if isinstance(obj, list):
                return any(_has_oracle_type(i) for i in obj)
            return False
        assert not _has_oracle_type(out)

    def test_from_context_accepts_structured_context(self):
        """OracleAdapter.from_context must accept a real StructuredContext."""
        from src.agents.main_agent.integration import OracleAdapter, NormalizedOracleOutput
        from src.models.context import StructuredContext, EvidenceModel, ExecutionGraph
        ctx = StructuredContext(
            project_name        = EvidenceModel(value="My Project", confidence=0.9, evidence=[]),
            project_type        = EvidenceModel(value="API", confidence=0.9, evidence=[]),
            frontend_framework  = EvidenceModel(value="React", confidence=0.85, evidence=[]),
            backend_framework   = EvidenceModel(value="FastAPI", confidence=0.95, evidence=[]),
            database_used       = EvidenceModel(value="PostgreSQL", confidence=0.9, evidence=[]),
            authentication_system = EvidenceModel(value="JWT", confidence=0.9, evidence=[]),
            architecture_pattern = EvidenceModel(value="REST API", confidence=0.9, evidence=[]),
            execution_graph     = ExecutionGraph(),
        )
        out = OracleAdapter.from_context(ctx)
        assert isinstance(out, NormalizedOracleOutput)
        assert out.project_name == "My Project"
