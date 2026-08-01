"""tests/test_image_dedup.py

Covers tools/image_dedup.py without network access.

The --mock path forces the first 4 rows to share a phash and the next 4
to share another; this gives a deterministic duplicate-detection signal
that the cluster builder must group.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import image_dedup as idd  # noqa: E402


def _make_features(n: int) -> list[dict]:
    out = []
    for i in range(n):
        out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-55.8, -27.3]},
            "properties": {
                "id": f"x_{i}",
                "source": "tulugar",
                "source_id": f"x_{i}",
                "source_url": f"https://tulugar.com/{i}",
                "title": f"Lote {i}",
                "listing_type": "sale",
                "images": [f"https://cdn.example/{i}.jpg"] if i < 8 else [],
            },
        })
    return out


def test_hamming_zero():
    assert idd._hamming(0xDEADBEEF, 0xDEADBEEF) == 0


def test_hamming_threshold_groups_duplicates():
    a, b = 0xDEADBEEFCAFEBABE, 0xDEADBEEFCAFEBAB8  # 1 bit apart
    assert idd._hamming(a, b) <= 5


def test_hamming_threshold_separates_distinct():
    a, b = 0x0000000000000000, 0xFFFFFFFFFFFFFFFF  # 64 bits apart
    assert idd._hamming(a, b) > 5


def test_hash_features_drops_rent():
    feats = _make_features(3)
    feats[0]["properties"]["listing_type"] = "rent"
    feats[0]["properties"]["images"] = ["https://x"]
    rows, no_image = idd._hash_features(feats, limit=10)
    # rent is dropped at the row-build stage
    assert all(r["source_id"] != "x_0" for r in rows)


def test_hash_features_records_no_image():
    feats = _make_features(10)
    rows, no_image = idd._hash_features(feats, limit=10)
    assert len(no_image) == 2  # rows 8 and 9 have no image
    assert all(rows[i]["image_url"] for i in range(len(rows)))


def test_cluster_groups_identical_phashes():
    feats = _make_features(8)
    payload = idd._mock_run(feats, limit=8)
    # 4 rows with hash 0xDEADBEEFCAFEBABE and 4 with 0x1111... → 2 clusters
    assert len(payload["clusters"]) == 2
    sizes = sorted(c["size"] for c in payload["clusters"])
    assert sizes == [4, 4]


def test_cluster_records_unique_sources_per_cluster():
    feats = _make_features(4)
    # Vary sources on the 4 identical-phash rows to prove cross-source grouping.
    feats[0]["properties"]["source"] = "tulugar"
    feats[1]["properties"]["source"] = "infocasas"
    feats[2]["properties"]["source"] = "clasipar"
    feats[3]["properties"]["source"] = "tulugar"
    payload = idd._mock_run(feats, limit=4)
    assert len(payload["clusters"]) == 1
    sources = {p["source"] for p in payload["clusters"][0]["properties"]}
    assert {"tulugar", "infocasas", "clasipar"} <= sources


def test_empty_input_produces_empty_output():
    payload = idd._mock_run([], limit=0)
    assert payload["input_rows"] == 0
    assert payload["clusters"] == []