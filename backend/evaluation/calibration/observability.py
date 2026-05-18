"""
Runtime Observability and Tracing Infrastructure

Provides deep visibility into:
- Signal generation process and reasoning
- Execution graph traversal and propagation
- Failure scenario construction
- Viva question generation logic

All traces remain grounded in code evidence with no speculation.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class TraceLevel(Enum):
    """Trace verbosity level."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TraceEvent:
    """Single trace event in analysis pipeline."""
    timestamp: str
    level: str
    component: str  # observable_signals, failure_analyzer, viva_generator
    event_type: str  # signal_detection, graph_traversal, etc.
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return asdict(self)


@dataclass
class SignalGenerationTrace:
    """Trace of observable signal generation process."""
    signal_name: str
    search_pattern: str
    files_searched: List[str]
    matches_found: int
    confidence_calculated: float
    confidence_reasoning: str
    evidence_files_collected: List[str]
    
    # Trace events during generation
    trace_events: List[TraceEvent] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "signal_name": self.signal_name,
            "search_pattern": self.search_pattern,
            "files_searched": len(self.files_searched),
            "matches_found": self.matches_found,
            "confidence": round(self.confidence_calculated, 3),
            "confidence_reasoning": self.confidence_reasoning,
            "evidence_files": self.evidence_files_collected,
            "trace_depth": len(self.trace_events),
        }


@dataclass
class PropagationTrace:
    """Trace of failure propagation through execution graph."""
    scenario_name: str
    trigger_node: str
    affected_path_count: int
    propagation_depth: int
    
    # Node-by-node traversal
    traversal_steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # Risk assessment reasoning
    risk_justification_steps: List[str] = field(default_factory=list)
    
    trace_events: List[TraceEvent] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "scenario_name": self.scenario_name,
            "trigger_node": self.trigger_node,
            "affected_paths": self.affected_path_count,
            "propagation_depth": self.propagation_depth,
            "traversal_steps": len(self.traversal_steps),
            "risk_reasoning_steps": self.risk_justification_steps,
        }


@dataclass
class VivaGenerationTrace:
    """Trace of viva question generation."""
    question_topic: str
    grounding_source: str  # failure_scenario, observable_signal, tech_detection
    code_patterns_matched: List[str]
    evidence_files: List[str]
    
    # Generation steps
    generation_steps: List[str] = field(default_factory=list)
    
    # Specificity reasoning
    specificity_reasoning: str = ""
    
    trace_events: List[TraceEvent] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "question_topic": self.question_topic,
            "grounding_source": self.grounding_source,
            "code_patterns_matched": len(self.code_patterns_matched),
            "evidence_files": self.evidence_files,
            "generation_steps": self.generation_steps,
        }


class TraceCollector:
    """Collects and manages traces during analysis."""
    
    def __init__(self):
        self.signal_traces: List[SignalGenerationTrace] = []
        self.propagation_traces: List[PropagationTrace] = []
        self.viva_traces: List[VivaGenerationTrace] = []
        self.all_events: List[TraceEvent] = []
    
    def add_signal_trace(self, trace: SignalGenerationTrace) -> None:
        """Add signal generation trace."""
        self.signal_traces.append(trace)
        self.all_events.extend(trace.trace_events)
    
    def add_propagation_trace(self, trace: PropagationTrace) -> None:
        """Add propagation trace."""
        self.propagation_traces.append(trace)
        self.all_events.extend(trace.trace_events)
    
    def add_viva_trace(self, trace: VivaGenerationTrace) -> None:
        """Add viva generation trace."""
        self.viva_traces.append(trace)
        self.all_events.extend(trace.trace_events)
    
    def add_event(self, event: TraceEvent) -> None:
        """Add raw trace event."""
        self.all_events.append(event)
    
    def get_traces_summary(self) -> Dict[str, Any]:
        """Get summary of all traces."""
        return {
            "total_events": len(self.all_events),
            "signal_traces": len(self.signal_traces),
            "propagation_traces": len(self.propagation_traces),
            "viva_traces": len(self.viva_traces),
            "timestamp": datetime.now().isoformat(),
        }
    
    def export_traces(self, format: str = "json") -> str:
        """Export all traces in specified format."""
        if format == "json":
            import json
            data = {
                "summary": self.get_traces_summary(),
                "signal_traces": [t.to_dict() for t in self.signal_traces],
                "propagation_traces": [t.to_dict() for t in self.propagation_traces],
                "viva_traces": [t.to_dict() for t in self.viva_traces],
                "events": [e.to_dict() for e in self.all_events],
            }
            return json.dumps(data, indent=2, default=str)
        
        raise ValueError(f"Unsupported trace format: {format}")


# Global trace collector
_global_trace_collector = TraceCollector()


def get_trace_collector() -> TraceCollector:
    """Get global trace collector instance."""
    return _global_trace_collector


def emit_trace_event(
    level: TraceLevel,
    component: str,
    event_type: str,
    message: str,
    evidence: Optional[Dict[str, Any]] = None,
) -> None:
    """Emit a trace event."""
    event = TraceEvent(
        timestamp=datetime.now().isoformat(),
        level=level.value,
        component=component,
        event_type=event_type,
        message=message,
        evidence=evidence or {},
    )
    _global_trace_collector.add_event(event)
