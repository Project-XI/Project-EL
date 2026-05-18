"""
ORACLE Calibration Integration Guide

This guide shows how to integrate validation and observability into the
OracleAgent analysis pipeline.

Integration involves:
1. Adding trace collection during analysis
2. Wiring validators into the pipeline
3. Exporting validation reports
4. Publishing calibration dashboards
"""

# ============================================================================
# STEP 1: INTEGRATION POINTS IN ORACLEAGENT
# ============================================================================

ORACLE_AGENT_MODIFICATIONS = """
# File: backend/src/agents/oracle/agent.py

from evaluation.calibration.observability import TraceCollector, get_trace_collector
from evaluation.calibration.signal_validator import ObservableSignalValidator
from evaluation.calibration.failure_propagation_validator import ExecutionGraphFailureValidator
from evaluation.calibration.viva_quality_validator import VivaQualityValidator


class OracleAgent(BaseAgent):
    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None):
        # Initialize trace collection for this session
        trace_collector = TraceCollector()
        
        # ... existing analysis code ...
        
        # PHASE 2A: Observable Signals with Tracing
        observable_signals = ObservableSignalsEngine.extract_signals(
            repo_path, repo_structure, repo_detections, project_graph
        )
        
        # Capture signal traces
        for signal in observable_signals:
            signal_trace = SignalGenerationTrace(
                signal_name=signal.signal_name,
                search_pattern=getattr(signal, 'search_pattern', ''),
                files_searched=getattr(signal, 'files_searched', []),
                matches_found=len(signal.evidence_files),
                confidence_calculated=signal.confidence,
                confidence_reasoning=f"{len(signal.evidence_files)} evidence files, "
                                     f"confidence {signal.confidence:.2f}",
                evidence_files_collected=signal.evidence_files,
            )
            trace_collector.add_signal_trace(signal_trace)
        
        # PHASE 2B: Failure Scenarios with Tracing
        failure_scenarios = ExecutionGraphFailureAnalyzer.analyze_failure_scenarios(
            repo_path, repo_structure, repo_detections, observable_signals, project_graph
        )
        
        # Capture propagation traces
        for scenario in failure_scenarios:
            propagation_trace = PropagationTrace(
                scenario_name=scenario.scenario_name,
                trigger_node=scenario.trigger,
                affected_path_count=len(scenario.affected_paths),
                propagation_depth=len(scenario.affected_paths),
                traversal_steps=[
                    {
                        "component": component,
                        "risk_level": scenario.propagation_risk
                    }
                    for component in scenario.affected_paths
                ],
                risk_justification_steps=[
                    f"Propagation risk {scenario.propagation_risk}: "
                    f"{len(scenario.affected_paths)} affected components",
                    f"Recovery possible: {scenario.recovery_possible}",
                ],
            )
            trace_collector.add_propagation_trace(propagation_trace)
        
        # Store traces in context for validation
        context.trace_collector = trace_collector
        
        return context
"""

# ============================================================================
# STEP 2: VALIDATION WORKFLOW
# ============================================================================

VALIDATION_WORKFLOW = """
# File: backend/evaluation/validate_oracle_analysis.py

import asyncio
from pathlib import Path
from src.agents.oracle.agent import OracleAgent
from evaluation.calibration.calibration_runner import CalibrationRunner
from evaluation.calibration.repository_fixtures import ALL_FIXTURES
from evaluation.calibration.signal_validator import ObservableSignalValidator
from evaluation.calibration.failure_propagation_validator import ExecutionGraphFailureValidator
from evaluation.calibration.viva_quality_validator import VivaQualityValidator


async def validate_oracle_against_fixtures():
    '''
    Run ORACLE against fixture repositories and validate outputs.
    '''
    oracle = OracleAgent()
    runner = CalibrationRunner()
    
    all_results = {}
    
    for fixture in ALL_FIXTURES:
        print(f"\\n[Validation] Testing: {fixture.name}")
        
        # In real scenario, would have fixture.repo_url
        # For now, demonstrate with real project
        if fixture.name == "Clean FastAPI REST API":
            repo_url = "https://github.com/Project-XI/Project-EL.git"
        else:
            print(f"[Validation] Fixture {fixture.name} - skipping (no test repo available)")
            continue
        
        # Run oracle analysis
        context = await oracle.process(
            session_id=f"validation_{fixture.name}",
            input_data={"repo_url": repo_url},
        )
        
        # Validate signals
        signal_report = ObservableSignalValidator.validate_signals(
            context.observable_signals,
            fixture.expected_signals,
            fixture.name
        )
        print(f"  Signals: Precision={signal_report.precision:.3f}, "
              f"Recall={signal_report.recall:.3f}")
        
        # Validate failures
        failure_report = ExecutionGraphFailureValidator.validate_failure_scenarios(
            context.failure_scenarios,
            fixture.expected_failure_scenarios,
            context.project_graph,
            fixture.name
        )
        print(f"  Failures: Precision={failure_report.precision:.3f}, "
              f"Propagation Accuracy={failure_report.propagation_accuracy:.3f}")
        
        # Validate viva questions
        viva_report = VivaQualityValidator.validate_viva_questions(
            context.viva_intelligence_targets,
            fixture.name,
            context.observable_signals,
            context.failure_scenarios,
        )
        print(f"  Viva: Validity={viva_report.validity_rate:.3f}, "
              f"Grounding={viva_report.grounding_rate:.3f}")
        
        # Collect results
        all_results[fixture.name] = {
            "signal_validation": signal_report,
            "failure_validation": failure_report,
            "viva_validation": viva_report,
            "traces": context.trace_collector.export_traces("json"),
        }
    
    # Generate aggregate report
    print("\\n" + "="*80)
    print("ORACLE VALIDATION COMPLETE")
    print("="*80)
    
    # Save validation results
    validation_dir = Path("backend/evaluation/calibration/validation_results")
    validation_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    
    report_path = validation_dir / f"validation_{timestamp}.json"
    with open(report_path, 'w') as f:
        # Convert to JSON-serializable format
        json_results = {}
        for fixture_name, results in all_results.items():
            json_results[fixture_name] = {
                "signals": results["signal_validation"].to_dict(),
                "failures": results["failure_validation"].to_dict(),
                "viva": results["viva_validation"].to_dict(),
            }
        json.dump(json_results, f, indent=2)
    
    print(f"Results saved to {report_path}")
    return all_results


if __name__ == "__main__":
    asyncio.run(validate_oracle_against_fixtures())
"""

# ============================================================================
# STEP 3: CI/CD INTEGRATION
# ============================================================================

GITHUB_ACTIONS_WORKFLOW = """
# File: .github/workflows/calibration.yml

name: ORACLE Calibration Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/src/services/intelligence/**'
      - 'backend/src/agents/oracle/**'
      - 'backend/evaluation/calibration/**'
  pull_request:
    branches: [main]

jobs:
  calibration:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run ORACLE calibration validation
        run: |
          cd backend
          python -m evaluation.validate_oracle_analysis
      
      - name: Generate calibration report
        run: |
          cd backend
          python -m evaluation.calibration.calibration_runner
      
      - name: Upload calibration results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: oracle-calibration-results
          path: backend/evaluation/calibration/results/
      
      - name: Check validation thresholds
        run: |
          # Fail if metrics below thresholds
          python backend/evaluation/check_calibration_thresholds.py \\
            --signal-precision 0.80 \\
            --signal-recall 0.80 \\
            --failure-accuracy 0.80 \\
            --viva-validity 0.85
      
      - name: Comment on PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync(
              'backend/evaluation/calibration/results/calibration_report_*.json'
            ));
            const comment = '## ORACLE Calibration Results\\n' +
              '- Signal Precision: ' + results.aggregate_metrics.signals.average_precision +
              '\\n- Viva Validity: ' + results.aggregate_metrics.viva.average_validity_rate;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
"""

# ============================================================================
# STEP 4: THRESHOLD CHECKING
# ============================================================================

THRESHOLD_CHECKER = """
# File: backend/evaluation/check_calibration_thresholds.py

import json
import sys
from pathlib import Path


def check_thresholds(
    signal_precision: float = 0.80,
    signal_recall: float = 0.80,
    failure_accuracy: float = 0.80,
    viva_validity: float = 0.85,
):
    '''Verify calibration metrics meet thresholds.'''
    
    # Find latest calibration report
    results_dir = Path("backend/evaluation/calibration/results")
    if not results_dir.exists():
        print("❌ No calibration results found")
        return False
    
    # Load latest report
    reports = sorted(results_dir.glob("calibration_report_*.json"))
    if not reports:
        print("❌ No calibration reports found")
        return False
    
    with open(reports[-1]) as f:
        report = json.load(f)
    
    metrics = report["aggregate_metrics"]
    passed = True
    
    # Check each threshold
    checks = [
        ("Signal Precision", 
         metrics["signals"]["average_precision"], signal_precision),
        ("Signal Recall",
         metrics["signals"]["average_recall"], signal_recall),
        ("Failure Propagation Accuracy",
         metrics["failures"]["average_propagation_accuracy"], failure_accuracy),
        ("Viva Validity Rate",
         metrics["viva"]["average_validity_rate"], viva_validity),
    ]
    
    print("\\n📊 CALIBRATION THRESHOLD CHECK")
    print("="*60)
    
    for name, actual, threshold in checks:
        status = "✅ PASS" if actual >= threshold else "❌ FAIL"
        print(f"{status} | {name}: {actual:.3f} (threshold: {threshold:.3f})")
        if actual < threshold:
            passed = False
    
    print("="*60)
    
    if passed:
        print("\\n✅ All calibration metrics within acceptable ranges!")
    else:
        print("\\n❌ Some metrics below thresholds. Review recommendations:")
        for rec in report["calibration_recommendations"]:
            print(f"  {rec}")
    
    return passed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal-precision", type=float, default=0.80)
    parser.add_argument("--signal-recall", type=float, default=0.80)
    parser.add_argument("--failure-accuracy", type=float, default=0.80)
    parser.add_argument("--viva-validity", type=float, default=0.85)
    
    args = parser.parse_args()
    
    success = check_thresholds(
        signal_precision=args.signal_precision,
        signal_recall=args.signal_recall,
        failure_accuracy=args.failure_accuracy,
        viva_validity=args.viva_validity,
    )
    
    sys.exit(0 if success else 1)
"""

# ============================================================================
# STEP 5: QUICK START
# ============================================================================

QUICK_START = """
## Quick Start: Running Oracle Calibration

### 1. Run Full Calibration Pipeline

```bash
cd /Users/rajkoli/Project-EL
python -m backend.evaluation.calibration.calibration_runner
```

This will:
- Test all 4 fixture repositories
- Validate signals, failures, and viva questions
- Calibrate confidence scores
- Generate comprehensive report
- Save results to `backend/evaluation/calibration/results/`

### 2. Validate Against Real Repositories

```bash
cd /Users/rajkoli/Project-EL/backend
python -m evaluation.validate_oracle_analysis
```

This will:
- Run OracleAgent against fixture repos
- Validate outputs against expected patterns
- Collect traces for each analysis
- Save validation results

### 3. Check Calibration Metrics

```bash
cd /Users/rajkoli/Project-EL
python backend/evaluation/check_calibration_thresholds.py
```

This will:
- Load latest calibration report
- Check against quality thresholds
- Show pass/fail for each metric
- Print recommendations if needed

### 4. View Calibration Dashboard

Open in browser:
```
file:///Users/rajkoli/Project-EL/backend/testing_oracle_ui/calibration_dashboard.html
```

## Integration Timeline

1. **Week 1**: Add trace collection to OracleAgent
2. **Week 2**: Wire validators into analysis pipeline
3. **Week 3**: Set up CI/CD calibration runs
4. **Week 4**: Publish calibration benchmarks
5. **Ongoing**: Monitor calibration trends, refine algorithms

## Key Files to Modify

- `backend/src/agents/oracle/agent.py` - Add trace collection
- `backend/src/services/intelligence/observable_signals_engine.py` - Add observability
- `backend/src/services/intelligence/execution_graph_failure_analyzer.py` - Add observability
- `backend/src/services/intelligence/evidence_grounded_viva_generator.py` - Add observability

## Expected Baseline Metrics

After full integration:
- Signal Detection Precision: ~0.85
- Signal Detection Recall: ~0.82
- Failure Propagation Accuracy: ~0.88
- Viva Validity Rate: ~0.86
- Viva Grounding Rate: ~0.91
- Confidence Calibration RMSE: <0.10

## Continuous Improvement Workflow

1. Run calibration on every PR
2. Track metrics over time (dashboard)
3. Identify degradation patterns
4. Refine algorithms based on findings
5. Re-calibrate confidence scores
6. Publish updated benchmarks
"""

# ============================================================================
# EXECUTION INSTRUCTIONS
# ============================================================================

print(__doc__)
print(ORACLE_AGENT_MODIFICATIONS)
print(VALIDATION_WORKFLOW)
print(GITHUB_ACTIONS_WORKFLOW)
print(THRESHOLD_CHECKER)
print(QUICK_START)
