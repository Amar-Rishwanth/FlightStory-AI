from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional

from src.models import NormalizedEvent
from src.models_incident import CorrelationReason, Incident


def _extract_source_incident_id(event: NormalizedEvent) -> Optional[str]:
    raw = event.raw_record
    if isinstance(raw, dict):
        incident_id = raw.get("incident_id")
        if incident_id is not None and str(incident_id).strip():
            return str(incident_id).strip()
    return None


def _is_fault_event(event: NormalizedEvent) -> bool:
    if event.log_family == "faults_recovery":
        return True

    category = str(event.category or "").lower()
    if "fault" in category:
        return True

    event_type = str(event.event_type or "").upper()
    if "FAULT" in event_type:
        return True

    code = str(event.code or "").upper()
    if "ERR_" in code or "FAULT" in code:
        return True

    return False


def _is_recovery_event(event: NormalizedEvent) -> bool:
    raw = event.raw_record
    if isinstance(raw, dict):
        recovery_status = str(raw.get("recovery_status") or "").upper()
        recovery_method = str(raw.get("recovery_method") or "").lower()
        if recovery_status and any(token in recovery_status for token in ["COMPLETED", "IN_PROGRESS", "ONGOING", "RECOVERY"]):
            return True
        if "recovery" in recovery_method:
            return True

    category = str(event.category or "").lower()
    if "recovery" in category:
        return True

    event_type = str(event.event_type or "").upper()
    if "RECOVERY" in event_type:
        return True

    message = str(event.message or "").lower()
    if "recover" in message or "recovery" in message:
        return True

    return False


def _relationship_reason(event_a: NormalizedEvent, event_b: NormalizedEvent, window_seconds: int) -> Optional[str]:
    # strongest relationship: explicit source incident ID
    incident_a = _extract_source_incident_id(event_a)
    incident_b = _extract_source_incident_id(event_b)
    if incident_a and incident_b and incident_a == incident_b:
        return "same incident_id"

    delta_seconds = abs((event_a.timestamp - event_b.timestamp).total_seconds())

    if event_a.node == event_b.node and delta_seconds <= window_seconds:
        return "same node + temporal proximity"

    if event_a.node != event_b.node and delta_seconds <= window_seconds:
        if _is_fault_event(event_a) and event_b.log_family == "guidance_events":
            return "fault associated with guidance"
        if _is_fault_event(event_a) and _is_recovery_event(event_b):
            return "fault associated with recovery"
        if event_a.log_family == "system_state" and _is_fault_event(event_b):
            return "state change associated with fault"
        if event_a.log_family == "operator_actions" and _is_fault_event(event_b):
            return "operator action associated with fault"

    return None


def correlate_events(events: List[NormalizedEvent], correlation_window_seconds: int = 1800) -> List[Incident]:
    """
    Groups normalized events into deterministic, explainable incidents.

    rules:
    - preserve explicit incident IDs from source raw_record (e.g. INC_001)
    - same-node events within the time window are linked
    - cross-node events are linked only with meaningful relationship + time proximity
    - do not claim causality; use association language only
    """
    if not events:
        return []

    ordered = sorted(events, key=lambda e: e.timestamp)
    incidents: Dict[str, Incident] = {}
    event_to_incident: Dict[str, str] = {}

    # explicit source incident IDs are strongest and must be kept intact
    for event in ordered:
        incident_id = _extract_source_incident_id(event)
        if incident_id:
            if incident_id not in incidents:
                incidents[incident_id] = Incident(
                    incident_id=incident_id,
                    start_time=event.timestamp,
                    end_time=event.timestamp,
                    duration_seconds=0.0,
                    nodes=[event.node],
                    events=[event],
                    fault_events=[event] if _is_fault_event(event) else [],
                    recovery_events=[event] if _is_recovery_event(event) else [],
                    correlation_reasons=[CorrelationReason(reason="same incident_id", confidence=0.98)],
                    confidence=0.98,
                )
            else:
                incident = incidents[incident_id]
                incident.events.append(event)
                incident.nodes.append(event.node)
                incident.start_time = min(incident.start_time, event.timestamp)
                incident.end_time = max(incident.end_time, event.timestamp)
                incident.duration_seconds = (incident.end_time - incident.start_time).total_seconds()
                if _is_fault_event(event):
                    incident.fault_events.append(event)
                if _is_recovery_event(event):
                    incident.recovery_events.append(event)
                if not any(reason.reason == "same incident_id" for reason in incident.correlation_reasons):
                    incident.correlation_reasons.append(CorrelationReason(reason="same incident_id", confidence=0.98))
            event_to_incident[event.evidence_id] = incident_id

    # conservative grouping for remaining events
    unassigned = [e for e in ordered if e.evidence_id not in event_to_incident]

    for event in unassigned:
        matched = False
        for incident_id, incident in incidents.items():
            if event.timestamp < incident.start_time - timedelta(seconds=correlation_window_seconds):
                continue
            if event.timestamp > incident.end_time + timedelta(seconds=correlation_window_seconds):
                continue

            for existing_event in incident.events:
                reason = _relationship_reason(existing_event, event, correlation_window_seconds)
                if reason is None:
                    continue

                incident.events.append(event)
                incident.nodes.append(event.node)
                incident.start_time = min(incident.start_time, event.timestamp)
                incident.end_time = max(incident.end_time, event.timestamp)
                incident.duration_seconds = (incident.end_time - incident.start_time).total_seconds()
                if _is_fault_event(event):
                    incident.fault_events.append(event)
                if _is_recovery_event(event):
                    incident.recovery_events.append(event)

                reason_confidence = 0.85 if "same node" in reason else 0.70
                incident.correlation_reasons.append(CorrelationReason(reason=reason, confidence=reason_confidence))
                event_to_incident[event.evidence_id] = incident_id
                matched = True
                break

            if matched:
                break

        if not matched:
            generated_id = f"GEN_{len(incidents) + 1:03d}"
            incidents[generated_id] = Incident(
                incident_id=generated_id,
                start_time=event.timestamp,
                end_time=event.timestamp,
                duration_seconds=0.0,
                nodes=[event.node],
                events=[event],
                fault_events=[event] if _is_fault_event(event) else [],
                recovery_events=[event] if _is_recovery_event(event) else [],
                correlation_reasons=[CorrelationReason(reason="single event", confidence=0.50)],
                confidence=0.50,
            )
            event_to_incident[event.evidence_id] = generated_id

    final = sorted(incidents.values(), key=lambda incident: incident.start_time)
    for incident in final:
        incident.events = sorted(incident.events, key=lambda e: e.timestamp)
        incident.fault_events = sorted(incident.fault_events, key=lambda e: e.timestamp)
        incident.recovery_events = sorted(incident.recovery_events, key=lambda e: e.timestamp)
        incident.nodes = sorted(set(incident.nodes))
        incident.duration_seconds = (incident.end_time - incident.start_time).total_seconds()

    return final
