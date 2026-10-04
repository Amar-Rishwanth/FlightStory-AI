from pathlib import Path

from src.importer import import_all_datasets


def test_all_four_files_can_be_read():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    assert len(report) == 4
    dataset_names = {item["dataset"] for item in report}
    assert dataset_names == {
        "operator_actions.csv",
        "system_state.csv",
        "guidance_events.csv",
        "faults_recovery.csv",
    }


def test_events_are_generated():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    assert len(events) > 0
    assert sum(item["imported_records"] for item in report) == len(events)


def test_event_ids_are_unique():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    ids = [event.event_id for event in events]
    assert len(ids) == len(set(ids))


def test_evidence_ids_exist():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    assert all(event.evidence_id for event in events)


def test_timestamps_are_normalized():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    for event in events:
        assert hasattr(event.timestamp, "isoformat")


def test_source_traceability_is_preserved():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    for event in events:
        assert event.source_file
        assert event.source_row > 0
        assert event.raw_record


def test_skipped_records_are_reported():
    base_dir = Path(__file__).resolve().parents[1]
    events, report, skipped = import_all_datasets(base_dir)
    assert isinstance(skipped, list)
