/* Paraguay Geodata — map cartography
   Adds cartographic essentials to the home-page Leaflet map:
     - scale bar (bottom-left)
     - north arrow (top-right)
     - live coordinate display (top-right)
     - legend overlay (bottom-right)
     - measure tool (top-right)
   Run after the main map is constructed.  Idempotent.
*/
(function () {
    'use strict';

    function ready(fn) {
        if (typeof window.map === 'object' && window.map && typeof window.map.addControl === 'function') {
            fn();
        } else {
            setTimeout(function () { ready(fn); }, 200);
        }
    }

    function buildCSS() {
        if (document.getElementById('py-map-css')) return;
        var css = document.createElement('style');
        css.id = 'py-map-css';
        css.textContent = [
            '#py-coord-display { background: rgba(20,20,31,0.92); color: var(--fg, #e8e8ee); border:1px solid var(--line, #2a2a3a); border-radius:4px; padding:4px 8px; font-size:11px; font-family: var(--mono, monospace); box-shadow: 0 1px 4px rgba(0,0,0,.4); }',
            '#py-north { background: rgba(255,255,255,.92); color:#000; border:1px solid #999; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:11px; box-shadow:0 1px 4px rgba(0,0,0,.4); margin-bottom:8px; }',
            '#py-legend { background: rgba(20,20,31,0.92); color: var(--fg, #e8e8ee); border:1px solid var(--line, #2a2a3a); border-radius:6px; padding:8px 12px; font-size:11px; line-height:1.6; box-shadow:0 1px 4px rgba(0,0,0,.4); max-width:200px; }',
            '#py-legend h4 { margin:0 0 6px; font-size:11px; color: var(--accent, #fbbf24); text-transform: uppercase; letter-spacing: .04em; }',
            '#py-legend .row { display:flex; align-items:center; gap:8px; margin:2px 0; }',
            '#py-legend .swatch { width:14px; height:14px; border-radius:2px; border:1px solid rgba(255,255,255,.2); }',
            '#py-measure-btn { background: rgba(20,20,31,0.92); color: var(--fg, #e8e8ee); border:1px solid var(--line, #2a2a3a); border-radius:4px; padding:6px 10px; font-size:11px; cursor:pointer; box-shadow:0 1px 4px rgba(0,0,0,.4); }',
            '#py-measure-btn:hover { background: rgba(245,158,11,0.2); border-color: var(--accent, #fbbf24); }',
            '#py-measure-btn.active { background: var(--accent, #fbbf24); color:#000; border-color: var(--accent, #fbbf24); }',
            '.py-measure-result { background: rgba(20,20,31,0.95); color: var(--fg, #e8e8ee); border:1px solid var(--accent, #fbbf24); border-radius:4px; padding:4px 8px; font-size:11px; font-family: var(--mono, monospace); margin:4px 0; }',
        ].join('\n');
        document.head.appendChild(css);
    }

    function addScaleBar() {
        if (!window.L || !window.L.control || !window.L.control.scale) return;
        var scale = window.L.control.scale({ position: 'bottomleft', metric: true, imperial: false, maxWidth: 200 });
        scale.addTo(window.map);
    }

    function addCoordDisplay() {
        var Display = window.L.Control.extend({
            onAdd: function () {
                var el = window.L.DomUtil.create('div', 'leaflet-bar');
                el.id = 'py-coord-display';
                el.innerHTML = '— · —';
                el.style.marginTop = '8px';
                el.style.marginRight = '8px';
                window.map.on('mousemove', function (e) {
                    el.innerHTML = e.latlng.lat.toFixed(4) + ' · ' + e.latlng.lng.toFixed(4);
                });
                window.map.on('mouseout', function () { el.innerHTML = '— · —'; });
                return el;
            }
        });
        new Display({ position: 'topright' }).addTo(window.map);
    }

    function addNorthArrow() {
        var North = window.L.Control.extend({
            onAdd: function () {
                var el = window.L.DomUtil.create('div', 'leaflet-bar');
                el.id = 'py-north';
                el.textContent = 'N';
                el.title = 'Norte';
                el.style.marginTop = '8px';
                el.style.marginRight = '8px';
                return el;
            }
        });
        new North({ position: 'topright' }).addTo(window.map);
    }

    function addLegend() {
        var Legend = window.L.Control.extend({
            onAdd: function () {
                var el = window.L.DomUtil.create('div');
                el.id = 'py-legend';
                el.innerHTML = [
                    '<h4>Capas activas</h4>',
                    '<div class="row"><span class="swatch" style="background:#ef4444"></span><span>Propiedades</span></div>',
                    '<div class="row"><span class="swatch" style="background:#0ea5e9"></span><span>Agua</span></div>',
                    '<div class="row"><span class="swatch" style="background:#a3a3a3"></span><span>Carreteras</span></div>',
                    '<div class="row"><span class="swatch" style="background:#dc2626"></span><span>Riesgo inundación</span></div>',
                    '<div class="row"><span class="swatch" style="background:#f59e0b"></span><span>Riesgo climático</span></div>',
                    '<div class="row"><span class="swatch" style="background:#84cc16"></span><span>Hillshade / relieve</span></div>',
                    '<div class="row"><span class="swatch" style="background:#7c3aed"></span><span>Zonas de construcción</span></div>',
                ].join('');
                return el;
            }
        });
        new Legend({ position: 'bottomright' }).addTo(window.map);
    }

    function addMeasure() {
        var Measure = window.L.Control.extend({
            onAdd: function () {
                var btn = window.L.DomUtil.create('button', 'leaflet-bar');
                btn.id = 'py-measure-btn';
                btn.textContent = '📏 Medir';
                btn.title = 'Medir distancia';
                btn.style.marginTop = '8px';
                btn.style.marginRight = '8px';
                btn.addEventListener('click', function () {
                    btn.classList.toggle('active');
                    if (window.PY_MEASURE && window.PY_MEASURE.active) {
                        window.PY_MEASURE.stop();
                    } else {
                        window.PY_MEASURE = startMeasure();
                    }
                });
                return btn;
            }
        });
        new Measure({ position: 'topright' }).addTo(window.map);
    }

    function startMeasure() {
        var points = [];
        var line = null;
        var markers = [];
        var resultEl = null;

        function onClick(e) {
            points.push(e.latlng);
            var m = window.L.circleMarker(e.latlng, { radius: 4, color: '#fbbf24', weight: 2, fillOpacity: 1 }).addTo(window.map);
            markers.push(m);
            if (points.length >= 2) {
                if (line) window.map.removeLayer(line);
                line = window.L.polyline(points, { color: '#fbbf24', weight: 3 }).addTo(window.map);
                updateResult();
            }
        }

        function updateResult() {
            var total = 0;
            for (var i = 1; i < points.length; i++) {
                total += points[i - 1].distanceTo(points[i]);
            }
            var text = '';
            if (total >= 1000) text = (total / 1000).toFixed(2) + ' km';
            else text = total.toFixed(0) + ' m';
            if (!resultEl) {
                resultEl = window.L.DomUtil.create('div', 'py-measure-result');
                document.querySelector('.leaflet-top.leaflet-right').appendChild(resultEl);
            }
            resultEl.textContent = 'Total: ' + text + ' (' + points.length + ' pts)';
        }

        function stop() {
            window.map.off('click', onClick);
            if (line) window.map.removeLayer(line);
            markers.forEach(function (m) { window.map.removeLayer(m); });
            if (resultEl) resultEl.remove();
            var btn = document.getElementById('py-measure-btn');
            if (btn) btn.classList.remove('active');
            window.PY_MEASURE = null;
        }

        window.map.on('click', onClick);
        return { active: true, stop: stop };
    }

    ready(function () {
        buildCSS();
        addScaleBar();
        addCoordDisplay();
        addNorthArrow();
        addLegend();
        addMeasure();
    });

})();