import argparse
import asyncio
import sys
import json
import os
from src.agents.oracle import OracleAgent
from src.services.debug_visualizer.mermaid_generator import MermaidGenerator
from src.services.debug_visualizer.html_report_builder import HTMLReportBuilder

async def analyze_cmd(args):
    print(f"[*] Analyzing repository: {args.repo_url}")
    oracle = OracleAgent()
    context = await oracle.process("cli_session", {"repo_url": args.repo_url})
    
    # Simple summary output
    print(f"\n[✓] Project: {context.project_name.value}")
    print(f"[✓] Stack Detected: {context.backend_framework.value}")
    print(f"[✓] Architecture: {context.architecture_pattern.value}")
    print(f"[✓] Execution Nodes: {len(context.execution_graph.nodes)}")
    
    if args.report:
        report_path = args.report if isinstance(args.report, str) else "oracle_debug_report.html"
        HTMLReportBuilder.build(context, report_path)

    if args.debug:
        mermaid = MermaidGenerator.generate(context.execution_graph)
        print("\n--- Mermaid Flow ---")
        print(mermaid)
        print("--------------------")

async def evaluate_cmd(args):
    from evaluation.evaluation_runner import OracleEvaluator
    evaluator = OracleEvaluator()
    report = await evaluator.run_benchmark(args.repo_url, args.expected)
    
    print("\n--- Evaluation Report ---")
    print(f"Repo: {args.repo_url}")
    print(f"Stack Accuracy: {report['metrics']['stack_accuracy']*100:.1f}%")
    print(f"Auth Detection: {report['metrics']['auth_detection_accuracy']*100:.1f}%")
    
    if report["mismatches"]:
        print("\n[!] Mismatches Found:")
        for m in report["mismatches"]:
            print(f"  - {m['category']}: Expected '{m['expected']}', Got '{m['actual']}'")
    else:
        print("\n[✓] No major mismatches detected.")

async def explain_cmd(args):
    print(f"[*] Explaining claim: {args.claim_id}")
    # In a real scenario, we'd need a way to load the last context. 
    # For now, we simulate by running analysis if no context provided.
    from src.services.intelligence.explainability_engine import ExplainabilityEngine
    oracle = OracleAgent()
    context = await oracle.process("cli_explain", {"repo_url": args.repo_url if hasattr(args, 'repo_url') else "https://github.com/Project-XI/Project-EL"})
    
    explanation = ExplainabilityEngine.explain_claim(context, args.claim_id)
    
    if "error" in explanation:
        print(f"[!] {explanation['error']}")
    else:
        print(f"\n--- Explanation: {args.claim_id} ---")
        print(f"Claim: {explanation['claim']}")
        print(f"Reasoning: {explanation['reasoning']}")
        print(f"Confidence: {explanation['confidence']*100:.1f}%")
        print("\nEvidence:")
        for ev in explanation['evidence']:
            print(f"  - {ev}")

async def debug_cmd(args):
    print(f"[*] Debugging ExecutionGraph for: {args.repo_url}")
    oracle = OracleAgent()
    context = await oracle.process("cli_debug", {"repo_url": args.repo_url})
    
    print("\n--- Graph Anomaly Detection ---")
    nodes = context.execution_graph.nodes
    if not nodes:
        print("[!] Warning: Empty ExecutionGraph detected.")
    else:
        print(f"[✓] {len(nodes)} nodes found.")
        orphans = [n.id for n in nodes if not any(e.source == n.id or e.target == n.id for e in context.execution_graph.edges)]
        if orphans:
            print(f"[!] Found {len(orphans)} orphan nodes: {', '.join(orphans)}")
        else:
            print("[✓] No orphan nodes detected.")

def main():
    parser = argparse.ArgumentParser(prog="oracle", description="ORACLE Engineering Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("repo_url", help="GitHub repository URL")
    analyze_parser.add_argument("--debug", action="store_true", help="Show debug visualization")
    analyze_parser.add_argument("--report", nargs="?", const=True, help="Generate HTML debug report (optional path)")

    # Evaluate
    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate accuracy against benchmarks")
    evaluate_parser.add_argument("repo_url", help="Repository URL to evaluate")
    evaluate_parser.add_argument("--expected", required=True, help="Path to expected output JSON")

    # Explain
    explain_parser = subparsers.add_parser("explain", help="Explain an analysis claim")
    explain_parser.add_argument("claim_id", help="ID of the claim to explain")
    
    # Debug
    debug_parser = subparsers.add_parser("debug", help="Debug the ExecutionGraph")
    debug_parser.add_argument("repo_url", help="Repository URL to debug")

    args = parser.parse_args()

    if args.command == "analyze":
        asyncio.run(analyze_cmd(args))
    elif args.command == "evaluate":
        asyncio.run(evaluate_cmd(args))
    elif args.command == "explain":
        asyncio.run(explain_cmd(args))
    elif args.command == "debug":
        asyncio.run(debug_cmd(args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
