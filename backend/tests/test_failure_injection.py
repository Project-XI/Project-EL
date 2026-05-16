import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.agents.oracle import OracleAgent

async def test_failure_injection():
    print("--- Failure Injection & Robustness Test ---")
    oracle = OracleAgent()
    
    # Test 1: Non-existent Repo
    print("\n[Test 1] Analyzing non-existent repo...")
    try:
        context = await oracle.process("fail_test_1", {"repo_url": "https://github.com/Project-XI/NonExistentRepo"})
        print(f"Result: {context.project_name.value}")
    except Exception as e:
        print(f"Expected Failure: {str(e)}")

    # Test 2: Repo with deep nesting (simulated by using current repo)
    print("\n[Test 2] Analyzing complex repo structure...")
    context = await oracle.process("fail_test_2", {"repo_url": "https://github.com/Project-XI/Project-EL"})
    print(f"Success: Found {len(context.execution_graph.nodes)} execution nodes.")

if __name__ == "__main__":
    asyncio.run(test_failure_injection())
