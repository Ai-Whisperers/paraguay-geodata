# 📋 Lucía — Datos que podés proveer / colaborar

**Live:** https://geodata.paragu-ai.com/ · **Repos:**
- Paraguay Geodata: https://github.com/Ai-Whisperers/paraguay-geodata
- LQV: https://github.com/Ai-Whisperers/la-quebrada-viva

## TL;DR

Tenés razón — sin las ordenanzas municipales + un mapa de zonas, no se puede responder "qué puedo construir acá". Ya hay una sección en el popup que muestra esto (zonas sintéticas por ahora, Asunción centro). Lo que falta es **datos reales**. Acá está la lista de qué nos podés pasar para que aparezca en el sitio.

## 🎯 Datos que podés descargar del sitio (para que uses vos misma)

En cada zona (cuando haya datos reales):

```
[Popup de propiedad]
📋 Zona de construcción
Villa Morra - Residencial R3 (denso)
Ord. 246/94 art. 24 - Zona R3

Altura máx:    25 m
Pisos:         7
COS:           60%
FOT:           400%
Retiro frontal: 3 m
Retiro lateral: 3 m
Permitido: vivienda, comercio, oficina, hotel boutique
Restringido: industrial, depósito, taller
```

También exportable el JSON completo desde `/data/construction_zones.json`.

## 📋 Datos que necesitamos de vos

### 1. Ordenanzas municipales (por ciudad)

Para cada ciudad, idealmente el texto completo de la **Ordenanza de Construcción**:

- **Asunción**: Ord. 246/94 + Plan Regulador 2010 (ya hay zonificación)
- **Ciudad del Este**: Ordenanzas municipales + plan regulador
- **Encarnación**: Plan de desarrollo urbano
- **Pilar, Pedro Juan Caballero, San Lorenzo, Capiatá, Luque, Fernando de la Mora**: cada una
- Cualquier otra que hagas análisis para

El formato que necesito por ciudad (puede ser Excel o lo que tengas):

```
| zone_id | category | name | max_height_m | max_floors | max_lot_coverage_pct | max_construction_pct | setback_front | setback_side | setback_back | allowed_use | restricted_use | ordinance_ref | last_updated |
```

### 2. Catastro urbano polygons

Si tenés los polígonos de zonificación en formato GeoJSON o shapefile, mejor aún — así podemos dibujarlos en el mapa en lugar de aproximarlos con bbox.

`/data/admin/catastro_urba.geojson` ya tiene **470 urbanizaciones** a nivel nacional, pero sin atributos de construcción. Si tenés un join con ordenanzas, perfecto.

### 3. Reportes de terreno

Si querés subir análisis puntuales (los que mencionás que hacés con 2 arquis), los podemos publicar como puntos de interés con:

```
{
  "type": "Feature",
  "geometry": {"type": "Point", "coordinates": [-57.57, -25.31]},
  "properties": {
    "kind": "terrain_analysis",
    "max_construction_m2": 180,
    "max_height_m": 12,
    "constraints": ["retiro costanera", "zona inundable"],
    "report_url": "https://...",
    "analyst": "Lucía Díaz",
    "date": "2026-07-13"
  }
}
```

## 🚀 Lo que ya tenemos en el sitio

| Feature | Status |
|---|---|
| Hillshade nacional (30m DEM, 4 regiones) | **Generando** — debería estar listo hoy |
| Hillshade por tile (5m para los 37 priority tiles) | Pendiente (próxima semana) |
| SoilGrids (texture, pH, organic carbon) | Pendiente |
| Catastro urban zoning (470 urbanizaciones) | ✓ ya está |
| Climate risk por depto (flood, drought, heatwave, wildfire) | ✓ ya está |
| Flood risk polygons (5 zonas Catastro WFS) | ✓ ya está |
| Indigenous territories (10 polígonos) | ✓ ya está |
| OSM water (247 features) | ✓ ya está |
| NASA POWER (Asunción 2024, 12-month strip) | ✓ ya está |
| GBIF biodiversity (200 species) | ✓ ya está |
| INBIO crops (soja, arroz, maíz zafriña) | ✓ ya está |
| Risk score por propiedad (10,754 analizadas) | ✓ ya está |

## 🛠️ Tu privacidad

Todo lo que subas es público (es la naturaleza del sitio). Si querés que algo sea privado (cliente específico, etc.) usamos git-lfs o un repo privado y sólo linkeamos.

## 📩 Para contactarme

- Email: erebus@ai-Whisperers.org
- Telegram: el chat que ya tenés
- GitHub issues: https://github.com/Ai-Whisperers/paraguay-geodata/issues

Si me pasás un CSV con la estructura de zonas de cualquier ciudad, lo integro en 30 min. Si tenés un GeoJSON con polígonos de zonificación, mejor.

— Erebus (en nombre de Ai-Whisperers / Paraguay AI)
2026-07-13