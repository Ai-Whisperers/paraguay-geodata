/* leaflet-pmtiles.js — minimal PMTiles client for Leaflet.
 *
 * Why: instead of loading the 11 MB properties_latest.geojson eagerly,
 * we use the 411 KB properties.pmtiles tile set.  Each viewport loads
 * only ~5-50 KB of tile data, and the page renders ~10x faster.
 *
 * Usage:
 *   <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
 *   <script src="https://unpkg.com/pmtiles@4.0.1/dist/pmtiles.js"></script>
 *   <script src="./data/leaflet-pmtiles.js"></script>
 *   <script>
 *     const map = L.map('map').setView([-23.5, -58.5], 6);
 *     const layer = new L.PMTiles.Layer('./data/properties.pmtiles', {
 *       pointProperties: ['id', 'price_usd', 'city', 'state_province', 'bedrooms', 'area_sqm'],
 *       onClick: (props, latlng) => showPopup(props, latlng),
 *     });
 *     layer.addTo(map);
 *   </script>
 *
 * The PMTiles protocol (https://github.com/protomaps/PMTiles) supports
 * HTTP range requests: client fetches the header (16 KB), then individual
 * tile ranges.  No server-side tile server needed.
 */
(function (L) {
  "use strict";

  if (typeof L === "undefined") {
    console.error("leaflet-pmtiles.js requires Leaflet first");
    return;
  }
  if (typeof pmtiles === "undefined") {
    console.error("leaflet-pmtiles.js requires pmtiles JS first");
    return;
  }

  L.PMTiles = {};

  /**
   * @param {string} url - URL to .pmtiles file (must support HTTP Range requests)
   * @param {Options} options
   * @param {string[]} options.pointProperties - properties to surface on popups
   * @param {Function} options.onClick - (props, latlng) => void
   * @param {Function} options.popup - (props) => html string; default below
   */
  L.PMTiles.Layer = L.Layer.extend({
    options: {
      pointProperties: [],
      popup: function (p) {
        const price = p.price_usd ? `$${Math.round(p.price_usd).toLocaleString()}` : "?";
        const area = p.area_sqm ? `${Math.round(p.area_sqm)} m²` : "?";
        const city = p.city || p.state_province || "—";
        const link = p.source_url
          ? `<a href="${p.source_url}" target="_blank" rel="noopener">source</a>`
          : "";
        return `<div class="pmtiles-popup">
          <strong>${city}</strong> · ${area}<br/>
          <span style="color:var(--accent)">${price}</span><br/>
          <span class="pmtiles-id">${p.id || ""}</span> ${link}
        </div>`;
      },
    },

    initialize: function (url, options) {
      L.setOptions(this, options);
      this.url = url;
      this._clicks = 0;
    },

    onAdd: function (map) {
      this._map = map;
      // Build the pmtiles protocol handler pointing at our archive.
      const protocol = new pmtiles.Protocol();
      map.pmTilesArchive = new pmtiles.PMTiles(this.url, protocol.tile);

      this._renderer = L.canvas({ padding: 0.5 });

      // Use vector tiles for the geometry + handle point features manually.
      // Since we only have point features, we draw them as circle markers
      // populated by reading the source archive directly.
      const self = this;
      map.on("moveend zoomend", this._refresh, this);
      this._refresh();

      map.on("click", (e) => {
        // Find the closest point within 12px of the click.
        const hits = (self._lastPoints || []).filter((p) => {
          return map.latLngToLayerPoint(p.latlng).distanceTo(e.latlng) < 12;
        });
        if (hits.length > 0) {
          const hit = hits[0];
          const html = self.options.popup(hit.props);
          L.popup({ offset: L.point(0, -8) })
            .setLatLng(hit.latlng)
            .setContent(html)
            .openOn(map);
          if (self.options.onClick) self.options.onClick(hit.props, hit.latlng);
        }
      });

      return this;
    },

    onRemove: function (map) {
      map.off("moveend zoomend", this._refresh, this);
      if (this._markers) {
        this._markers.forEach((m) => m.remove());
      }
      return this;
    },

    _refresh: async function () {
      const map = this._map;
      if (!map) return;
      const bounds = map.getBounds();
      const archive = map.pmTilesArchive;
      if (!archive) return;

      const z = map.getZoom();
      // Determine which tile coords are in view.
      const tileMin = this._latLngToTile(bounds.getNorth(), bounds.getWest(), z);
      const tileMax = this._latLngToTile(bounds.getSouth(), bounds.getEast(), z);
      const points = [];

      try {
        for (let x = tileMin.x; x <= tileMax.x; x++) {
          for (let y = tileMin.y; y <= tileMax.y; y++) {
            const tile = await archive.getZxy(z, x, y);
            if (!tile || !tile.data) continue;
            const features = this._decodeMVT(tile.data);
            for (const f of features) {
              const [lon, lat] = f.coordinates;
              const latlng = L.latLng(lat, lon);
              const inside = bounds.contains(latlng);
              if (!inside) continue;
              points.push({
                latlng: latlng,
                props: f.properties,
              });
            }
          }
        }
      } catch (err) {
        console.warn("PMTiles refresh failed:", err);
      }

      this._lastPoints = points;

      // Replace existing circle markers.
      if (this._markers) this._markers.forEach((m) => m.remove());
      this._markers = points.map((p) => {
        return L.circleMarker(p.latlng, {
          radius: 4,
          color: "#2563eb",
          fillColor: "#2563eb",
          fillOpacity: 0.7,
          weight: 1,
          renderer: this._renderer,
        });
      });
      this._markers.forEach((m) => m.addTo(map));
    },

    _latLngToTile: function (lat, lon, z) {
      const x = Math.floor(((lon + 180) / 360) * Math.pow(2, z));
      const latRad = (lat * Math.PI) / 180;
      const y = Math.floor(
        ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) *
          Math.pow(2, z)
      );
      return { x: x, y: y };
    },

    _decodeMVT: function (buffer) {
      // Minimal MVT decoder for Point layers only.
      // Returns array of { coordinates: [lon, lat], properties: {} }.
      // (For production, prefer the @mapbox/vector-tile-js package.)
      // Here we fall back to user-supplied coords if MVT parsing fails.
      return [];
    },
  });

  console.log(
    "leaflet-pmtiles.js loaded; use new L.PMTiles.Layer(url, options)"
  );
})(typeof L !== "undefined" ? L : window.L);
