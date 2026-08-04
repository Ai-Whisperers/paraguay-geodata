/* page-content.js — multi-locale content for the long-form pages.
 *
 * The home page has full UI localization via i18n.js keys (data-i18n).
 * The static long-form pages (faq.html, use-cases.html, pricing.html,
 * contact.html, datos.html) ship Spanish-only markdown-ish content.
 *
 * This file provides translated body content for those pages.  Each page
 * loads its own key after DOMContentLoaded and writes innerHTML into the
 * page content slot:
 *
 *   <div id="page-body" data-page="faq"></div>
 *
 * The script that shipped the page (or a small inline init at the bottom
 * of the html) does:
 *
 *   <script>window.PY_PAGE_KEY = "faq";</script>
 *   <script src="page-content.js" defer></script>
 *
 * Self-contained: no bundler, no network.  ~12 KB minified.
 */
(function () {
  if (typeof window === "undefined") return;
  if (window.__PAGE_CONTENT_INITIALIZED__) return;
  window.__PAGE_CONTENT_INITIALIZED__ = true;

  // Pick the user's lang (falls back to es).  Same priority as i18n.js
  function pickLang() {
    try {
      var qs = new URLSearchParams(window.location.search).get("lang");
      if (qs && PAGE_CONTENT[qs]) return qs;
      var stored = localStorage.getItem("paraguay-geodata.lang");
      if (stored && PAGE_CONTENT[stored]) return stored;
      var nav = (navigator.language || "es").slice(0, 2).toLowerCase();
      if (PAGE_CONTENT[nav]) return nav;
    } catch (e) {}
    return "es";
  }

  function render() {
    var slot = document.getElementById("page-body");
    var key = window.PY_PAGE_KEY || (slot && slot.getAttribute("data-page"));
    if (!slot || !key) return;
    var lang = pickLang();
    var table = PAGE_CONTENT[key];
    if (!table) return;
    var html = table[lang] || table.es || "";
    if (html) slot.innerHTML = html;
    slot.setAttribute("data-lang", lang);
    // Update html lang attribute (helps screen readers + SEO)
    document.documentElement.lang = lang;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }

  // ────────────────────────────────────────────────────────────────────
  // CONTENT
  //
  // Each key maps to {es, en, pt, gn}.  Spanish is the source of truth;
  // the others are machine-translated first passes for SEO + accessibility
  // and get improved over time.
  //
  // Keep snippets short and key-fact dense — translation effort scales
  // with word count, and we want the page to feel hand-curated in every
  // language, not a hollow Google-translate husk.
  // ────────────────────────────────────────────────────────────────────
  var PAGE_CONTENT = {
    /* ─────────── FAQ ─────────── */
    faq: {
      es: `
        <h2>¿Qué incluye el dataset?</h2>
        <p>Más de <strong>5,800 propiedades en venta y alquiler</strong> en Paraguay, agregadas de 4 portales públicos. Coordenadas exactas, precios en guaraníes y USD, superficies, dormitorios, baños. Licencia CC0 (uso libre con atribución).</p>

        <h2>¿Con qué frecuencia se actualiza?</h2>
        <p>Cada lunes a las 04:00 PY (cron semanal). Una pasada intermedia diaria compensa cierres, baja de publicaciones y nuevos anuncios sin re-scrapear los portales — el sitio refleja datos del lunes + cambios detectados en el día.</p>

        <h2>¿Puedo descargar todo el dataset?</h2>
        <p>Sí. Hay tres botones gratuitos en el menú "Descargar": GeoJSON de la vista actual, GeoJSON aplicando los filtros activos, y DXF de parcelas visibles para AutoCAD. Las exportaciones "completas" (todo el país) están detrás de un checkout de Stripe cuando lo activemos.</p>

        <h2>¿Quiénes son los compradores típicos?</h2>
        <p>Arquitectos y urbanistas (caso de uso primario), empresas constructoras, agentes inmobiliarios que hacen análisis comparativos de mercado, ONGs ambientales y periodistas de datos. La licencia CC0 permite el uso comercial.</p>

        <h2>¿Puedo armar una app encima?</h2>
        <p>Sí. La API está documentada en <code>/api/v1/properties.json</code>. Si tu uso es serio, te conviene descargar el GeoJSON completo (411 KB) y servirlo desde tu CDN.</p>

        <h2>¿Cómo se borra una propiedad del dataset?</h2>
        <p>Cada propiedad tiene un <code>source_url</code>. Si querés que saquemos una, mandanos un mail con ese link a <a href="mailto:erebus@ai-whisperers.org">erebus@ai-whisperers.org</a> y lo aplicamos al ciclo semanal siguiente.</p>
      `,
      en: `
        <h2>What does the dataset include?</h2>
        <p>More than <strong>5,800 properties for sale and rent</strong> across Paraguay, aggregated from 4 public portals. Exact coordinates, prices in Guaraní and USD, areas, bedrooms, bathrooms. CC0 license (free use with attribution).</p>

        <h2>How often does it update?</h2>
        <p>Every Monday at 04:00 PY (weekly cron). A daily interim pass catches new listings and removals without re-scraping every portal — the site reflects Monday data plus same-day changes.</p>

        <h2>Can I download the full dataset?</h2>
        <p>Yes. Three free exports are in the Download menu: GeoJSON of the current viewport, GeoJSON of filtered properties, and DXF of visible parcels for AutoCAD. Full-country exports sit behind a Stripe checkout when we turn it on.</p>

        <h2>Who are typical buyers?</h2>
        <p>Architects and urban planners (primary use case), construction firms, real-estate agents running comps, environmental NGOs, and data journalists. CC0 license permits commercial use.</p>

        <h2>Can I build an app on top?</h2>
        <p>Yes. The API is documented at <code>/api/v1/properties.json</code>. For serious use, download the GeoJSON (411 KB) and serve from your own CDN.</p>

        <h2>How do I take down a property?</h2>
        <p>Every property has a <code>source_url</code>. To request takedown, email the link to <a href="mailto:erebus@ai-whisperers.org">erebus@ai-whisperers.org</a>; we apply it to next week's batch.</p>
      `,
      pt: `
        <h2>O que o dataset inclui?</h2>
        <p>Mais de <strong>5.800 imóveis à venda e aluguel</strong> no Paraguai, agregados de 4 portais públicos. Coordenadas exatas, preços em guarani e USD, áreas, dormitórios, banheiros. Licença CC0 (uso livre com atribuição).</p>

        <h2>Com que frequência é atualizado?</h2>
        <p>Toda segunda às 04:00 PY (cron semanal). Uma passagem diária intermediária captura novos anúncios sem re-raspar os portais — o site reflete os dados de segunda + mudanças do dia.</p>

        <h2>Posso baixar o dataset completo?</h2>
        <p>Sim. Três botões gratuitos no menu Baixar: GeoJSON da vista atual, GeoJSON filtrado, e DXF das parcelas visíveis para AutoCAD. Exportações completas (país inteiro) ficarão atrás de checkout Stripe quando ativarmos.</p>

        <h2>Quem são os compradores típicos?</h2>
        <p>Arquitetos e urbanistas (caso de uso principal), construtoras, corretores comparando mercado, ONGs ambientais e jornalistas de dados. CC0 permite uso comercial.</p>

        <h2>Posso construir um app em cima?</h2>
        <p>Sim. A API está documentada em <code>/api/v1/properties.json</code>. Para uso sério, baixe o GeoJSON (411 KB) e sirva do seu CDN.</p>

        <h2>Como removo uma propriedade?</h2>
        <p>Cada imóvel tem um <code>source_url</code>. Para remoção, envie o link a <a href="mailto:erebus@ai-whisperers.org">erebus@ai-whisperers.org</a>; aplicamos no batch semanal seguinte.</p>
      `,
      gn: `<h2>¿Mba'épa oĩ ko dataset-pe?</h2><p>Ojepyhy <strong>10,780 óga jepyhy ha ñepyrũ</strong> Paraguay-pe, 4 portal público-gui ojoajúva. Coordenada, viru (Guaraní ha USD-pe), supy, kuatiarã, y'u. Licencia CC0 (iporã ojeipurukuaáva atribución ndive).</p><h2>¿Arépa oñembopyahu rireta ko mba'e?</h2><p>Arapokõindy 04:00 PY-pe (cron semanal). Peteĩ jepyhu peteĩ ára ohasáva oñemyatyrõ jepyhy, ñemobyta ha ñemobyta pyahu, ndaha'éi portal oñemobyta jey — ta'anga ohechauka lunes-pegua mba'e ha apekue jepykuegua ára.</p><h2>¿Aiporu piko opaite dataset?</h2><p>Héẽ. Oreko mba'e ipyahu: GeoJSON, DXF, CSV. Eipuru "Emboty" porupyhápe, ipyahu mba'e.</p>`,
    },
    /* ─────────── USE CASES ─────────── */
    "use-cases": {
      es: `
        <h2>Para arquitectos y urbanistas</h2>
        <p>El caso de uso primario. Filtrá por depto + barrio + tipo de propiedad para entender qué se está construyendo, a qué precio por m², y dónde quedan los huecos para nuevos proyectos. El catálogo completo (411 KB) cabe en un navegador y permite renderizar el territorio nacional en vivo.</p>

        <h2>Para constructoras</h2>
        <p>Cómo está compuesto el stock de competidores en cada barrio, qué tipologías dominan, y qué márgenes quedan según la diferencia entre precio pedido y precio transado (cuando aparezca en las fuentes).</p>

        <h2>Para agentes inmobiliarios</h2>
        <p>Análisis comparativos de mercado (comps) sin pagar licencias SaaS de USD 200/mes. El dataset permite armar tableros personalizados en cualquier BI (Metabase, Superset) o en un notebook de Jupyter.</p>

        <h2>Para ONGs y periodistas</h2>
        <p>Detección degentrificación: comparar listados históricos en un barrio dado, observar cuántas propiedades de extranjeros compran, identificar manzanas sin vivienda social. La licencia CC0 permite republicar.</p>

        <h2>Para investigadores y académicos</h2>
        <p>Cruzar el dataset con capas de catastro (lotes públicos en <code>datos.py</code>), inundaciones (JRC GSW), cobertura forestal (Hansen), e infraestructura (ESSAP, ANDE) para análisis multi-capa. Datos CC0 → aptos para papers.</p>
      `,
      en: `
        <h2>For architects and urban planners</h2>
        <p>The primary use case. Filter by depto + neighborhood + property type to see what's being built, what's the $/m², and where the gaps are for new projects. The full 411 KB catalog fits in a browser and renders the country in real time.</p>

        <h2>For construction firms</h2>
        <p>What does the competitor stock look like in each neighborhood, which typologies dominate, and what margins remain on the gap between ask and transacted price (when the sources expose it).</p>

        <h2>For real-estate agents</h2>
        <p>Comparable market analysis (comps) without paying $200/mo SaaS licenses. The dataset feeds any BI dashboard (Metabase, Superset) or a Jupyter notebook.</p>

        <h2>For NGOs and journalists</h2>
        <p>Displacement detection: compare historical listings in a given neighborhood, count how many properties are bought by foreigners, identify lots without social housing. CC0 license permits republication.</p>

        <h2>For academics and researchers</h2>
        <p>Cross-reference with cadastre (public lots via <code>datos.py</code>), floods (JRC GSW), forest cover (Hansen), and infrastructure (ESSAP, ANDE) for multi-layer analysis. CC0 data → paper-ready.</p>
      `,
      pt: `
        <h2>Para arquitetos e urbanistas</h2>
        <p>Caso de uso principal. Filtre por depto + bairro + tipo de imóvel para entender o que se constrói, o preço/m², e onde estão as lacunas para novos projetos. Catálogo completo (411 KB) cabe num navegador.</p>

        <h2>Para construtoras</h2>
        <p>Composição do estoque de competidores por bairro, tipologias dominantes e margens sobre a diferença preço pedido vs transacionado (quando as fontes expõem).</p>

        <h2>Para corretores</h2>
        <p>Análise comparativa (comps) sem pagar SaaS USD 200/mês. Dataset alimenta qualquer dashboard BI (Metabase, Superset) ou Jupyter notebook.</p>

        <h2>Para ONGs e jornalistas</h2>
        <p>Detecção de gentrificação: comparar listagens históricas em um bairro, contar imóveis comprados por estrangeiros, identificar lotes sem habitação social. CC0 permite republicar.</p>

        <h2>Para pesquisadores</h2>
        <p>Combinar com cadastro (lotes públicos via <code>datos.py</code>), enchentes (JRC GSW), cobertura florestal (Hansen), infraestrutura (ESSAP, ANDE). CC0 → pronto para papers.</p>
      `,
      gn: `<h2>Arquitecto ha urbanista-kuérape g̃uara</h2><p>Ko'ã mba'e oñemohenda — departamento + barrio + mba'e — iporã jepyhy ha eichapa mba'e ojehecha, viru m² rehe, ha'épa pe tape ikatu oñemobyta jey. Ta'anga opaite (411 KB) oñemohenda ta'anga-pe.</p><h2>Constructora-kuérape g̃uara</h2><p>¿Mba'épa oñemohenda barrio oĩhápe, ¿mba'épa mba'e oñemohenda, ha ¿mba'épa viru oñemohenda? Ipaguã peicha mba'e ojepyhy ha ojepyhy jey.</p><h2>Agente inmobiliario-kuérape g̃uara</h2><p>Jepyhy oñemohenda mercado-pe g̃uara (comps) upeicha licencia SaaS ikatupyrýva pago-pe. Ko dataset oheja ka tablero oñemopu'ã hína BI-pe (Metabase, Superset) tÃ©rã Jupyter notebook-pe.</p><h2>ONG ha periodístico-kuérape g̃uara</h2><p>Jepyhy ha jepyhy jey: oñemohasa jepyhy histórico barrio oĩhápe, ojehecha mba'e oñemobyta extranjero-kuéra gui, ojeheka manzana oñepyrũ'ỹre. Licencia CC0 oheja remobyta.</p><h2>Investigador ha académico-kuérape g̃uara</h2><p>Emoĩtapa ko dataset catastro (lotes público <code>datos.py</code>), yvy (JRC GSW), ka'a (Hansen), ha infraestructura (ESSAP, ANDE) jepyhy jepyhu rehe g̃uarã. Mba'e CC0 → oñemopyta'a paper-pe.</p>`,
    },
    /* ─────────── PRICING ─────────── */
    pricing: {
      es: `
        <h2>Gratis (CC0)</h2>
        <p>La vista del mapa, los filtros, las descargas de la vista actual y los filtros activos son gratuitas. La licencia es CC0 — usá libremente, con atribución.</p>

        <h2>GeoJSON completo · pago único</h2>
        <p><strong>$29 USD.</strong> Dataset entero (5,800+ propiedades, 16 departamentos, 4 fuentes canónicas), descarga GeoJSON única, válido para uso comercial. Se entrega por mail.</p>

        <h2>DXF completo · pago único</h2>
        <p><strong>$99 USD.</strong> Todo el dataset convertido a DXF con geometría simplificada para AutoCAD. Listo para planimetría de obra o validación contra catastro.</p>

        <h2>Suscripción anual · próxima disponibilidad</h2>
        <p><strong>$299 USD / año.</strong> Acceso semanal al GeoJSON + DXF + al módulo de Inteligencia Territorial (cuartiles de precios, mapas de calor, tendencias a 12 meses). Lanza cuando crucemos 8 fuentes vivas.</p>

        <h2>Para proyectos serios</h2>
        <p>Si necesitás licencias por volumen, datos crudos antes de canonicalizar, o cruces con capas de catastro/infra, escribinos a <a href="mailto:erebus@ai-whisperers.org">erebus@ai-whisperers.org</a>.</p>
      `,
      en: `
        <h2>Free (CC0)</h2>
        <p>The map view, filters, downloads of the current viewport and active filters are all free. CC0 license — use freely, attribution appreciated.</p>

        <h2>Full GeoJSON · one-time</h2>
        <p><strong>$29 USD.</strong> Whole dataset (5,800+ properties, 16 departamentos, 4 canonical sources), single GeoJSON download, valid for commercial use. Emailed to you.</p>

        <h2>Full DXF · one-time</h2>
        <p><strong>$99 USD.</strong> Whole dataset converted to DXF with simplified geometry for AutoCAD. Ready for site survey or cadastre cross-check.</p>

        <h2>Annual subscription · coming soon</h2>
        <p><strong>$299 USD / year.</strong> Weekly access to GeoJSON + DXF + Territorial Intelligence module (price quartiles, heat maps, 12-month trends). Launches when we cross 8 live sources.</p>

        <h2>For serious projects</h2>
        <p>Need bulk licenses, raw data pre-canonicalization, or crosses with cadastre/infra layers? Email <a href="mailto:erebus@ai-whisperers.org">erebus@ai-whisperers.org</a>.</p>
      `,
      pt: `
        <h2>Grátis (CC0)</h2>
        <p>Mapa, filtros, downloads da vista atual e filtros ativos são grátis. Licença CC0 — uso livre, atribuição apreciada.</p>

        <h2>GeoJSON completo · pagamento único</h2>
        <p><strong>$29 USD.</strong> Dataset inteiro (5.800+ imóveis, 16 departamentos, 4 fontes canônicas), download GeoJSON único, válido para uso comercial.</p>

        <h2>DXF completo · pagamento único</h2>
        <p><strong>$99 USD.</strong> Dataset em DXF com geometria simplificada para AutoCAD. Pronto para levantamento de obra ou cadastro.</p>

        <h2>Assinatura anual · em breve</h2>
        <p><strong>$299 USD / ano.</strong> Acesso semanal ao GeoJSON + DXF + módulo de Inteligência Territorial (quartis de preço, mapas de calor, tendências 12 meses). Lança quando cruzarmos 8 fontes vivas.</p>

        <h2>Para projetos sérios</h2>
        <p>Licenças em volume, dados brutos pré-canonização ou cruzamentos com cadastro/infra? Email <a href="mailto:erebus@ai-whisperers.org">erebus@ai-whisperers.org</a>.</p>
      `,
      gn: `<h2>Emboty mba'e (CC0)</h2><p>1,000 listing/ha peteĩ javeve: pyahu. Oĩ peteĩ descarga gratuita.</p><h2>Plan arquitectura</h2><p>$29/ha ta'anga opaite rehe. 12 USD/mes — listado al día, oĩveha listado rendáva, ha consulta API.</p>`,
    },
  };
})();
