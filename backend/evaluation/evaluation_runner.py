import os
import json
import asyncio
import sys
from typing import Dict, Any, List
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.agents.oracle import OracleAgent
from src.models.context import StructuredContext

class OracleEvaluator:
    """
    Benchmarks ORACLE analysis against ground-truth expected outputs.
    """
    def __init__(self):
        self.oracle = OracleAgent()
        self.results_dir = "backend/evaluation/results"
        os.makedirs(self.results_dir, exist_ok=True)

    async def run_benchmark(self, repo_url: str, expected_path: str) -> Dict[str, Any]:
        print(f"[EVAL] Benchmarking: {repo_url}...")
        
        # 1. Load Expected
        with open(expected_path, 'r') as f:
            expected = json.load(f)

        # 2. Run ORACLE
        session_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        actual_context = await self.oracle.process(session_id, {"repo_url": repo_url})
        actual = actual_context.model_dump()

        # 3. Calculate Metrics
        metrics = self._calculate_metrics(expected, actual)
        
        # 4. Save Report
        report = {
            "timestamp": datetime.now().isoformat(),
            "repo_url": repo_url,
            "metrics": metrics,
            "mismatches": self._find_mismatches(expected, actual)
        }
        
        report_path = os.path.join(self.results_dir, f"report_{expected['repo_name']}.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report

    def _calculate_metrics(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, float]:
        scores = {}
        
        # Tech Stack Precision/Recall (Simplified)
        exp_stack = set(expected.get("expected_stack", []))
        # Extract detected tech from actual
        act_stack = set()
        for key in ["frontend_framework", "backend_framework", "database_used"]:
            val = actual.get(key, {}).get("value")
            if val and val != "Unknown":
                act_stack.add(val)
        
        if not exp_stack:
            scores["stack_accuracy"] = 1.0 if not act_stack else 0.0
        else:
            intersection = exp_stack.intersection(act_stack)
            scores["stack_accuracy"] = len(intersection) / len(exp_stack)
            
        # Protected Routes Accuracy
        exp_protected = expected.get("expected_protected_routes", 0)
        act_protected = len([n for n in actual.get("execution_graph", {}).get("nodes", []) if n["type"] == "AUTH_HANDLER"])
        
        if exp_protected == 0:
            scores["auth_detection_accuracy"] = 1.0 if act_protected == 0 else 0.0
        else:
            scores["auth_detection_accuracy"] = min(1.0, act_protected / exp_protected)

        return scores

    def _find_mismatches(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> List[Dict[str, Any]]:
        mismatches = []
        
        # Check architecture
        exp_arch = expected.get("expected_architecture")
        act_arch = actual.get("architecture_pattern", {}).get("value")
        if exp_arch and exp_arch != act_arch:
            mismatches.append({
                "category": "architecture",
                "expected": exp_arch,
                "actual": act_arch,
                "severity": "MEDIUM"
            })
            
        return mismatches

if __name__ == "__main__":
    # Example usage
    evaluator = OracleEvaluator()
    # Placeholder for actual runner logic
    print("Evaluator initialized.")
