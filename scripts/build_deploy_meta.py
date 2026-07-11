{
  "commit": "HEAD",
  "branch": "main",
  "deployed_at_utc": "2026-07-10",
  "deployer": "Erebus",
  "project": "paraguay-geodata",
  "data_layers_loaded": [
    {
      "id": "tile_fabric",
      "label": "National tile fabric (10x10 km)",
      "features": 7912,
      "source": "derived",
      "phase": 0,
      "file": "data/tile_index.json"
    },
    {
      "id": "priority_tiles",
      "label": "Priority tiles (urban anchors)",
      "features": 37,
      "source": "derived",
      "phase": 0,
      "file": "data/priority_tiles.json"
    },
    {
      "id": "departamentos_py",
      "label": "Departamentos boundaries (OSM)",
      "features": 18,
      "source": "OpenStreetMap (ODbL)",
      "phase": 1,
      "file": "data/admin/departamentos.geojson",
      "size_b": 888831
    },
    {
      "id": "properties_infocasas",
      "label": "Real-estate listings (infocasas.com.py)",
      "features": 38,
      "source": "infocasas.com.py",
      "phase": 2,
      "file": "data/properties_latest.geojson",
      "size_b": 23392,
      "notes": "Live scraped Jul 11 2026, Central dept, 2 pages"
    },
    {
      "id": "gbif_species",
      "label": "Species observations (GBIF)",
      "features": 200,
      "unique_species": 138,
      "kingdoms": {"Animalia": 158, "Plantae": 42},
      "source": "GBIF",
      "phase": 1,
      "file": "data/gbif_paraguay.geojson",
      "size_b": 96654
    },
    {
      "id": "bcp_snapshot",
      "label": "BCP macro/monetary/rates snapshot",
      "source": "Banco Central del Paraguay",
      "phase": 1.5,
      "file": "data/bcp_snapshot.json",
      "highlights": "TPM 5.5%, PIB 2025 +6%, RIN $11.6B, morosidad bancos 2.29%, tasa activa ME 8.07%"
    },
    {
      "id": "nasa_power",
      "label": "NASA POWER daily climate 2024 (Asunción)",
      "source": "NASA POWER (no key)",
      "phase": 1,
      "file": "data/nasa_power_asuncion.json",
      "highlights": "2024 avg temp 23.7°C, precip 3.78 mm/day, solar 17.04 MJ/m2/day"
    }
  ],
  "live_features_total": 7912,
  "deferred_sources": [
    {"id": "distritos_osm",  "reason": "Overpass timeout on 262-district query; alternative datasource pending"},
    {"id": "bcp_rates_xlsx", "reason": "CDN 403 on direct XLSX download; using homepage snapshot"},
    {"id": "firms_active",   "reason": "Requires MAP_KEY from firms.modaps.eosdis.nasa.gov signup"},
    {"id": "datos_gov_py",   "reason": "Cloudflare challenge blocks programmatic access; 18 dept boundaries available via OSM directly"},
    {"id": "inbio_pdfs",     "reason": "PDF parsing of 30+ zafra reports pending; estimates preserved in finance.md catalog"},
    {"id": "hansen_jrc",     "reason": "STAC asset download not yet wired (Microsoft Planetary Computer auth tokenized)"}
  ]
}