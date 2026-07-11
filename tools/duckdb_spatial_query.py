#!/usr/bin/env python3
"""tools/duckdb_spatial_query.py

Fast spatial queries on Paraguay Geodata using DuckDB + spatial extension.
No PostGIS needed — DuckDB is in-process, no server.

Use cases:
- Find all properties within X km of a point
- Calculate centroids per barrio
- Spatial joins
- Aggregate by H3 hexagons
- Distance computations

Setup:
  pip install duckdb
"""
import duckdb
import json
from pathlib import Path

ROOT = Path('/root/paraguay-geodata')
DATA_DIR = ROOT / 'exports/web/data'

def install_spatial():
    """Install DuckDB spatial extension (one-time)."""
    con = duckdb.connect(':memory:')
    con.execute("INSTALL spatial; LOAD spatial;")
    return con

def load_properties(con):
    """Load all properties into DuckDB."""
    con.execute(f"""
        CREATE TABLE properties AS
        SELECT
            json_extract_string(features, '$.properties.title') AS title,
            json_extract_string(features, '$.properties.source') AS source,
            json_extract_string(features, '$.properties.state_province') AS depto,
            json_extract_string(features, '$.properties.city') AS city,
            json_extract_string(features, '$.properties.property_type') AS prop_type,
            json_extract_string(features, '$.properties.listing_type') AS listing_type,
            json_extract(features, '$.properties.price_usd') AS price_usd,
            json_extract(features, '$.properties.area_ha') AS area_ha,
            json_extract(features, '$.properties.bedrooms') AS bedrooms,
            json_extract(features, '$.properties."$/ha"') AS usd_per_ha,
            json_extract(features, '$.properties.scraped_at_utc') AS scraped_at,
            json_extract(features, '$.geometry.coordinates[1]') AS lat,
            json_extract(features, '$.geometry.coordinates[0]') AS lon
        FROM (
            SELECT unnest(features) AS features
            FROM read_json_auto('{DATA_DIR}/properties_latest.geojson')
        )
    """)
    return con.execute("SELECT COUNT(*) FROM properties").fetchone()[0]

def demo_queries(con):
    """Run example queries."""

    print('=== QUERY 1: Most expensive deptos ===')
    rows = con.execute("""
        SELECT depto, COUNT(*) as cnt,
               ROUND(AVG(CAST(price_usd AS DOUBLE))) as avg_price,
               ROUND(AVG(CAST(usd_per_ha AS DOUBLE))) as avg_per_ha
        FROM properties
        WHERE CAST(price_usd AS DOUBLE) > 0 AND CAST(usd_per_ha AS DOUBLE) > 0 AND depto IS NOT NULL
        GROUP BY depto
        ORDER BY avg_price DESC
        LIMIT 10
    """).fetchall()
    for r in rows:
        print(f'  {r[0]:20s} {r[1]:>5} listings, ${r[2]:>10,.0f} avg, ${r[3]:>10,.0f}/ha')

    print('\n=== QUERY 2: Properties within 5km of Asunción centro ===')
    rows = con.execute("""
        SELECT COUNT(*) as nearby,
               ROUND(AVG(CAST(price_usd AS DOUBLE))) as avg_price,
               ROUND(AVG(CAST(area_ha AS DOUBLE)), 2) as avg_area
        FROM properties
        WHERE CAST(price_usd AS DOUBLE) > 0 AND lat IS NOT NULL
          AND ST_Distance_Spheroid(ST_Point(CAST(lon AS DOUBLE), CAST(lat AS DOUBLE)), ST_Point(-57.5759, -25.2637)) < 5000
    """).fetchall()
    print(f'  {rows[0][0]:,} properties, ${rows[0][1]:,.0f} avg, {rows[0][2]} ha avg')

    print('\n=== QUERY 3: Median price by listing type ===')
    rows = con.execute("""
        SELECT listing_type,
               ROUND(MEDIAN(CAST(price_usd AS DOUBLE))) as median_price,
               COUNT(*) as cnt
        FROM properties
        WHERE CAST(price_usd AS DOUBLE) > 1000 AND CAST(price_usd AS DOUBLE) < 10000000
        GROUP BY listing_type
    """).fetchall()
    for r in rows:
        print(f'  {r[0]:10s} ${r[1]:>10,.0f} median, {r[2]:>5,} listings')

    print('\n=== QUERY 4: Inventory by type ===')
    rows = con.execute("""
        SELECT prop_type, COUNT(*) as cnt
        FROM properties
        WHERE prop_type IS NOT NULL
        GROUP BY prop_type
        ORDER BY cnt DESC
    """).fetchall()
    for r in rows:
        print(f'  {r[0]:15s} {r[1]:>6,}')

    print('\n=== QUERY 5: Cheap deals (< 30th percentile price in depto) ===')
    rows = con.execute("""
        WITH depto_stats AS (
            SELECT depto, PERCENTILE_CONT(0.30) WITHIN GROUP (ORDER BY CAST(price_usd AS DOUBLE)) as p30
            FROM properties
            WHERE CAST(price_usd AS DOUBLE) > 1000 AND CAST(price_usd AS DOUBLE) < 10000000 AND depto IS NOT NULL
            GROUP BY depto
        )
        SELECT p.depto, p.title, CAST(p.price_usd AS DOUBLE) as price
        FROM properties p
        JOIN depto_stats d ON p.depto = d.depto
        WHERE CAST(p.price_usd AS DOUBLE) < d.p30 AND p.listing_type = 'sale'
        ORDER BY CAST(p.price_usd AS DOUBLE)
        LIMIT 10
    """).fetchall()
    for r in rows:
        title = r[1][:50] if r[1] else '?'
        print(f'  {r[0]:15s} ${r[2]:>10,.0f} {title}')


if __name__ == '__main__':
    try:
        con = install_spatial()
        count = load_properties(con)
        print(f'Loaded {count:,} properties into DuckDB\n')
        demo_queries(con)
    except Exception as e:
        print(f'Error: {e}')
        print('Install duckdb: pip install duckdb --break-system-packages')