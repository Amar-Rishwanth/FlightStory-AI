from pathlib import Path

from src.importer import import_all_datasets
from src.correlation import correlate_events


def _load_events():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    return events, report, skipped


def test_all_130_events_can_be_processed():
    events, _, _ = _load_events()
    assert len(events) == 130
    incidents = correlate_events(events)
    assert len(incidents) > 0


def test_incidents_are_generated():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    assert len(incidents) > 0


def test_inc_001_exists():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    assert any(incident.incident_id == "INC_001" for incident in incidents)


def test_inc_002_exists():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    assert any(incident.incident_id == "INC_002" for incident in incidents)


def test_inc_003_exists():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    assert any(incident.incident_id == "INC_003" for incident in incidents)


def test_events_are_chronologically_ordered():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        if len(incident.events) > 1:
            times = [event.timestamp for event in incident.events]
            assert times == sorted(times)


def test_evidence_id_is_preserved():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        for event in incident.events:
            assert event.evidence_id


def test_source_file_and_row_are_preserved():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        for event in incident.events:
            assert event.source_file
            assert event.source_row > 0


def test_raw_record_is_preserved():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        for event in incident.events:
            assert event.raw_record


def test_correlation_reasons_are_present():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        assert incident.correlation_reasons
        for reason in incident.correlation_reasons:
            assert reason.reason
            assert 0.0 <= reason.confidence <= 1.0


def test_explicit_incident_id_has_high_confidence():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        if incident.incident_id.startswith("INC_"):
            assert any(reason.confidence >= 0.95 for reason in incident.correlation_reasons)


def test_small_window_prevents_distant_grouping():
    events, _, _ = _load_events()
    incidents = correlate_events(events, correlation_window_seconds=5)
    for incident in incidents:
        if len(incident.events) > 1:
            delta = (incident.events[-1].timestamp - incident.events[0].timestamp).total_seconds()
            assert delta <= 60


def test_result_is_deterministic():
    events, _, _ = _load_events()
    first = correlate_events(events)
    second = correlate_events(events)
    assert [incident.incident_id for incident in first] == [incident.incident_id for incident in second]


def test_fault_events_are_identified():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        if incident.incident_id in {"INC_001", "INC_002", "INC_003"}:
            assert incident.fault_events


def test_recovery_events_are_identified():
    events, _, _ = _load_events()
    incidents = correlate_events(events)
    for incident in incidents:
        if incident.incident_id in {"INC_001", "INC_003"}:
            assert incident.recovery_events
