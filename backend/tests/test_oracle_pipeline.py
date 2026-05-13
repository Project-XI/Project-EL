import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.src.agents.oracle import OracleAgent
from backend.src.models.context import StructuredContext

async def test_oracle_pipeline():
    print("--- ORACLE Intelligence Pipeline Verification ---")
    
    oracle = OracleAgent(prompt_version="v2")
    
    # Mock data
    session_id = "viva_session_intelligence_test"
    input_data = {
        "report_path": None, 
        "repo_url": "https://github.com/Project-XI/Project-EL" 
    }
    
    print(f"\n1. Running ORACLE intelligence process for {input_data['repo_url']}...")
    context = await oracle.process(session_id, input_data)
    
    # Use Pydantic V2 model_dump()
    context_dict = context.model_dump()
    
    print("\n2. Verifying Architecture Inference:")
    arch = context_dict["architecture_pattern"]
    print(f"Value: {arch['value']}")
    print(f"Confidence: {arch['confidence']}")
    print(f"Evidence: {arch['evidence']}")
    
    print("\n3. Verifying Project Graph with Edges:")
    graph = context_dict["project_graph"]
    print(f"Nodes: {[n['label'] for n in graph['nodes']]}")
    for edge in graph["edges"]:
        print(f"Edge: {edge['source']} -> {edge['target']} ({edge['relationship']}) [Conf: {edge['confidence']}]")
        print(f"  Evidence: {edge['evidence']}")
    
    print("\n4. Verifying Probable Engineering Reasoning:")
    for r in context_dict["implementation_reasoning"]:
        print(f"Tech: {r['technology']}")
        print(f"  Reasoning: {r['probable_reasoning'][0]}")
    
    print("\n5. Verifying Viva Intelligence Targets:")
    for target in context_dict["viva_intelligence_targets"]:
        print(f"Topic: {target['topic']} | Focus: {target['focus']}")

    if context_dict["inconsistencies"]:
        print("\n6. Detected Inconsistencies:")
        for inc in context_dict["inconsistencies"]:
            print(f"Issue: {inc['issue']} [Severity: {inc['severity']}]")

    print("\n--- Pipeline Verification Complete ---")
    
    # Save sample output
    output_path = "backend/data/sample_context_v2.json"
    with open(output_path, "w") as f:
        json.dump(context_dict, f, indent=2)
    print(f"Sample output saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(test_oracle_pipeline())
