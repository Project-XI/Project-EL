import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.src.agents.oracle import OracleAgent
from backend.src.models.context import StructuredContext

async def test_oracle_pipeline():
    print("--- ORACLE Deep Implementation Intelligence Verification ---")
    
    oracle = OracleAgent(prompt_version="v2")
    
    # Mock data (using this repo itself for analysis)
    session_id = "viva_session_deep_intelligence"
    input_data = {
        "report_path": None, 
        "repo_url": "https://github.com/Project-XI/Project-EL" 
    }
    
    print(f"\n1. Running ORACLE Implementation Analysis for {input_data['repo_url']}...")
    context = await oracle.process(session_id, input_data)
    
    context_dict = context.model_dump()
    
    print("\n2. Verifying Execution Graph:")
    graph = context_dict["execution_graph"]
    print(f"Nodes: {len(graph['nodes'])}")
    for node in graph["nodes"][:5]:
        print(f"  - [{node['type']}] {node['label']}")
    
    print("\n3. Verifying Authentication Flow:")
    auth = context_dict["authentication_flow"]
    if auth:
        print(f"Confidence: {auth['confidence']}")
        for step in auth['steps'][:3]:
            print(f"  Step: {step}")
    
    print("\n4. Verifying Runtime Risks:")
    for risk in context_dict["runtime_risks"]:
        print(f"[{risk['severity']}] {risk['value']} (Conf: {risk['confidence']})")
    
    print("\n5. Verifying Implementation Viva Targets:")
    for target in context_dict["implementation_viva_targets"]:
        print(f"Topic: {target['topic']} | Focus: {target['focus']} [Score: {target['importance_score']}]")

    print("\n--- Pipeline Verification Complete ---")
    
    # Save sample output
    output_path = "backend/data/sample_context_v3.json"
    with open(output_path, "w") as f:
        json.dump(context_dict, f, indent=2)
    print(f"Sample output saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(test_oracle_pipeline())
