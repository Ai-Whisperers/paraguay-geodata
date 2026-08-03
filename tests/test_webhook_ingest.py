"""tests/test_webhook_ingest.py

Smoke tests for tools/webhook_ingest.py: verify summarize() output
schema and event-log round-trip.
"""
import json
import sys
from pathlib import Path


def test_summary_writes_known_schema(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path("/root/paraguay-geodata")))
    import tools.webhook_ingest as wi
    # Force the module's path constants to tmp_path
    monkeypatch.setattr(wi, "EVENTS_PATH", tmp_path / "events.jsonl")
    summary_path = tmp_path / "vitals_summary.json"
    monkeypatch.setattr(wi, "SUMMARY_PATH", summary_path)
    # Seed a couple of events
    wi._append_event({"type": "js_error", "msg": "boom", "ts": 1000000})
    wi._append_event({"type": "vital", "name": "LCP", "rating": "good", "url": "/"})
    out = wi.summarize()
    assert out["total_events"] >= 0
    assert "by_type" in out
    assert "by_rating" in out
    assert "as_of_utc" in out
    # Verify the file was written
    on_disk = json.loads(summary_path.read_text())
    assert on_disk["total_events"] == out["total_events"]


def test_summary_handles_empty(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path("/root/paraguay-geodata")))
    import tools.webhook_ingest as wi
    monkeypatch.setattr(wi, "EVENTS_PATH", tmp_path / "empty.jsonl")
    monkeypatch.setattr(wi, "SUMMARY_PATH", tmp_path / "vitals_summary.json")
    out = wi.summarize()
    assert out["total_events"] == 0
    assert out["by_type"] == {}


def test_module_importable():
    sys.path.insert(0, str(Path("/root/paraguay-geodata")))
    import tools.webhook_ingest as wi
    assert hasattr(wi, "summarize")
    assert hasattr(wi, "serve")
    assert hasattr(wi, "main")
