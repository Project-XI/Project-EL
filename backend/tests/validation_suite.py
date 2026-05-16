import asyncio
import os
import sys
import json
import time
import traceback
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.agents.oracle import OracleAgent
from src.services.debug_visualizer.mermaid_generator import MermaidGenerator
from src.services.debug_visualizer.html_report_builder import HTMLReportBuilder
from evaluation.evaluation_runner import OracleEvaluator

async def validate_phase_1():
    print("\n--- PHASE 1: CLI & Core Validation ---")
    oracle = OracleAgent()
    repo_url = "https://github.com/Project-XI/Project-EL"
    
    try:
        start_time = time.time()
        print(f"[*] Testing 'analyze' for {repo_url}...")
        context = await oracle.process("val_session", {"repo_url": repo_url})
        
        print(f"[✓] Analysis complete in {time.time() - start_time:.2f}s")
        print(f"[✓] Nodes: {len(context.execution_graph.nodes)}")
        
        print("[*] Testing 'debug' visualization...")
        mermaid = MermaidGenerator.generate(context.execution_graph)
        if not mermaid.startswith("graph TD"):
            raise ValueError("Invalid Mermaid output")
        print("[✓] Mermaid generated successfully.")
        
        print("[*] Testing 'report' generation...")
        report_path = "backend/tests/validation_report.html"
        HTMLReportBuilder.build(context, report_path)
        if not os.path.exists(report_path):
            raise FileNotFoundError("HTML report not found")
        print(f"[✓] HTML report generated at {report_path}")
        
    except Exception as e:
        print(f"[✘] Phase 1 Failed: {str(e)}")
        traceback.print_exc()

async def validate_phase_4():
    print("\n--- PHASE 4: Benchmark Accuracy Test ---")
    evaluator = OracleEvaluator()
    repo_url = "https://github.com/Project-XI/Project-EL"
    expected_path = "backend/evaluation/expected_outputs/project_el.json"
    
    try:
        report = await evaluator.run_benchmark(repo_url, expected_path)
        print(f"[✓] Benchmark complete.")
        print(f"    - Stack Accuracy: {report['metrics']['stack_accuracy']*100:.1f}%")
        print(f"    - Auth Accuracy: {report['metrics']['auth_detection_accuracy']*100:.1f}%")
        
        if report["metrics"]["stack_accuracy"] < 0.8:
            print("[!] Warning: Stack accuracy below threshold.")
            
    except Exception as e:
        print(f"[✘] Phase 4 Failed: {str(e)}")

async def run_full_validation():
    await validate_phase_1()
    await validate_phase_4()
    print("\n--- Validation Suite Complete ---")

if __name__ == "__main__":
    asyncio.run(run_full_validation())
