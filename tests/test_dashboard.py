from pathlib import Path

import app
from src.dashboard import filter_events, load_project_data


def test_app_module_imports():
    assert app is not None


def test_dashboard_loads_normalized_events():
    events, incidents, report, skipped = load_project_data()
    assert len(events) == 130
    assert len(incidents) > 0
    assert report
    assert skipped == []


def test_incident_ids_are_available():
    _, incidents, _, _ = load_project_data()
    ids = {incident.incident_id for incident in incidents}
    assert "INC_001" in ids
    assert "INC_002" in ids
    assert "INC_003" in ids


def test_timeline_data_can_be_generated_for_incident():
    _, incidents, _, _ = load_project_data()
    for incident in incidents:
        if incident.incident_id in {"INC_001", "INC_002", "INC_003"}:
            timeline = incident
            assert len(timeline.events) > 0


def test_evidence_information_is_preserved_after_filtering():
    events, _, _, _ = load_project_data()
    filtered = filter_events(events, node="NODE_A")
    assert filtered
    for event in filtered:
        assert event.evidence_id
        assert event.source_file
        assert event.source_row > 0
