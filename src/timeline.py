from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from src.models import NormalizedEvent
from src.models_incident import Incident


@dataclass
class TimelineEvent:
    event_id: str
    evidence_id: str
    timestamp: datetime
    node: str
    log_family: str
    event_type: str
    category: Optional[str]
    code: Optional[str]
    severity: Optional[str]
    message: str
    state: Optional[str]
    source_file: str
    source_row: int
    relative_time_seconds: float


@dataclass
class IncidentTimeline:
    incident_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    nodes: List[str] = field(default_factory=list)
    timeline_events: List[TimelineEvent] = field(default_factory=list)
    fault_events: List[TimelineEvent] = field(default_factory=list)
    recovery_events: List[TimelineEvent] = field(default_factory=list)
    key_events: List[TimelineEvent] = field(default_factory=list)


def _event_is_fault(event: NormalizedEvent) -> bool:
    if event.log_family == "faults_recovery":
        return True
    if event.category and "fault" in str(event.category).lower():
        return True
    if event.event_type and "FAULT" in str(event.event_type).upper():
        return True
    if event.code and ("ERR_" in str(event.code).upper() or "FAULT" in str(event.code).upper()):
        return True
    return False


def _event_is_recovery(event: NormalizedEvent) -> bool:
    raw = event.raw_record
    if isinstance(raw, dict):
        status = str(raw.get("recovery_status") or "").upper()
        method = str(raw.get("recovery_method") or "").lower()
        if status and any(token in status for token in ["COMPLETED", "IN_PROGRESS", "ONGOING", "RECOVERY"]):
            return True
        if "recovery" in method:
            return True

    if event.category and "recovery" in str(event.category).lower():
        return True
    if event.event_type and "RECOVERY" in str(event.event_type).upper():
        return True
    if event.message and ("recover" in str(event.message).lower() or "recovery" in str(event.message).lower()):
        return True
    return False


def _event_is_guidance(event: NormalizedEvent) -> bool:
    return event.log_family == "guidance_events" or (event.category and "guidance" in str(event.category).lower())


def _event_is_operator_action(event: NormalizedEvent) -> bool:
    return event.log_family == "operator_actions"


def _event_is_state_change(event: NormalizedEvent) -> bool:
    return event.log_family == "system_state" or (event.event_type and "STATE" in str(event.event_type).upper())


def _to_timeline_event(event: NormalizedEvent, incident_start: datetime, relative_time_seconds: float) -> TimelineEvent:
    return TimelineEvent(
        event_id=event.event_id,
        evidence_id=event.evidence_id,
        timestamp=event.timestamp,
        node=event.node,
        log_family=event.log_family,
        event_type=event.event_type,
        category=event.category,
        code=event.code,
        severity=event.severity,
        message=event.message,
        state=event.state,
        source_file=event.source_file,
        source_row=event.source_row,
        relative_time_seconds=relative_time_seconds,
    )


def _timeline_priority(event: NormalizedEvent) -> int:
    if _event_is_fault(event):
        return 0
    if _event_is_recovery(event):
        return 1
    if _event_is_guidance(event):
        return 2
    if _event_is_operator_action(event):
        return 3
    if _event_is_state_change(event):
        return 4
    return 5


def build_incident_timeline(incident: Incident) -> IncidentTimeline:
    """Convert a correlated Incident into a deterministic, evidence-linked timeline."""
    if not incident.events:
        return IncidentTimeline(
            incident_id=incident.incident_id,
            start_time=incident.start_time,
            end_time=incident.end_time,
            duration_seconds=incident.duration_seconds,
            nodes=list(incident.nodes),
            timeline_events=[],
            fault_events=[],
            recovery_events=[],
            key_events=[],
        )

    timeline_events: List[TimelineEvent] = []
    for event in sorted(incident.events, key=lambda e: e.timestamp):
        delta_seconds = (event.timestamp - incident.start_time).total_seconds()
        timeline_events.append(_to_timeline_event(event, incident.start_time, delta_seconds))

    fault_events = [te for te in timeline_events if any(e.evidence_id == te.evidence_id for e in incident.fault_events)]
    recovery_events = [te for te in timeline_events if any(e.evidence_id == te.evidence_id for e in incident.recovery_events)]

    selected: List[TimelineEvent] = []
    selected_evidence: set[str] = set()
    for te in sorted(timeline_events, key=lambda x: ( _timeline_priority(next(e for e in incident.events if e.evidence_id == x.evidence_id),), x.timestamp, x.evidence_id)):
        evidence_id = te.evidence_id
        if evidence_id in selected_evidence:
            continue
        if _event_is_fault(next(e for e in incident.events if e.evidence_id == evidence_id)):
            selected.append(te)
            selected_evidence.add(evidence_id)
            continue
        if _event_is_recovery(next(e for e in incident.events if e.evidence_id == evidence_id)):
            selected.append(te)
            selected_evidence.add(evidence_id)
            continue
        if _event_is_guidance(next(e for e in incident.events if e.evidence_id == evidence_id)):
            selected.append(te)
            selected_evidence.add(evidence_id)
            continue
        if _event_is_operator_action(next(e for e in incident.events if e.evidence_id == evidence_id)):
            selected.append(te)
            selected_evidence.add(evidence_id)
            continue
        if _event_is_state_change(next(e for e in incident.events if e.evidence_id == evidence_id)):
            selected.append(te)
            selected_evidence.add(evidence_id)
            continue

    # Keep the final key_events deterministic and stable.
    key_events = sorted(selected, key=lambda te: (te.relative_time_seconds, te.evidence_id))

    return IncidentTimeline(
        incident_id=incident.incident_id,
        start_time=incident.start_time,
        end_time=incident.end_time,
        duration_seconds=incident.duration_seconds,
        nodes=list(incident.nodes),
        timeline_events=timeline_events,
        fault_events=fault_events,
        recovery_events=recovery_events,
        key_events=key_events,
    )
