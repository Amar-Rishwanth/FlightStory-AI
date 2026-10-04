from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, List, Optional

from src.correlation import correlate_events
from src.importer import import_all_datasets


@lru_cache(maxsize=1)
def load_project_data():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    incidents = correlate_events(events)
    return events, incidents, report, skipped


def filter_events(
    events: Iterable[Any],
    node: str = "All",
    start: Optional[Any] = None,
    end: Optional[Any] = None,
    log_family: str = "All",
    category: str = "All",
) -> List[Any]:
    filtered: List[Any] = []
    for event in events:
        if node != "All" and event.node != node:
            continue
        if start is not None and event.timestamp < start:
            continue
        if end is not None and event.timestamp > end:
            continue
        if log_family != "All" and event.log_family != log_family:
            continue
        if category != "All" and str(event.category or "") != str(category):
            continue
        filtered.append(event)
    return filtered


def filter_incidents(
    incidents: Iterable[Any],
    node: str = "All",
    start: Optional[Any] = None,
    end: Optional[Any] = None,
    log_family: str = "All",
    category: str = "All",
    incident_id: str = "All",
) -> List[Any]:
    filtered: List[Any] = []
    for incident in incidents:
        if incident_id != "All" and incident.incident_id != incident_id:
            continue
        if node != "All" and node not in incident.nodes:
            continue

        included = []
        for event in incident.events:
            if start is not None and event.timestamp < start:
                continue
            if end is not None and event.timestamp > end:
                continue
            if log_family != "All" and event.log_family != log_family:
                continue
            if category != "All" and str(event.category or "") != str(category):
                continue
            if node != "All" and event.node != node:
                continue
            included.append(event)

        if included:
            filtered.append(incident)
    return filtered


def summarize_incident(incident: Any) -> str:
    fault_count = len(incident.fault_events)
    recovery_count = len(incident.recovery_events)
    return (
        f"Incident {incident.incident_id} involved {', '.join(incident.nodes)}. "
        f"The timeline contains {len(incident.events)} events, including {fault_count} fault events "
        f"and {recovery_count} recovery events. Related operator, state, guidance, fault, and recovery "
        "events were observed."
    )
