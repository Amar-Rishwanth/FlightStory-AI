from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.models import NormalizedEvent
from src.normalizer import normalize_record

DATASET_FILES = {
    "operator_actions.csv": "data/operator_actions.csv",
    "system_state.csv": "data/system_state.csv",
    "guidance_events.csv": "data/guidance_events.csv",
    "faults_recovery.csv": "data/faults_recovery.csv",
}


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return rows
        for row in reader:
            if row is None:
                continue
            if not any((value or "").strip() for value in row.values()):
                continue
            rows.append({k: ("" if v is None else v.strip()) for k, v in row.items()})
    return rows


def import_all_datasets(base_dir: str | Path = ".") -> Tuple[List[NormalizedEvent], List[Dict[str, Any]], List[Dict[str, Any]]]:
    repo_root = Path(base_dir)
    all_events: List[NormalizedEvent] = []
    report: List[Dict[str, Any]] = []
    skipped_records: List[Dict[str, Any]] = []

    event_counter = 1

    for dataset_name, relative_path in DATASET_FILES.items():
        file_path = repo_root / relative_path
        rows = _read_csv_rows(file_path)
        imported_rows = 0
        dataset_skips: List[Dict[str, Any]] = []

        for source_row, row in enumerate(rows, start=2):
            try:
                event = normalize_record(
                    dataset_name=dataset_name,
                    row=row,
                    source_file=str(file_path),
                    source_row=source_row,
                    event_counter=event_counter,
                )
                all_events.append(event)
                event_counter += 1
                imported_rows += 1
            except Exception as exc:
                dataset_skips.append(
                    {
                        "dataset": dataset_name,
                        "source_row": source_row,
                        "reason": str(exc),
                        "raw_record": row,
                    }
                )
                skipped_records.append(
                    {
                        "dataset": dataset_name,
                        "source_row": source_row,
                        "reason": str(exc),
                        "raw_record": row,
                    }
                )

        report.append(
            {
                "dataset": dataset_name,
                "total_records": len(rows),
                "imported_records": imported_rows,
                "skipped_records": len(dataset_skips),
                "skip_reasons": [item["reason"] for item in dataset_skips],
            }
        )

    return all_events, report, skipped_records


def _print_import_report(report: List[Dict[str, Any]]) -> None:
    print("FlightStory AI - Import Report")
    print()
    print(f"{'Dataset':<26} {'Total':>8} {'Imported':>10} {'Skipped':>9}")
    print("-" * 62)
    total_events = 0
    for item in report:
        print(f"{item['dataset']:<26} {item['total_records']:>8} {item['imported_records']:>10} {item['skipped_records']:>9}")
        total_events += item["imported_records"]
    print("-" * 62)
    print(f"{'Total normalized events:':<26} {total_events:>8}")


def main() -> None:
    events, report, skipped = import_all_datasets(Path(__file__).resolve().parents[1])
    _print_import_report(report)
    if skipped:
        print()
        print("Skipped records:")
        for item in skipped[:10]:
            print(f"  - {item['dataset']} row {item['source_row']}: {item['reason']}")
    return None


if __name__ == "__main__":
    main()
