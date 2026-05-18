# ORACLE Calibration & Validation: Quick Reference

## What's Available

### 📚 Documentation
- **[README.md](calibration/README.md)** - Detailed framework documentation
- **[SYSTEM_OVERVIEW.md](calibration/SYSTEM_OVERVIEW.md)** - Architecture and usage
- **[INTEGRATION_GUIDE.md](calibration/INTEGRATION_GUIDE.md)** - Integration instructions

### 🧪 Test Framework
- **repository_fixtures.py** - 4 diverse test repositories
- **signal_validator.py** - Validate observable signals
- **failure_propagation_validator.py** - Validate failure scenarios
- **viva_quality_validator.py** - Validate interview questions
- **confidence_calibrator.py** - Calibrate confidence scores
- **observability.py** - Runtime tracing infrastructure

### 🚀 Executable Scripts

#### 1. Run Full Calibration
```bash
cd backend
python -m evaluation.calibration.calibration_runner
```
**Output:** Comprehensive JSON report + dashboard metrics

#### 2. Validate Against Fixtures
```bash
cd backend
python evaluation/validate_oracle_analysis.py
python evaluation/validate_oracle_analysis.py --fixtures clean,broken
```
**Output:** Validation results for each fixture

#### 3. Check Quality Thresholds
```bash
cd backend
python evaluation/check_calibration_thresholds.py
python evaluation/check_calibration_thresholds.py --strict  # For main branch
```
**Output:** Pass/fail for each metric + recommendations

### 📊 Visualizations
- **[calibration_dashboard.html](../testing_oracle_ui/calibration_dashboard.html)**
  - Open in browser: `file:///.../calibration_dashboard.html`
  - Shows confidence calibration curves
  - Repository-specific performance
  - Issues and recommendations

### ⚙️ CI/CD Integration
- **[.github/workflows/calibration.yml](../.github/workflows/calibration.yml)**
  - Runs on every PR and push to main/develop
  - Checks thresholds automatically
  - Publishes results as PR comments
  - Uploads artifacts for analysis

## Workflow

### For PR Review

```bash
# Before submitting PR:
cd backend
python -m evaluation.calibration.calibration_runner
python evaluation/check_calibration_thresholds.py

# Check that metrics pass:
# - Signal Precision: 0.80+
# - Signal Recall: 0.80+
# - Viva Validity: 0.85+
# - etc.
```

### For Main Branch

```bash
# CI/CD runs automatically on push
# Uses STRICT thresholds:
# - Signal Precision: 0.85+
# - Viva Validity: 0.90+
# - etc.

# If checks fail, local debugging:
cd backend
python evaluation/check_calibration_thresholds.py --strict
```

### For Dashboard Updates

```bash
# Run calibration
cd backend
python -m evaluation.calibration.calibration_runner

# Results automatically feed dashboard
# Open: backend/testing_oracle_ui/calibration_dashboard.html
```

## Key Metrics

### Signal Detection (Observable Signals)
| Metric | Standard | Strict | What It Means |
|--------|----------|--------|---------------|
| Precision | 0.80 | 0.85 | % of detected signals are correct |
| Recall | 0.80 | 0.82 | % of expected signals found |
| F1 Score | 0.80 | 0.83 | Harmonic mean of P/R |
| Confidence RMSE | 0.12 | 0.10 | Calibration accuracy |

### Failure Propagation
| Metric | Standard | Strict | What It Means |
|--------|----------|--------|---------------|
| Precision | 0.75 | 0.80 | % of scenarios match expected |
| Propagation Accuracy | 0.80 | 0.85 | % of paths correctly identified |

### Viva Questions
| Metric | Standard | Strict | What It Means |
|--------|----------|--------|---------------|
| Validity Rate | 0.85 | 0.90 | % of questions pass quality checks |
| Grounding Rate | 0.90 | 0.92 | % have code evidence |

## Troubleshooting

### Issue: "No calibration results found"
```bash
# Make sure you're running from backend directory
cd backend
python -m evaluation.calibration.calibration_runner
```

### Issue: Metrics below threshold
```bash
# Check detailed report
cd backend
python evaluation/check_calibration_thresholds.py

# Read recommendations from report
# Typical issues:
# - Signal patterns need refinement
# - Confidence scores miscalibrated
# - Viva generation too generic
```

### Issue: CI/CD workflow failing
```bash
# Run locally to debug
cd backend
python -m evaluation.calibration.calibration_runner
python evaluation/validate_oracle_analysis.py
python evaluation/check_calibration_thresholds.py
```

## Integration Timeline

### Week 1: Foundation (✅ DONE)
- [x] Validation framework built
- [x] Repository fixtures defined
- [x] All validators implemented
- [x] Observability infrastructure created
- [x] Dashboard built
- [x] Documentation complete

### Week 2: Integration (🔄 IN PROGRESS)
- [ ] Wire validators into OracleAgent
- [ ] Add trace emission to engines
- [ ] Create validation wrapper
- [ ] Set up CI/CD workflow
- [ ] Test end-to-end pipeline

### Week 3: Automation (📋 PLANNED)
- [ ] Automate calibration on every PR
- [ ] Publish dashboard to team
- [ ] Track metrics over time
- [ ] Set up alerts for degradation

### Week 4: Refinement (📋 PLANNED)
- [ ] Analyze calibration results
- [ ] Refine algorithms based on findings
- [ ] Update confidence scoring
- [ ] Publish benchmarks

## File Structure

```
backend/
├── evaluation/
│   ├── calibration/
│   │   ├── __init__.py
│   │   ├── README.md                              ← Start here
│   │   ├── SYSTEM_OVERVIEW.md                     ← Architecture
│   │   ├── INTEGRATION_GUIDE.md                   ← Integration steps
│   │   ├── repository_fixtures.py                 ← Test dataset
│   │   ├── signal_validator.py
│   │   ├── failure_propagation_validator.py
│   │   ├── viva_quality_validator.py
│   │   ├── confidence_calibrator.py
│   │   ├── observability.py
│   │   ├── calibration_runner.py
│   │   └── results/                               ← Generated reports
│   ├── validate_oracle_analysis.py                ← Validation wrapper
│   └── check_calibration_thresholds.py            ← Quality gating
│
├── testing_oracle_ui/
│   └── calibration_dashboard.html                 ← Visualization
│
└── .github/workflows/
    └── calibration.yml                            ← CI/CD automation
```

## Example Output

### Calibration Report
```
ORACLE EVIDENCE-GROUNDED INTELLIGENCE CALIBRATION REPORT
=========================================================

📊 AGGREGATE METRICS:

  signals:
    - average_precision: 0.847
    - average_recall: 0.823
    - average_f1_score: 0.835
    - average_confidence: 0.814

  failures:
    - average_precision: 0.805
    - average_recall: 0.778
    - average_propagation_accuracy: 0.892

  viva:
    - average_validity_rate: 0.856
    - average_grounding_rate: 0.912
    - average_specificity: 0.821

💡 RECOMMENDATIONS:
  ✅ Signal accuracy within acceptable ranges
  ✅ Propagation analysis sound
  ⚠️  Async pattern detection needs refinement
  ⚠️  Monorepo consistency thresholds need calibration
```

### Threshold Check Output
```
📋 Loading: calibration_report_2026-05-18T14-32-15.json

✅ PASS | Signal Precision....................... 0.847 (threshold: 0.80)
✅ PASS | Signal Recall......................... 0.823 (threshold: 0.80)
✅ PASS | Signal F1 Score....................... 0.835 (threshold: 0.80)
✅ PASS | Failure Precision..................... 0.805 (threshold: 0.75)
✅ PASS | Failure Propagation Accuracy.......... 0.892 (threshold: 0.80)
✅ PASS | Viva Validity Rate................... 0.856 (threshold: 0.85)
✅ PASS | Viva Grounding Rate.................. 0.912 (threshold: 0.90)

📊 RESULTS: 7/7 metrics passed

✅ All calibration metrics within acceptable ranges!

🎯 Status: READY FOR MERGE
```

## Next Steps

1. **Read the docs**
   - Start with [README.md](calibration/README.md)
   - Review [SYSTEM_OVERVIEW.md](calibration/SYSTEM_OVERVIEW.md)

2. **Run calibration locally**
   ```bash
   cd backend
   python -m evaluation.calibration.calibration_runner
   python evaluation/check_calibration_thresholds.py
   ```

3. **Follow integration guide**
   - See [INTEGRATION_GUIDE.md](calibration/INTEGRATION_GUIDE.md)
   - Modify OracleAgent to emit traces
   - Wire validators into pipeline

4. **Set up CI/CD**
   - GitHub Actions workflow ready in `.github/workflows/calibration.yml`
   - Automatically runs on every PR/push
   - Comments results on PRs

## Questions?

- **How do I interpret the metrics?** → See [SYSTEM_OVERVIEW.md](calibration/SYSTEM_OVERVIEW.md#interpreting-results)
- **How do I integrate with my code?** → See [INTEGRATION_GUIDE.md](calibration/INTEGRATION_GUIDE.md)
- **What if my metrics are low?** → See [Troubleshooting](#troubleshooting)
- **How does validation work?** → See [README.md](calibration/README.md#how-it-works-example)

---

**ORACLE Evidence-Grounded Intelligence** | Validated | Calibrated | Observable | Production-Ready
