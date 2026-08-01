"""tests/test_fetch_century21.py

Covers tools/fetch_century21.py with synthetic HTML pages.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_century21 as fc21  # noqa: E402


INDEX_HTML = """
<html><body>
<a href="/propiedad/52033_casa-en-venta-en-republicano-asuncion-paraguay">casa</a>
<a href="/propiedad/52031_terreno-en-venta-en-san-vicente-asuncion-paraguay">terreno</a>
<a href="/propiedad/52035_departamento-en-alquiler-asuncion">depto</a>
<a href="/propiedad/52039_oficinas-en-venta-asuncion">oficina</a>
<a href="/noticia/12345">non-listing link</a>
</body></html>
"""


# Realistic detail-page HTML snippet — matches what Century21 serves.  The
# JSON record is inlined as one balanced object inside the HTML.
DETAIL_HTML_TPL = """
<html><head><title>Casa en venta</title></head>
<body>
<script>
window.filtrosArray = {{...}};
</script>
<div id="property-data">
{record}
</div>
</body></html>
"""


def _record(sid, **overrides):
    base = {
        "id": sid,
        "encabezado": "Casa de 4 dormitorios en Venta en Asunción",
        "precio": 350_000_000,
        "precio2": 46_666,
        "moneda": "PYG",
        "m2T": 280,
        "m2C": 240,
        "municipio": "Asunción",
        "estado": "Asunción",
        "pais": "Paraguay",
        "calle": "Av. España 1234",
        "municipio": "Asunción",
        "lat": -25.286,
        "lon": -57.633,
        "recamaras": 4,
        "banios": 3,
        "estacionamientos": 2,
        "tipoOperacion": "venta",
        "subTipoPropiedad": "casa",
        "descripcion": "Hermosa casa con piscina y jardín en zona céntrica.",
        "fotosArray": [
            {"large": "https://cdn.21online.lat/py/uploads/23/propiedades/{}/a.jpg".format(sid)},
            {"large": "https://cdn.21online.lat/py/uploads/23/propiedades/{}/b.jpg".format(sid)},
        ],
    }
    base.update(overrides)
    return base


def test_extract_prop_urls():
    urls = fc21._extract_prop_urls(INDEX_HTML)
    assert len(urls) == 4
    assert all("/propiedad/" in u for u in urls)
    assert all(u.startswith("https://century21.com.py/") for u in urls)


def test_parse_detail_extracts_core_fields():
    sid = "52033"
    html = DETAIL_HTML_TPL.format(record=json.dumps(_record(sid)))
    feat = fc21._parse_detail(html, f"https://century21.com.py/propiedad/{sid}_casa-en-venta-asuncion")
    assert feat is not None
    p = feat["properties"]
    assert p["source"] == "century21"
    assert p["source_id"] == sid
    assert p["state_province"] == "Asunción"
    assert p["city"] == "Asunción"
    assert p["price_pyg"] == 350_000_000
    assert p["area_sqm"] == 280
    assert p["bedrooms"] == 4
    assert p["bathrooms"] == 3
    assert p["property_type"] == "house"
    assert len(p["images"]) == 2


def test_parse_detail_usd_price():
    sid = "99001"
    rec = _record(sid, precio=85_000, moneda="USD")
    html = DETAIL_HTML_TPL.format(record=json.dumps(rec))
    feat = fc21._parse_detail(html, f"https://century21.com.py/propiedad/{sid}_x")
    assert feat["properties"]["price_usd"] == 85_000
    assert feat["properties"]["price_pyg"] == 637_500_000  # 85_000 * 7500


def test_parse_detail_rent_is_rent():
    sid = "99002"
    rec = _record(sid, tipoOperacion="renta")
    html = DETAIL_HTML_TPL.format(record=json.dumps(rec))
    feat = fc21._parse_detail(html, f"https://century21.com.py/propiedad/{sid}_x")
    assert feat["properties"]["listing_type"] == "rent"


def test_parse_detail_out_of_bounds_returns_none():
    sid = "99999"
    rec = _record(sid, lat=-34.9, lon=-56.0)  # Montevideo, not PY
    html = DETAIL_HTML_TPL.format(record=json.dumps(rec))
    feat = fc21._parse_detail(html, f"https://century21.com.py/propiedad/{sid}_x")
    assert feat is None


def test_parse_detail_missing_lat_lon_returns_none():
    sid = "99999"
    rec = _record(sid, lat=None, lon=None)
    html = DETAIL_HTML_TPL.format(record=json.dumps(rec))
    feat = fc21._parse_detail(html, f"https://century21.com.py/propiedad/{sid}_x")
    assert feat is None


def test_property_type_mapping():
    assert fc21._map_property_type("casa") == "house"
    assert fc21._map_property_type("casa-duplex") == "house"
    assert fc21._map_property_type("departamento") == "apartment"
    assert fc21._map_property_type("departamento-en-pozo") == "apartment"
    assert fc21._map_property_type("terreno") == "land"
    assert fc21._map_property_type("estancia/ganadera") == "land"
    assert fc21._map_property_type("local") == "commercial"
    assert fc21._map_property_type("bodega") == "commercial"
    assert fc21._map_property_type("edificio") == "commercial"
    assert fc21._map_property_type("") == "unknown"


def test_no_fetch_emits_empty_envelope(tmp_path):
    """CI-friendly: --no-fetch returns 0 listings, no network."""
    import subprocess
    r = subprocess.run(
        ["python3", "-m", "tools.fetch_century21", "--no-fetch",
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert r.returncode == 0, r.stderr
    files = list(tmp_path.glob("century21_*.geojson"))
    assert len(files) == 1
    d = json.loads(files[0].read_text())
    assert d["feature_count"] == 0
    assert d["features"] == []


# json is imported at top — helpers below re-use it.


# ────────────────────────────────────────────────────────────────────
# Index-page tests (REP_LOG_APP_PROPS hydration blob)
# ────────────────────────────────────────────────────────────────────
import json as _json  # noqa: E402


def _make_record(sid=51938, **over):
    rec = {
        "id": sid,
        "calle": "Av. Test 123",
        "municipio": "San Lorenzo",
        "estado": "Central",
        "pais": "Paraguay",
        "subTipoPropiedad": "casa",
        "encabezado": "Casa de prueba",
        "precio": 700000000,
        "moneda": "PYG",
        "m2T": 360,
        "m2C": 155,
        "recamaras": "2",
        "banios": "3",
        "estacionamientos": "2",
        "tipoOperacion": "venta",
        "lat": -25.33,
        "lon": -57.52,
        "urlCorrecta": f"/propiedad/{sid}_casa-en-venta",
        "fotosArray": [{"large": "https://cdn.21online.lat/a.jpg"}],
        "descripcion": "Hermosa casa.",
    }
    rec.update(over)
    return rec


def _page_html(records):
    """Wrap records in a fake REP_LOG_APP_PROPS hydration blob.  Note the
    PAGE-REAL syntax is JS (unquoted keys), which the parser must handle."""
    rec_json = [_json.dumps(r, ensure_ascii=False) for r in records]
    inner = ",\n".join(rec_json)
    return (
        "<html><body><script>\n"
        "window.REP_LOG_APP_PROPS = {\n"
        "filtrosArray: {},\n"
        "propiedades: [" + inner + "]\n"
        "};\n"
        "</script></body></html>"
    )


def test_extract_index_data_returns_parsed_records():
    html = _page_html([_make_record(sid=51938), _make_record(sid=51939)])
    recs = fc21._extract_index_data(html)
    assert len(recs) == 2
    assert recs[0]["id"] == 51938
    assert recs[1]["id"] == 51939


def test_extract_index_data_handles_escaped_quotes_in_strings():
    rec = _make_record(sid=51938, calle='Calle con \\"escaped\\" quotes')
    html = _page_html([rec])
    recs = fc21._extract_index_data(html)
    assert len(recs) == 1
    assert 'escaped' in recs[0]["calle"]


def test_extract_index_data_handles_nested_arrays_in_records():
    """Records contain nested arrays (fotosArray) and objects — make sure
    the brace walker doesn't bail at the first unbalanced char."""
    rec = _make_record(sid=51938, fotosArray=[
        {"large": "https://a.com/1.jpg"},
        {"large": "https://b.com/2.jpg"},
        {"large": "https://c.com/3.jpg"},
    ])
    html = _page_html([rec])
    recs = fc21._extract_index_data(html)
    assert len(recs) == 1
    assert len(recs[0]["fotosArray"]) == 3


def test_extract_index_data_no_propiedades():
    html = "<html><body><script>window.SOMETHING = {filtros: 1};</script></body></html>"
    recs = fc21._extract_index_data(html)
    assert recs == []


def test_parse_record_includes_urlCorrecta():
    feat = fc21._parse_record(_make_record(sid=51938))
    assert feat["properties"]["source_url"] == "https://century21.com.py/propiedad/51938_casa-en-venta"


def test_parse_record_usd():
    feat = fc21._parse_record(_make_record(sid=51999, precio=85000, moneda="USD"))
    assert feat["properties"]["price_usd"] == 85000
    assert feat["properties"]["price_pyg"] == 637_500_000