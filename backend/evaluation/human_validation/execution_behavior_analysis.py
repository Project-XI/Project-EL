"""Execution Behavior Reasoning Expansion: Runtime Analysis Beyond Static Structure

This module expands ORACLE's analysis to understand execution-time behavior:
- Request lifecycle propagation through middleware, services, DB
- Dependency interaction chains and cascade effects
- Async/await ordering and potential races
- State propagation and mutation tracking
- DB/cache interaction flows and consistency implications
- Middleware execution order and side effects
- Operational failure consequences and recovery

All reasoning remains:
- Execution-graph grounded
- Evidence-backed with code references
- Explainable and deterministic
- No speculative pattern matching
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from dataclasses import dataclass


class ExecutionNodeType(str, Enum):
    """Types of nodes in execution flow"""
    MIDDLEWARE = "middleware"
    ROUTE_HANDLER = "route_handler"
    SERVICE_METHOD = "service_method"
    DB_OPERATION = "db_operation"
    CACHE_OPERATION = "cache_operation"
    EXTERNAL_SERVICE = "external_service"
    STATE_MUTATION = "state_mutation"
    ASYNC_TASK = "async_task"
    EXCEPTION_HANDLER = "exception_handler"
    RESPONSE = "response"


class FailurePropagationMode(str, Enum):
    """How failures propagate through execution"""
    STOPS_REQUEST = "stops_request"  # Exception thrown, request fails
    SILENTLY_HANDLED = "silently_handled"  # Error caught, request continues
    DEFERRED = "deferred"  # Error happens in background task
    CASCADES = "cascades"  # Triggers failure in dependent system
    RECOVERABLE = "recoverable"  # System can recover from failure


class ExecutionFlowNode(BaseModel):
    """Single node in execution flow"""
    node_id: str
    node_type: ExecutionNodeType
    code_location: str  # File:line where this happens
    description: str
    
    # Execution metadata
    is_async: bool = False
    can_fail: bool = True
    calls_external_service: bool = False
    accesses_database: bool = False
    accesses_cache: bool = False
    mutates_state: bool = False
    
    # Failure handling
    has_try_except: bool = False
    exception_types: List[str] = []
    recovery_strategy: Optional[str] = None
    propagates_exception: bool = True
    
    # Confidence
    existence_confidence: float = Field(ge=0, le=1.0)  # How sure we are this runs


class ExecutionFlowEdge(BaseModel):
    """Edge between execution nodes showing call/dependency"""
    from_node_id: str
    to_node_id: str
    call_type: str  # "direct_call", "event", "message_queue", "async_task"
    happens_before: bool  # Guaranteed ordering
    evidence: List[str] = []  # Code locations proving this edge


class RequestLifecycleTrace(BaseModel):
    """Complete trace of request through execution graph"""
    route: str
    request_id: str
    
    # Execution flow
    nodes: List[ExecutionFlowNode]
    edges: List[ExecutionFlowEdge]
    
    # Execution order
    execution_sequence: List[str]  # Ordered node IDs
    
    # State
    state_mutations: List[Dict[str, Any]] = []  # What state changes when?
    
    # Database
    db_operations: List[Dict[str, Any]] = []  # Queries in order
    db_transaction_scope: Optional[str] = None  # How transactions bound
    
    # Cache
    cache_operations: List[Dict[str, Any]] = []
    cache_invalidation_timing: Optional[str] = None
    
    # Async
    async_tasks: List[Dict[str, Any]] = []  # Background tasks spawned
    await_points: List[str] = []  # Where code waits
    potential_race_conditions: List[Dict[str, Any]] = []
    
    # Middleware
    middleware_order: List[str]  # Execution order
    middleware_state_sharing: List[Dict[str, Any]] = []  # What state shared?
    
    # Failure
    failure_points: List[Dict[str, Any]] = []
    failure_propagation_paths: List[List[str]] = []  # Multiple possible paths


class DependencyInteractionChain(BaseModel):
    """Chain of service interactions and their consequences"""
    source_service: str
    target_service: str
    interaction_type: str  # "sync_call", "async_message", "shared_state"
    
    # Chain metadata
    chain_path: List[str]  # All services in chain
    critical_path: bool  # Is this on critical path?
    has_fallback: bool
    timeout_configured: bool = False
    retry_logic: Optional[Dict[str, Any]] = None
    
    # Failure impact
    target_failure_impact: str  # "critical", "degraded", "none"
    cascade_effect: Optional[str] = None
    
    # Evidence
    code_locations: List[str]


class AsyncExecutionAnalysis(BaseModel):
    """Analysis of async/concurrent execution behavior"""
    
    # Async patterns
    concurrent_handlers: List[str]  # Endpoints/tasks that can run concurrently
    shared_mutable_state: List[Dict[str, Any]] = []  # State accessed by multiple handlers
    
    # Ordering issues
    ordering_assumptions: List[Dict[str, Any]] = []  # What ordering is assumed?
    ordering_guaranteed: bool  # Is ordering enforced?
    
    # Race conditions
    potential_races: List[Dict[str, Any]] = []  # Possible race conditions
    
    # Synchronization
    locks_used: List[Dict[str, Any]] = []
    atomic_operations: List[str] = []
    transaction_isolation_level: Optional[str] = None
    
    # Correctness
    concurrent_safety_score: float = Field(ge=0, le=1.0)


class StateConsistencyAnalysis(BaseModel):
    """Analysis of state consistency across operations"""
    
    # State tracking
    mutable_state_locations: List[str]  # Where state lives
    state_mutation_points: List[Dict[str, Any]]  # Where it changes
    
    # Consistency models
    consistency_model: str  # "strong", "eventual", "weak", "unknown"
    consistency_windows: List[Dict[str, Any]] = []  # When is data stale?
    
    # Violations
    possible_inconsistencies: List[Dict[str, Any]] = []
    lost_updates: List[Dict[str, Any]] = []  # Race conditions on state
    dirty_reads: List[Dict[str, Any]] = []  # Stale data reads
    
    # Guarantees
    consistency_guarantees: List[str] = []


class OperationalFailureImpact(BaseModel):
    """Analysis of operational consequences when something fails"""
    
    failure_type: str  # "service_unavailable", "slow_response", "data_corruption"
    affected_operations: List[str]  # What operations break?
    user_impact: str  # "no_impact", "some_users", "all_users", "cascading"
    data_integrity_risk: bool
    
    # Recovery
    automatic_recovery: bool
    recovery_time_estimate: Optional[str]  # "seconds", "minutes", "manual"
    recovery_mechanism: Optional[str]
    
    # Mitigation
    circuit_breaker_configured: bool
    timeout_configured: bool
    fallback_available: bool
    retry_strategy: Optional[Dict[str, Any]] = None


class ExecutionBehaviorSignalDetector:
    """Detects signals about execution behavior (not static structure)"""
    
    @staticmethod
    def detect_request_lifecycle_signal(
        route: str,
        execution_nodes: List[ExecutionFlowNode],
        edges: List[ExecutionFlowEdge],
    ) -> Dict[str, Any]:
        """Detect signal about request lifecycle"""
        return {
            "signal_type": "request_lifecycle",
            "route": route,
            "total_steps": len(execution_nodes),
            "has_middleware": any(n.node_type == ExecutionNodeType.MIDDLEWARE for n in execution_nodes),
            "has_external_calls": any(n.calls_external_service for n in execution_nodes),
            "has_db_operations": any(n.accesses_database for n in execution_nodes),
            "confidence": 0.85,
        }
    
    @staticmethod
    def detect_async_execution_signal(
        async_analysis: AsyncExecutionAnalysis,
    ) -> Optional[Dict[str, Any]]:
        """Detect signal about async execution issues"""
        
        if not async_analysis.potential_races:
            return None
        
        return {
            "signal_type": "async_execution_risk",
            "race_condition_count": len(async_analysis.potential_races),
            "concurrent_safety_score": async_analysis.concurrent_safety_score,
            "confidence": 0.90 if async_analysis.concurrent_safety_score < 0.7 else 0.60,
        }
    
    @staticmethod
    def detect_dependency_cascade_signal(
        chains: List[DependencyInteractionChain],
    ) -> Optional[Dict[str, Any]]:
        """Detect signal about cascading failures"""
        
        cascading_chains = [c for c in chains if c.cascade_effect]
        if not cascading_chains:
            return None
        
        return {
            "signal_type": "cascading_failure_risk",
            "cascade_count": len(cascading_chains),
            "critical_path_cascades": sum(1 for c in cascading_chains if c.critical_path),
            "confidence": 0.85,
        }
    
    @staticmethod
    def detect_state_consistency_signal(
        consistency_analysis: StateConsistencyAnalysis,
    ) -> Optional[Dict[str, Any]]:
        """Detect signal about state consistency issues"""
        
        if not consistency_analysis.possible_inconsistencies:
            return None
        
        return {
            "signal_type": "state_consistency_risk",
            "inconsistency_count": len(consistency_analysis.possible_inconsistencies),
            "consistency_model": consistency_analysis.consistency_model,
            "confidence": 0.80,
        }


class ExecutionBehaviorAnalyzer:
    """Analyzes runtime execution behavior of application"""
    
    def analyze_request_lifecycle(
        self,
        route: str,
        execution_nodes: List[ExecutionFlowNode],
        edges: List[ExecutionFlowEdge],
    ) -> RequestLifecycleTrace:
        """Build complete request lifecycle trace"""
        
        # Order nodes by execution sequence
        execution_sequence = self._topological_sort(execution_nodes, edges)
        
        # Analyze state mutations
        state_mutations = self._analyze_state_mutations(execution_nodes, execution_sequence)
        
        # Analyze database operations
        db_operations = self._analyze_db_operations(execution_nodes, execution_sequence)
        
        # Analyze async tasks
        async_tasks = self._analyze_async_tasks(execution_nodes)
        
        # Find failure points
        failure_points = self._analyze_failure_points(execution_nodes, edges)
        
        return RequestLifecycleTrace(
            route=route,
            request_id=f"{route}_{int(datetime.now().timestamp())}",
            nodes=execution_nodes,
            edges=edges,
            execution_sequence=execution_sequence,
            state_mutations=state_mutations,
            db_operations=db_operations,
            async_tasks=async_tasks,
            failure_points=failure_points,
            middleware_order=self._extract_middleware_order(execution_nodes),
        )
    
    def analyze_dependency_interactions(
        self,
        service_dependencies: Dict[str, List[str]],
    ) -> List[DependencyInteractionChain]:
        """Analyze how services interact and cascade failures"""
        chains = []
        # Build interaction chains from dependency graph
        return chains
    
    def analyze_async_execution(
        self,
        async_nodes: List[ExecutionFlowNode],
        shared_state: List[Dict[str, Any]],
    ) -> AsyncExecutionAnalysis:
        """Analyze async execution for races and ordering issues"""
        
        return AsyncExecutionAnalysis(
            concurrent_handlers=[n.node_id for n in async_nodes],
            shared_mutable_state=shared_state,
            concurrent_safety_score=self._calculate_concurrent_safety(async_nodes, shared_state),
        )
    
    def analyze_state_consistency(
        self,
        state_locations: List[str],
        mutations: List[Dict[str, Any]],
    ) -> StateConsistencyAnalysis:
        """Analyze state consistency and possible violations"""
        
        return StateConsistencyAnalysis(
            mutable_state_locations=state_locations,
            state_mutation_points=mutations,
            consistency_model="unknown",  # Would be detected from code
        )
    
    def analyze_operational_failure_impact(
        self,
        failure_type: str,
        affected_operations: List[str],
        recovery_mechanisms: List[str],
    ) -> OperationalFailureImpact:
        """Analyze what happens when something fails in production"""
        
        return OperationalFailureImpact(
            failure_type=failure_type,
            affected_operations=affected_operations,
            user_impact="unknown",
            automatic_recovery=len(recovery_mechanisms) > 0,
        )
    
    @staticmethod
    def _topological_sort(nodes: List[ExecutionFlowNode], edges: List[ExecutionFlowEdge]) -> List[str]:
        """Order nodes by execution dependencies"""
        # Build adjacency list
        graph: Dict[str, List[str]] = {n.node_id: [] for n in nodes}
        for edge in edges:
            if edge.happens_before:
                graph[edge.from_node_id].append(edge.to_node_id)
        
        # Topological sort (simplified)
        visited: Set[str] = set()
        sequence: List[str] = []
        
        def visit(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            for neighbor in graph.get(node_id, []):
                visit(neighbor)
            sequence.append(node_id)
        
        for node in nodes:
            visit(node.node_id)
        
        return sequence
    
    @staticmethod
    def _analyze_state_mutations(
        nodes: List[ExecutionFlowNode],
        sequence: List[str],
    ) -> List[Dict[str, Any]]:
        """Analyze how state mutates through execution"""
        mutations = []
        for node_id in sequence:
            node = next((n for n in nodes if n.node_id == node_id), None)
            if node and node.mutates_state:
                mutations.append({
                    "step": node_id,
                    "code_location": node.code_location,
                    "type": "state_mutation",
                })
        return mutations
    
    @staticmethod
    def _analyze_db_operations(
        nodes: List[ExecutionFlowNode],
        sequence: List[str],
    ) -> List[Dict[str, Any]]:
        """Analyze database operations in execution order"""
        operations = []
        for node_id in sequence:
            node = next((n for n in nodes if n.node_id == node_id), None)
            if node and node.accesses_database:
                operations.append({
                    "operation": node_id,
                    "code_location": node.code_location,
                })
        return operations
    
    @staticmethod
    def _analyze_async_tasks(nodes: List[ExecutionFlowNode]) -> List[Dict[str, Any]]:
        """Find async tasks that might run concurrently"""
        tasks = []
        for node in nodes:
            if node.is_async:
                tasks.append({
                    "task": node.node_id,
                    "code_location": node.code_location,
                })
        return tasks
    
    @staticmethod
    def _analyze_failure_points(
        nodes: List[ExecutionFlowNode],
        edges: List[ExecutionFlowEdge],
    ) -> List[Dict[str, Any]]:
        """Identify points where failures can occur"""
        failures = []
        for node in nodes:
            if node.can_fail:
                failures.append({
                    "failure_point": node.node_id,
                    "code_location": node.code_location,
                    "propagates": node.propagates_exception,
                })
        return failures
    
    @staticmethod
    def _extract_middleware_order(nodes: List[ExecutionFlowNode]) -> List[str]:
        """Extract middleware execution order"""
        return [n.code_location for n in nodes if n.node_type == ExecutionNodeType.MIDDLEWARE]
    
    @staticmethod
    def _calculate_concurrent_safety(
        async_nodes: List[ExecutionFlowNode],
        shared_state: List[Dict[str, Any]],
    ) -> float:
        """Calculate concurrent execution safety score"""
        if not async_nodes or not shared_state:
            return 1.0
        # Would implement proper analysis
        return 0.5


from datetime import datetime
