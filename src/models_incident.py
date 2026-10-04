"""
FlightStory AI - Incident Correlation Model

Defines the Incident data model for representing correlated events.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from src.models import NormalizedEvent


@dataclass
class CorrelationReason:
    """Explains why two or more events were grouped together."""
    reason: str  # e.g., "same incident_id", "temporal proximity", "fault->recovery"
    confidence: float  # 0.0 to 1.0


@dataclass
class Incident:
    """
    Represents a correlated group of events forming a single incident.
    
    An incident is a logical grouping of related events across one or more nodes
    that together tell a coherent story of system behavior.
    """
    
    # Identifiers
    incident_id: str  # Stable deterministic ID
    
    # Temporal bounds
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # System scope
    nodes: List[str] = field(default_factory=list)  # Affected nodes
    
    # Event categorization
    events: List[NormalizedEvent] = field(default_factory=list)  # All events
    fault_events: List[NormalizedEvent] = field(default_factory=list)  # Subset: faults
    recovery_events: List[NormalizedEvent] = field(default_factory=list)  # Subset: recovery
    
    # Correlation metadata
    correlation_reasons: List[CorrelationReason] = field(default_factory=list)
    confidence: float = 0.8  # Overall confidence in this correlation
    
    def __post_init__(self):
        """Ensure events are sorted chronologically."""
        self.events.sort(key=lambda e: e.timestamp)
        self.fault_events.sort(key=lambda e: e.timestamp)
        self.recovery_events.sort(key=lambda e: e.timestamp)
        # Deduplicate nodes
        self.nodes = sorted(list(set(self.nodes)))
    
    def __repr__(self):
        return (f"Incident(id={self.incident_id}, start={self.start_time.isoformat()}, "
                f"nodes={self.nodes}, event_count={len(self.events)})")
