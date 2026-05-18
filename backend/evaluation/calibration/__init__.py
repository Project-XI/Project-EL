"""
ORACLE Evidence-Grounded Intelligence Validation & Calibration Framework

This module provides comprehensive validation, stress-testing, and calibration
of the observable signals, failure propagation, and viva generation engines.

Key Components:
- repository_fixtures: Test dataset definitions with expected outputs
- signal_validator: Validates observable signal accuracy and grounding
- failure_propagation_validator: Tests failure scenario propagation chains
- viva_quality_validator: Evaluates viva question realism and specificity
- calibration_runner: Orchestrates full validation pipeline
- confidence_calibrator: Calibrates confidence score accuracy
- observability: Runtime tracing and reasoning transparency

Principles:
- All validation grounded in code evidence, never speculation
- No fake metrics or hardcoded evaluation values
- Adversarial stress-testing with messy/broken repositories
- Confidence scores calibrated against real accuracy
- Viva questions evaluated for implementation specificity
"""
