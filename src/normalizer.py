from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.models import NormalizedEvent

DATASET_NAME_MAP = {
    "operator_actions.csv": "operator_actions",
    "system_state.csv": "system_state",
    "guidance_events.csv": "guidance_events",
    "faults_recovery.csv": "faults_recovery",
}


def normalize_timestamp(value: Any, field_name: str = "timestamp") -> datetime:
    if value is None:
        raise ValueError(f"{field_name} is missing")
    text = str(value).strip()
    if text in {"", "null", "None", "nan"}:
        raise ValueError(f"{field_name} is missing")
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp for {field_name}: {value}") from exc


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "null", "None", "nan"}:
        return None
    return text


def parse_float(value: Any) -> Optional[float]:
    cleaned = clean_value(value)
    if cleaned is None:
        return None
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def event_id_for(index: int) -> str:
    return f"EV-{index:06d}"


def normalize_operator_actions(
    row: Dict[str, Any],
    source_file: str,
    source_row: int,
    event_counter: int,
) -> NormalizedEvent:
    ts = normalize_timestamp(row.get("timestamp"), "timestamp")
    node = clean_value(row.get("node"))
    if node is None:
        raise ValueError("Missing node")
    action_type = clean_value(row.get("action_type"))
    action_target = clean_value(row.get("action_target"))
    action_value = clean_value(row.get("action_value"))
    notes = clean_value(row.get("notes"))
    status = clean_value(row.get("status"))
    operator_id = clean_value(row.get("operator_id"))

    event_id = event_id_for(event_counter)
    message = notes or f"{action_type} on {node}"
    if action_target:
        message = f"{action_type} -> {action_target}"
        if action_value:
            message = f"{message} = {action_value}"
        if notes:
            message = f"{message}; {notes}"

    return NormalizedEvent(
        event_id=event_id,
        evidence_id=event_id,
        timestamp=ts,
        node=node,
        log_family="operator_actions",
        event_type=str(action_type or "ACTION"),
        category="operator_action",
        code=str(action_type) if action_type else None,
        severity=None,
        message=message,
        state=str(status) if status else None,
        value=parse_float(action_value),
        source_file=source_file,
        source_row=source_row,
        raw_record={k: clean_value(v) for k, v in row.items()},
    )


def normalize_system_state(
    row: Dict[str, Any],
    source_file: str,
    source_row: int,
    event_counter: int,
) -> NormalizedEvent:
    ts = normalize_timestamp(row.get("event_time"), "event_time")
    node = clean_value(row.get("system_id"))
    if node is None:
        raise ValueError("Missing node")

    category = clean_value(row.get("state_category"))
    previous_state = clean_value(row.get("previous_state"))
    current_state = clean_value(row.get("current_state"))
    trigger = clean_value(row.get("state_trigger"))
    cpu = parse_float(row.get("cpu_usage_pct"))
    memory_mb = parse_float(row.get("memory_mb"))
    temp = parse_float(row.get("temperature_c"))
    press = parse_float(row.get("pressure_bar"))

    event_id = event_id_for(event_counter)
    message = trigger or "state transition"
    if previous_state and current_state:
        message = f"{previous_state} -> {current_state}"
        if trigger:
            message = f"{message} ({trigger})"

    evt = NormalizedEvent(
        event_id=event_id,
        evidence_id=event_id,
        timestamp=ts,
        node=node,
        log_family="system_state",
        event_type="STATE_CHANGE",
        category=str(category or "state"),
        code=str(trigger) if trigger else None,
        severity=None,
        message=message,
        state=str(current_state) if current_state else None,
        value=cpu,
        source_file=source_file,
        source_row=source_row,
        raw_record={k: clean_value(v) for k, v in row.items()},
    )
    evt.metadata = {
        "cpu_usage_pct": cpu,
        "memory_mb": memory_mb,
        "temperature_c": temp,
        "pressure_bar": press,
    }
    return evt


def normalize_guidance_events(
    row: Dict[str, Any],
    source_file: str,
    source_row: int,
    event_counter: int,
) -> NormalizedEvent:
    ts = normalize_timestamp(row.get("guid_timestamp"), "guid_timestamp")
    node = clean_value(row.get("target_system"))
    if node is None:
        raise ValueError("Missing node")

    guidance_id = clean_value(row.get("guidance_id"))
    guidance_type = clean_value(row.get("guidance_type"))
    recommended_action = clean_value(row.get("recommended_action"))
    priority = clean_value(row.get("priority"))
    confidence = parse_float(row.get("confidence_level"))
    source_component = clean_value(row.get("source_component"))
    status = clean_value(row.get("status"))
    applied_by = clean_value(row.get("applied_by"))

    event_id = event_id_for(event_counter)
    message = recommended_action or f"{guidance_type} for {node}"

    evt = NormalizedEvent(
        event_id=event_id,
        evidence_id=event_id,
        timestamp=ts,
        node=node,
        log_family="guidance_events",
        event_type=str(guidance_type or "GUIDANCE"),
        category="guidance",
        code=str(guidance_id) if guidance_id else None,
        severity=str(priority) if priority else None,
        message=message,
        state=str(status) if status else None,
        value=confidence,
        source_file=source_file,
        source_row=source_row,
        raw_record={k: clean_value(v) for k, v in row.items()},
    )
    evt.metadata = {
        "source_component": source_component,
        "applied_by": applied_by,
        "priority": priority,
        "confidence_level": confidence,
    }
    return evt


def normalize_faults_recovery(
    row: Dict[str, Any],
    source_file: str,
    source_row: int,
    event_counter: int,
) -> NormalizedEvent:
    ts = normalize_timestamp(row.get("fault_timestamp"), "fault_timestamp")
    node = clean_value(row.get("node_name"))
    if node is None:
        raise ValueError("Missing node")

    fault_category = clean_value(row.get("fault_category"))
    error_code = clean_value(row.get("error_code"))
    fault_severity = clean_value(row.get("fault_severity"))
    affected_component = clean_value(row.get("affected_component"))
    root_cause = clean_value(row.get("root_cause_hypothesis"))
    recovery_method = clean_value(row.get("recovery_method"))
    recovery_status = clean_value(row.get("recovery_status"))
    recovery_ts = clean_value(row.get("recovery_timestamp"))
    recovery_duration = parse_float(row.get("recovery_duration_sec"))
    incident_id = clean_value(row.get("incident_id"))

    event_id = event_id_for(event_counter)
    message = root_cause or affected_component or "fault event"
    if affected_component:
        message = f"{affected_component}: {message}"

    evt = NormalizedEvent(
        event_id=event_id,
        evidence_id=event_id,
        timestamp=ts,
        node=node,
        log_family="faults_recovery",
        event_type="FAULT",
        category=str(fault_category or "fault"),
        code=str(error_code) if error_code else None,
        severity=str(fault_severity) if fault_severity else None,
        message=message,
        state=str(recovery_status) if recovery_status else None,
        value=recovery_duration,
        source_file=source_file,
        source_row=source_row,
        raw_record={k: clean_value(v) for k, v in row.items()},
    )
    evt.metadata = {
        "incident_id": incident_id,
        "affected_component": affected_component,
        "recovery_method": recovery_method,
        "recovery_status": recovery_status,
        "recovery_timestamp": recovery_ts,
        "recovery_duration_sec": recovery_duration,
    }
    return evt


def normalize_record(dataset_name: str, row: Dict[str, Any], source_file: str, source_row: int, event_counter: int) -> NormalizedEvent:
    dataset_name = dataset_name.split("/")[-1]
    if dataset_name == "operator_actions.csv":
        return normalize_operator_actions(row, source_file, source_row, event_counter)
    if dataset_name == "system_state.csv":
        return normalize_system_state(row, source_file, source_row, event_counter)
    if dataset_name == "guidance_events.csv":
        return normalize_guidance_events(row, source_file, source_row, event_counter)
    if dataset_name == "faults_recovery.csv":
        return normalize_faults_recovery(row, source_file, source_row, event_counter)
    raise ValueError(f"Unsupported dataset: {dataset_name}")
