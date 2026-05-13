from typing import Dict, Any, List
from .intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from .flows.auth_flow_analyzer import AuthFlowAnalyzer
from .flows.api_flow_analyzer import APIFlowAnalyzer
from .flows.middleware_chain_analyzer import MiddlewareChainAnalyzer
from .flows.db_flow_analyzer import DBFlowAnalyzer
from .flows.security_flow_analyzer import SecurityFlowAnalyzer
from .flows.failure_path_analyzer import FailurePathAnalyzer
from .framework_adapters.fastapi_adapter import FastAPIAdapter
from ...models.context import StructuredContext, VivaTarget

class ImplementationFlowEngine:
    """
    Orchestrates the implementation intelligence analyzers and synthesizes the ExecutionGraph.
    """
    
    @staticmethod
    def analyze_implementation(repo_path: str, structure: Dict[str, Any], context: StructuredContext) -> StructuredContext:
        builder = ExecutionGraphBuilder()
        
        # 1. Run Adapters (to be used by analyzers in next iteration)
        fastapi = FastAPIAdapter()
        routes = fastapi.extract_routes(repo_path, structure)
        
        # 2. Run Analyzers
        context.authentication_flow = AuthFlowAnalyzer.analyze(repo_path, structure, builder)
        context.api_lifecycle = APIFlowAnalyzer.analyze(repo_path, structure, builder)
        context.middleware_chain = MiddlewareChainAnalyzer.analyze(repo_path, structure, builder)
        context.database_interaction_flow = DBFlowAnalyzer.analyze(repo_path, structure, builder) # Note: Added field name correction if needed
        context.security_flows = [] # Aggregation
        context.runtime_risks = SecurityFlowAnalyzer.analyze(repo_path, structure, builder)
        context.failure_paths = FailurePathAnalyzer.analyze(repo_path, structure, builder)
        
        # 3. Finalize Graph
        context.execution_graph = builder.get_graph()
        
        # 4. Generate Implementation Viva Targets
        context.implementation_viva_targets = [
            VivaTarget(
                topic="Authentication Flow",
                question_target="JWT Middleware Failure",
                difficulty="hard",
                importance_score=0.95,
                focus="What happens if JWT verification fails inside your middleware chain?"
            ),
            VivaTarget(
                topic="Database Reliability",
                question_target="Connection Resilience",
                difficulty="medium",
                importance_score=0.85,
                focus="What happens if the database connection fails during authentication?"
            )
        ]
        
        return context
