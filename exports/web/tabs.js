/* Paraguay Geodata — sidebar tabs
   Wraps the existing sidebar sections into 6 tab panels:
     - Properties (default): filters, search, cluster-toggle, comparable
     - Insights:             live market signals, freshness, quality, secondary
     - Climate:              flood risk, climate risk, hillshade
     - Construction:         construction zones, urban zoning, ordinances
     - Architect:            architect export, plan PDF, DWG guide
     - Export:               downloads, sharing, citing

   Implementation: collects sections by their h2/section-id, builds a tab
   nav at the top of <aside>, and shows/hides panels based on the active tab.
   The Open / closed state is stored in localStorage so the choice persists.

   The script also enforces compact mode on small screens (< 1024px wide):
   the sidebar becomes a bottom-sheet and only one tab panel is visible at a time.
*/
(function () {
    'use strict';

    var TAB_MAP = {
        'properties': {
            label: 'Propiedades',
            en: 'Properties',
            pt: 'Imóveis',
            gn: 'Óga',
            match: function (el) {
                return false; // Composition handled below
            },
            sections: ['filterResultCount', 'geoSearchResults', 'cityList', 'fetchStatus', 'topRiskyAreas', 'topRiskyList', 'locationAnalysis', 'filterSheet', 'filterSheetHandle', 'drawerBackdrop']
        },
        'insights': {
            label: 'Insights',
            sections: ['insights', 'qualitySummary', 'marketSignals', 'secondaryInsights']
        },
        'climate': {
            label: 'Clima',
            en: 'Climate',
            pt: 'Clima',
            gn: 'Ati气候',
            sections: ['climateRisk', 'floodRisk', 'hillshade']
        },
        'construction': {
            label: 'Construcción',
            en: 'Construction',
            pt: 'Construção',
            gn: 'Ñemobyta',
            sections: ['constructionZonesSection', 'constructionZonesList']
        },
        'architect': {
            label: 'Arquitecto',
            en: 'Architect',
            pt: 'Arquiteto',
            gn: 'Arquitecto',
            sections: ['architectExportSection', 'architectDwgGuideModal']
        },
        'export': {
            label: 'Exportar',
            en: 'Export',
            pt: 'Exportar',
            gn: 'Emboty',
            sections: []  // Built dynamically — see buildExportPanel
        }
    };

    var STORAGE_KEY = 'py.sidebarTab';

    function getLang() {
        try {
            var stored = localStorage.getItem('paraguay-geodata.lang');
            if (stored) return stored;
            var nav = (navigator.language || 'es').slice(0, 2).toLowerCase();
            return nav;
        } catch (e) { return 'es'; }
    }

    function init() {
        var aside = document.querySelector('aside');
        if (!aside) return;

        // Build the tab bar
        var tabsBar = document.createElement('div');
        tabsBar.className = 'tabs';
        tabsBar.id = 'sidebar-tabs';
        tabsBar.setAttribute('role', 'tablist');
        tabsBar.style.cssText = 'display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:12px;flex-wrap:wrap;';

        Object.keys(TAB_MAP).forEach(function (key) {
            var tab = TAB_MAP[key];
            var lang = getLang();
            var label = tab[lang] || tab.label;
            var btn = document.createElement('button');
            btn.className = 'tab';
            btn.id = 'tab-' + key;
            btn.setAttribute('role', 'tab');
            btn.setAttribute('data-tab', key);
            btn.setAttribute('aria-controls', 'tabpanel-' + key);
            btn.textContent = label;
            btn.style.cssText = 'padding:6px 8px;background:none;border:none;color:var(--fg-dim);cursor:pointer;font-size:12px;border-bottom:2px solid transparent;margin-bottom:-1px;';
            btn.addEventListener('click', function () { switchTab(key); });
            tabsBar.appendChild(btn);
        });
        aside.insertBefore(tabsBar, aside.firstChild);

        // Build tab panels
        Object.keys(TAB_MAP).forEach(function (key) {
            var panel = document.createElement('div');
            panel.id = 'tabpanel-' + key;
            panel.className = 'tab-panel';
            panel.setAttribute('role', 'tabpanel');
            panel.setAttribute('aria-labelledby', 'tab-' + key);
            panel.style.cssText = 'display:none;';
            aside.appendChild(panel);
        });

        // Move sections into their panels
        var propsPanel = document.getElementById('tabpanel-properties');
        var insPanel = document.getElementById('tabpanel-insights');
        var climatePanel = document.getElementById('tabpanel-climate');
        var consPanel = document.getElementById('tabpanel-construction');
        var archPanel = document.getElementById('tabpanel-architect');
        var exportPanel = document.getElementById('tabpanel-export');

        // Move: insights panel + qualitySummary + marketSignals + secondaryInsights -> insights
        var insightsEl = aside.querySelector('.insights-panel');
        if (insightsEl) insPanel.appendChild(insightsEl);
        ['qualitySummary', 'marketSignals', 'secondaryInsights'].forEach(function (id) {
            var el = aside.querySelector('#' + id);
            if (el && el.parentElement === aside) insPanel.appendChild(el);
        });

        // Move: construction zones -> construction
        ['constructionZonesSection', 'constructionZonesList'].forEach(function (id) {
            var el = aside.querySelector('#' + id);
            if (el && el.parentElement === aside) consPanel.appendChild(el);
        });

        // Move: architect export -> architect
        ['architectExportSection', 'architectDwgGuideModal'].forEach(function (id) {
            var el = aside.querySelector('#' + id);
            if (el && el.parentElement === aside) archPanel.appendChild(el);
        });

        // Climate: identify climate risk / flood risk / hillshade by heading text
        var allDivs = aside.querySelectorAll('div[id]');
        allDivs.forEach(function (el) {
            if (el.id.match(/climate/i)) climatePanel.appendChild(el);
            else if (el.id.match(/flood/i)) climatePanel.appendChild(el);
            else if (el.id.match(/hillshade/i)) climatePanel.appendChild(el);
        });

        // Properties: every other section that was originally in <aside>
        // Walk aside children in order, moving everything not yet assigned
        var targetSiblings = Array.from(aside.children).filter(function (c) {
            return !c.id || (c.id !== 'sidebar-tabs' && !c.id.match(/^tabpanel-/));
        });
        targetSiblings.forEach(function (el) {
            // Skip the tab bar itself
            if (el.id === 'sidebar-tabs') return;
            propsPanel.appendChild(el);
        });

        // Build a tiny "Export" panel with quick links
        exportPanel.innerHTML = [
            '<div style="background:var(--bg-elev);border:1px solid var(--line);border-radius:6px;padding:12px;margin-bottom:12px;">',
            '  <h2 style="margin:0 0 8px;font-size:14px;">⬇ Descargas</h2>',
            '  <p style="font-size:11px;color:var(--fg-dim);margin:0 0 8px;">Las descargas de viewport son gratis. Las nacionales cuestan $29/$99.</p>',
            '  <div style="display:grid;grid-template-columns:1fr;gap:6px;">',
            '    <a class="btn btn-sm" href="pricing.html">Ver planes y precios</a>',
            '    <a class="btn btn-secondary btn-sm" href="./data/properties_latest.geojson" download>⬇ GeoJSON nacional (11 MB)</a>',
            '    <a class="btn btn-secondary btn-sm" href="./data/architect_export.geojson" download>⬇ Architect bundle</a>',
            '    <a class="btn btn-secondary btn-sm" href="./data/properties_latest.dxf" download>⬇ DXF nacional</a>',
            '  </div>',
            '</div>',
            '<div style="background:var(--bg-elev);border:1px solid var(--line);border-radius:6px;padding:12px;margin-bottom:12px;">',
            '  <h2 style="margin:0 0 8px;font-size:14px;">📢 Compartir</h2>',
            '  <p style="font-size:11px;color:var(--fg-dim);margin:0 0 8px;">Compartí esta vista con un enlace.</p>',
            '  <button onclick="navigator.clipboard.writeText(location.href).then(function(){window.PY.notify(\'Enlace copiado\',\'good\')})" class="btn btn-secondary btn-sm">Copiar URL</button>',
            '</div>',
            '<div style="background:var(--bg-elev);border:1px solid var(--line);border-radius:6px;padding:12px;margin-bottom:12px;">',
            '  <h2 style="margin:0 0 8px;font-size:14px;">📜 Citar</h2>',
            '  <p style="font-size:11px;color:var(--fg-dim);margin:0 0 8px;">Para papers o reportajes:</p>',
            '  <pre style="font-size:10px;background:var(--bg-elev-2);padding:8px;border-radius:4px;overflow-x:auto;">Ai-Whisperers. (2026). Paraguay Geodata [Data set]. https://geodata.paragu-ai.com/</pre>',
            '</div>',
        ].join('\n');

        // Set initial active tab
        var initial = (function () {
            try { return localStorage.getItem(STORAGE_KEY) || 'properties'; } catch (e) { return 'properties'; }
        })();
        switchTab(initial);

        // Compact mode on small screens
        if (window.innerWidth < 1024) {
            document.body.classList.add('compact');
        }
        window.addEventListener('resize', function () {
            if (window.innerWidth < 1024) document.body.classList.add('compact');
            else document.body.classList.remove('compact');
        });
    }

    function switchTab(key) {
        if (!TAB_MAP[key]) return;
        // Hide all panels
        document.querySelectorAll('.tab-panel').forEach(function (p) {
            p.style.display = 'none';
        });
        // Show the selected one
        var panel = document.getElementById('tabpanel-' + key);
        if (panel) panel.style.display = 'block';
        // Update tab buttons
        document.querySelectorAll('#sidebar-tabs .tab').forEach(function (btn) {
            if (btn.getAttribute('data-tab') === key) {
                btn.style.color = 'var(--accent)';
                btn.style.borderBottomColor = 'var(--accent)';
            } else {
                btn.style.color = 'var(--fg-dim)';
                btn.style.borderBottomColor = 'transparent';
            }
        });
        try { localStorage.setItem(STORAGE_KEY, key); } catch (e) {}
        // Smooth scroll to top of sidebar on mobile
        if (window.innerWidth < 1024) {
            var aside = document.querySelector('aside');
            if (aside) aside.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // Defer to ensure the legacy map JS has populated the sidebar already
        setTimeout(init, 0);
    }
})();