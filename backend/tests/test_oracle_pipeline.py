import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.src.agents.oracle import OracleAgent
from backend.src.models.context import StructuredContext

async def test_oracle_pipeline():
    print("--- ORACLE Pipeline Verification ---")
    
    oracle = OracleAgent(prompt_version="v1")
    
    # Mock data
    session_id = "viva_session_999"
    input_data = {
        "report_path": None, # Skip for now as we don't have a real file
        "repo_url": "https://github.com/Project-XI/Project-EL" # Self-reference for testing structure analysis
    }
    
    print(f"\n1. Running ORACLE process for {input_data['repo_url']}...")
    context = await oracle.process(session_id, input_data)
    
    print("\n2. Verifying Structured Context Output:")
    context_dict = context.dict()
    
    # Check for evidence mapping
    print(f"Project Name: {context_dict['project_name']['value']} (Confidence: {context_dict['project_name']['confidence']})")
    print(f"Backend Framework: {context_dict['backend_framework']['value']}")
    print(f"Evidence for Backend: {context_dict['backend_framework']['evidence']}")
    
    # Check for Project Graph
    print(f"\n3. Verifying Project Graph:")
    graph = context_dict["project_graph"]
    print(f"Nodes: {[n['label'] for n in graph['nodes']]}")
    print(f"Edges: {len(graph['edges'])}")
    
    # Check for Viva Topics
    print(f"\n4. Verifying Viva Intelligence:")
    print(f"Possible Topics: {context_dict['possible_viva_topics']}")

    print("\n--- Pipeline Verification Complete ---")
    
    # Save sample output
    with open("backend/data/sample_context.json", "w") as f:
        json.dump(context_dict, f, indent=2)
    print(f"Sample output saved to backend/data/sample_context.json")

if __name__ == "__main__":
    asyncio.run(test_oracle_pipeline())
