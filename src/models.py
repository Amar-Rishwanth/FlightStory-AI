"""
FlightStory AI - Data Models

Defines the common event model for normalized log events.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class NormalizedEvent:
    """
    Common event model representing a normalized log record from any source.
    
    All fields preserve source data exactly as provided; no inference or invention.
    """
    
    # Core identifiers
    event_id: str  # EV-000001 format
    evidence_id: str  # For traceability; initially same as event_id
    
    # Temporal
    timestamp: datetime
    
    # Source and context
    node: str  # NODE_A, NODE_B, NODE_C
    log_family: str  # operator_actions, system_state, guidance_events, faults_recovery
    
    # Event classification
    event_type: str  # e.g., PARAMETER_CHANGE, STATE_TRANSITION, FAULT, RECOVERY
    category: str  # e.g., operational, performance, hardware, configuration
    
    # Event details
    code: Optional[str] = None  # error_code, guidance_id, action_type
    severity: Optional[str] = None  # info, warning, critical
    message: str = ""  # Human-readable summary
    
    # State tracking (mainly for system_state events)
    state: Optional[str] = None  # current state
    previous_state: Optional[str] = None  # for state transitions
    
    # Metrics/values
    value: Optional[float] = None  # metric value if applicable
    metadata: dict = field(default_factory=dict)  # Additional context
    
    # Source traceability
    source_file: str = ""  # e.g., data/operator_actions.csv
    source_row: int = 0  # Row number in source file (1-indexed)
    raw_record: dict = field(default_factory=dict)  # Complete original record
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        d = asdict(self)
        # Convert datetime to ISO string
        if isinstance(d['timestamp'], datetime):
            d['timestamp'] = d['timestamp'].isoformat()
        return d
    
    def __repr__(self):
        return (f"NormalizedEvent(event_id={self.event_id}, timestamp={self.timestamp}, "
                f"node={self.node}, event_type={self.event_type}, category={self.category})")
