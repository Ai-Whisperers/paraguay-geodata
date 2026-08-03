// Paraguay Geodata — i18n strings
// Languages: es (default) · en · pt (Brazilian) · gn (Guaraní, official in PY)
//
// Usage in HTML:
//   <span data-i18n="home.title">Propiedades en Paraguay</span>
//   <span data-i18n-attr="placeholder" data-i18n="home.search">Buscar…</span>
//
// Languages can be switched at runtime via ?lang=en, the in-page <select>,
// or localStorage['paraguay-geodata.lang'].  Server-rendered pages always
// serve Spanish (default) so JS-disabled users still see content.

const i18n = {
    "es": {
        "site.title": "Paraguay Geodata — Visor nacional",
        "site.tagline": "5,784 propiedades · 16 ciudades · Cobertura nacional",
        "nav.home": "Nacional",
        "nav.data": "Datos",
        "nav.viewer": "Visor por tile",
        "nav.docs": "Docs",
        "nav.github": "GitHub",
        "nav.useCases": "Casos de uso",
        "nav.compare": "Comparar",
        "nav.faq": "FAQ",
        "nav.contact": "Contacto",
        "nav.changelog": "Cambios",
        "home.title": "5,784 propiedades en Paraguay",
        "home.subtitle": "Mapa interactivo de propiedades en venta y alquiler — construido con datos públicos abiertos.",
        "home.search": "Buscar dirección, ciudad o barrio…",
        "home.viewer": "Visor por tile",
        "home.compare": "Comparar propiedades",
        "home.useCases": "Para quién es esto",
        "home.investors.title": "Para inversores",
        "home.investors.body": "5,784 avisos · 3 fuentes (InfoCasas, TuLugar, Asunción.estate) · USD + PYG en cada listing.",
        "home.architects.title": "Para arquitectos",
        "home.architects.body": "Capas urbanas + climáticas + relieve. Exportá GeoJSON o DXF para QGIS / AutoCAD.",
        "home.farmers.title": "Para agrónomos",
        "home.farmers.body": "INBIO zafra + NASA POWER clima + GBIF biodiversidad por depto.",
        "home.government.title": "Para gobierno",
        "home.government.body": "Catastro, fiscalidad, riesgo climático — datos abiertos para planificar.",
        "home.cta.investors": "Ver 5,784 propiedades →",
        "home.cta.architects": "Abrir capas urbanas →",
        "home.cta.farmers": "Abrir capas agrícolas →",
        "home.cta.government": "Abrir datos públicos →",
        "home.metrics.listings": "Propiedades listadas",
        "home.metrics.cities": "Ciudades con cobertura",
        "home.metrics.sources": "Fuentes de datos",
        "home.metrics.freshness": "Edad mediana de datos",
        "tab.properties": "Propiedades",
        "tab.climate": "Clima",
        "tab.construction": "Construcción",
        "tab.insights": "Insights",
        "tab.architect": "Arquitecto",
        "tab.export": "Exportar",
        "filter.city": "Ciudad",
        "filter.source": "Fuente",
        "filter.price": "Precio",
        "filter.bedrooms": "Habitaciones",
        "filter.type": "Tipo",
        "filter.apply": "Aplicar",
        "filter.reset": "Limpiar",
        "listing.beds": "hab",
        "listing.baths": "baños",
        "listing.area": "m²",
        "listing.price": "Precio",
        "listing.daysOnMarket": "días en el mercado",
        "listing.source": "Fuente",
        "listing.openSource": "Ver aviso original",
        "listing.save": "Guardar",
        "listing.saved": "Guardado ✓",
        "listing.compare": "Comparar",
        "listing.share": "Compartir",
        "listing.copyLink": "Copiar enlace",
        "listing.linkCopied": "Enlace copiado",
        "saved.title": "Tus propiedades guardadas",
        "saved.empty": "Aún no guardaste ninguna propiedad. Hacé clic en ★ en cualquier listing.",
        "saved.clear": "Borrar todas",
        "compare.title": "Comparar propiedades",
        "compare.empty": "Elegí hasta 4 propiedades y hacé clic en \"Comparar\" para verlas una al lado de la otra.",
        "compare.table.price": "Precio",
        "compare.table.area": "Superficie",
        "compare.table.beds": "Habitaciones",
        "compare.table.baths": "Baños",
        "compare.table.city": "Ciudad",
        "compare.table.source": "Fuente",
        "compare.table.pricePerSqm": "Precio / m²",
        "compare.table.title": "Propiedad",
        "common.loading": "Cargando…",
        "common.error": "Algo falló",
        "common.retry": "Reintentar",
        "common.cancel": "Cancelar",
        "common.share": "Compartir",
        "common.close": "Cerrar",
        "common.menu": "Menú",
        "common.language": "Idioma",
        "common.lastUpdated": "Última actualización",
        "common.privacy": "Privacidad",
        "common.terms": "Términos",
        "common.license": "Código MIT · Datos CC0",
        "onboarding.step1.title": "Esto es el mapa nacional",
        "onboarding.step1.body": "5,784 propiedades en Paraguay, en una sola vista.",
        "onboarding.step2.title": "Hacé clic en un punto rojo",
        "onboarding.step2.body": "Para ver precio, área, habitaciones y el aviso original.",
        "onboarding.step3.title": "Filtrá por ciudad o fuente",
        "onboarding.step3.body": "En el panel de la derecha. Funciona en vivo.",
        "onboarding.step4.title": "Guardá o compará",
        "onboarding.step4.body": "Marcá con ★ para guardar, o usá \"Comparar\" para ver dos al lado.",
        "onboarding.step5.title": "Listo",
        "onboarding.step5.body": "Todo el código es MIT, los datos son CC0. Usá, copiá, mejorá.",
        "onboarding.skip": "Saltar",
        "onboarding.next": "Siguiente",
        "onboarding.done": "Empezar",
        "feedback.title": "Comentarios",
        "feedback.placeholder": "¿Qué cambiarías?",
        "feedback.send": "Enviar",
        "feedback.thanks": "¡Gracias!",
        "feedback.reportData": "Reportar dato incorrecto",
        "cookieBanner.text": "Usamos cookies para recordar idioma y propiedades guardadas. No rastreamos nada más.",
        "cookieBanner.accept": "Aceptar",
        "cookieBanner.decline": "Solo necesarias",
    },
    "en": {
        "site.title": "Paraguay Geodata — National Viewer",
        "site.tagline": "5,784 properties · 16 cities · National coverage",
        "nav.home": "National",
        "nav.data": "Data",
        "nav.viewer": "Per-tile viewer",
        "nav.docs": "Docs",
        "nav.github": "GitHub",
        "nav.useCases": "Use cases",
        "nav.compare": "Compare",
        "nav.faq": "FAQ",
        "nav.contact": "Contact",
        "nav.changelog": "Changelog",
        "home.title": "5,784 properties in Paraguay",
        "home.subtitle": "Interactive map of properties for sale and rent — built on public open data.",
        "home.search": "Search address, city or neighborhood…",
        "home.viewer": "Per-tile viewer",
        "home.compare": "Compare properties",
        "home.useCases": "Who is this for",
        "home.investors.title": "For investors",
        "home.investors.body": "5,784 listings · 3 sources (InfoCasas, TuLugar, Asunción.estate) · USD + PYG on every listing.",
        "home.architects.title": "For architects",
        "home.architects.body": "Urban + climate + terrain layers. Export GeoJSON or DXF for QGIS / AutoCAD.",
        "home.farmers.title": "For agronomists",
        "home.farmers.body": "INBIO harvest + NASA POWER climate + GBIF biodiversity by depto.",
        "home.government.title": "For government",
        "home.government.body": "Cadastre, taxation, climate risk — open data for planning.",
        "home.cta.investors": "View 5,784 properties →",
        "home.cta.architects": "Open urban layers →",
        "home.cta.farmers": "Open agriculture layers →",
        "home.cta.government": "Open public data →",
        "home.metrics.listings": "Listed properties",
        "home.metrics.cities": "Cities covered",
        "home.metrics.sources": "Data sources",
        "home.metrics.freshness": "Median data age",
        "tab.properties": "Properties",
        "tab.climate": "Climate",
        "tab.construction": "Construction",
        "tab.insights": "Insights",
        "tab.architect": "Architect",
        "tab.export": "Export",
        "filter.city": "City",
        "filter.source": "Source",
        "filter.price": "Price",
        "filter.bedrooms": "Bedrooms",
        "filter.type": "Type",
        "filter.apply": "Apply",
        "filter.reset": "Reset",
        "listing.beds": "bed",
        "listing.baths": "bath",
        "listing.area": "m²",
        "listing.price": "Price",
        "listing.daysOnMarket": "days on market",
        "listing.source": "Source",
        "listing.openSource": "Open original listing",
        "listing.save": "Save",
        "listing.saved": "Saved ✓",
        "listing.compare": "Compare",
        "listing.share": "Share",
        "listing.copyLink": "Copy link",
        "listing.linkCopied": "Link copied",
        "saved.title": "Your saved properties",
        "saved.empty": "You haven't saved any properties yet. Click ★ on any listing.",
        "saved.clear": "Clear all",
        "compare.title": "Compare properties",
        "compare.empty": "Choose up to 4 properties and click \"Compare\" to see them side by side.",
        "compare.table.price": "Price",
        "compare.table.area": "Area",
        "compare.table.beds": "Bedrooms",
        "compare.table.baths": "Bathrooms",
        "compare.table.city": "City",
        "compare.table.source": "Source",
        "compare.table.pricePerSqm": "Price / m²",
        "compare.table.title": "Property",
        "common.loading": "Loading…",
        "common.error": "Something failed",
        "common.retry": "Retry",
        "common.cancel": "Cancel",
        "common.share": "Share",
        "common.close": "Close",
        "common.menu": "Menu",
        "common.language": "Language",
        "common.lastUpdated": "Last updated",
        "common.privacy": "Privacy",
        "common.terms": "Terms",
        "common.license": "MIT code · CC0 data",
        "onboarding.step1.title": "This is the national map",
        "onboarding.step1.body": "5,784 properties across Paraguay, in one view.",
        "onboarding.step2.title": "Click any red dot",
        "onboarding.step2.body": "To see price, area, bedrooms, and the original listing.",
        "onboarding.step3.title": "Filter by city or source",
        "onboarding.step3.body": "In the right-hand panel. Updates live.",
        "onboarding.step4.title": "Save or compare",
        "onboarding.step4.body": "Tap ★ to save, or use \"Compare\" to see two side by side.",
        "onboarding.step5.title": "All set",
        "onboarding.step5.body": "All code is MIT, data is CC0. Use, copy, improve.",
        "onboarding.skip": "Skip",
        "onboarding.next": "Next",
        "onboarding.done": "Start",
        "feedback.title": "Feedback",
        "feedback.placeholder": "What would you change?",
        "feedback.send": "Send",
        "feedback.thanks": "Thank you!",
        "feedback.reportData": "Report incorrect data",
        "cookieBanner.text": "We use cookies to remember language and saved properties. Nothing else is tracked.",
        "cookieBanner.accept": "Accept",
        "cookieBanner.decline": "Necessary only",
    },
    "pt": {
        "site.title": "Paraguay Geodata — Visualizador nacional",
        "site.tagline": "5.784 imóveis · 16 cidades · Cobertura nacional",
        "nav.home": "Nacional",
        "nav.data": "Dados",
        "nav.viewer": "Visualizador por tile",
        "nav.docs": "Docs",
        "nav.github": "GitHub",
        "nav.useCases": "Casos de uso",
        "nav.compare": "Comparar",
        "nav.faq": "FAQ",
        "nav.contact": "Contato",
        "nav.changelog": "Mudanças",
        "home.title": "5.784 imóveis no Paraguai",
        "home.subtitle": "Mapa interativo de imóveis à venda e aluguel — construído com dados públicos abertos.",
        "home.search": "Buscar endereço, cidade ou bairro…",
        "home.viewer": "Visualizador por tile",
        "home.compare": "Comparar imóveis",
        "home.useCases": "Para quem é isto",
        "home.investors.title": "Para investidores",
        "home.investors.body": "5.784 anúncios · 3 fontes (InfoCasas, TuLugar, Asunción.estate) · USD + PYG em cada listing.",
        "home.architects.title": "Para arquitetos",
        "home.architects.body": "Camadas urbanas + climáticas + relevo. Exporte GeoJSON ou DXF para QGIS / AutoCAD.",
        "home.farmers.title": "Para agrônomos",
        "home.farmers.body": "INBIO safra + NASA POWER clima + GBIF biodiversidade por departamento.",
        "home.government.title": "Para governo",
        "home.government.body": "Cadastro, tributação, risco climático — dados abertos para planejar.",
        "home.cta.investors": "Ver 5.784 imóveis →",
        "home.cta.architects": "Abrir camadas urbanas →",
        "home.cta.farmers": "Abrir camadas agrícolas →",
        "home.cta.government": "Abrir dados públicos →",
        "home.metrics.listings": "Imóveis listados",
        "home.metrics.cities": "Cidades cobertas",
        "home.metrics.sources": "Fontes de dados",
        "home.metrics.freshness": "Idade mediana dos dados",
        "tab.properties": "Imóveis",
        "tab.climate": "Clima",
        "tab.construction": "Construção",
        "tab.insights": "Insights",
        "tab.architect": "Arquiteto",
        "tab.export": "Exportar",
        "filter.city": "Cidade",
        "filter.source": "Fonte",
        "filter.price": "Preço",
        "filter.bedrooms": "Quartos",
        "filter.type": "Tipo",
        "filter.apply": "Aplicar",
        "filter.reset": "Limpar",
        "listing.beds": "quarto",
        "listing.baths": "banheiro",
        "listing.area": "m²",
        "listing.price": "Preço",
        "listing.daysOnMarket": "dias no mercado",
        "listing.source": "Fonte",
        "listing.openSource": "Ver anúncio original",
        "listing.save": "Salvar",
        "listing.saved": "Salvo ✓",
        "listing.compare": "Comparar",
        "listing.share": "Compartilhar",
        "listing.copyLink": "Copiar link",
        "listing.linkCopied": "Link copiado",
        "saved.title": "Seus imóveis salvos",
        "saved.empty": "Você ainda não salvou imóveis. Clique em ★ em qualquer listing.",
        "saved.clear": "Limpar tudo",
        "compare.title": "Comparar imóveis",
        "compare.empty": "Escolha até 4 imóveis e clique em \"Comparar\" para vê-los lado a lado.",
        "compare.table.price": "Preço",
        "compare.table.area": "Área",
        "compare.table.beds": "Quartos",
        "compare.table.baths": "Banheiros",
        "compare.table.city": "Cidade",
        "compare.table.source": "Fonte",
        "compare.table.pricePerSqm": "Preço / m²",
        "compare.table.title": "Imóvel",
        "common.loading": "Carregando…",
        "common.error": "Algo falhou",
        "common.retry": "Tentar de novo",
        "common.cancel": "Cancelar",
        "common.share": "Compartilhar",
        "common.close": "Fechar",
        "common.menu": "Menu",
        "common.language": "Idioma",
        "common.lastUpdated": "Última atualização",
        "common.privacy": "Privacidade",
        "common.terms": "Termos",
        "common.license": "Código MIT · Dados CC0",
        "onboarding.step1.title": "Este é o mapa nacional",
        "onboarding.step1.body": "5.784 imóveis no Paraguai, em uma vista.",
        "onboarding.step2.title": "Clique em qualquer ponto vermelho",
        "onboarding.step2.body": "Para ver preço, área, quartos e o anúncio original.",
        "onboarding.step3.title": "Filtre por cidade ou fonte",
        "onboarding.step3.body": "No painel à direita. Atualiza ao vivo.",
        "onboarding.step4.title": "Salve ou compare",
        "onboarding.step4.body": "Toque em ★ para salvar, ou use \"Comparar\" para ver dois lado a lado.",
        "onboarding.step5.title": "Tudo pronto",
        "onboarding.step5.body": "Todo o código é MIT, dados são CC0. Use, copie, melhore.",
        "onboarding.skip": "Pular",
        "onboarding.next": "Próximo",
        "onboarding.done": "Começar",
        "feedback.title": "Feedback",
        "feedback.placeholder": "O que você mudaria?",
        "feedback.send": "Enviar",
        "feedback.thanks": "Obrigado!",
        "feedback.reportData": "Reportar dado incorreto",
        "cookieBanner.text": "Usamos cookies para lembrar idioma e imóveis salvos. Nada mais é rastreado.",
        "cookieBanner.accept": "Aceitar",
        "cookieBanner.decline": "Apenas necessários",
    },
    "gn": {
        "site.title": "Paraguay Geodata — Vista Nacional",
        "site.tagline": "5.784 óga · 16 táva · Tetã rembehape",
        "nav.home": "Tetã",
        "nav.data": "Mba'e",
        "nav.viewer": "Vista tile",
        "nav.docs": "Docs",
        "nav.github": "GitHub",
        "nav.useCases": "Oñemobyta hína",
        "nav.compare": "Oñemohasa",
        "nav.faq": "FAQ",
        "nav.contact": "Ñeñe'ẽ",
        "nav.changelog": "Ñemoambue",
        "home.title": "5.784 óga Paraguay-pe",
        "home.subtitle": "Mapa ojehecháva — ojeguerovia ha ojehepyme'ẽre — oñemobyta hína.",
        "home.search": "Heka kundaha, táva térã barrio…",
        "home.viewer": "Vista tile rehegua",
        "home.compare": "Emohasa óga",
        "home.useCases": "Máva-pe g̃uara hína ko",
        "home.investors.title": "Oñemobyta hína",
        "home.investors.body": "5.784 ñemobyta · 3 fuente (InfoCasas, TuLugar, Asunción.estate) · USD + PYG óga rehegua.",
        "home.architects.title": "Arquitecto-kuérape g̃uara",
        "home.architects.body": "Tenda +气候 + relieve. Emboty GeoJSON térã DXF QGIS / AutoCAD-pe.",
        "home.farmers.title": "Agrónomo-kuérape g̃uara",
        "home.farmers.body": "INBIO + NASA POWER + GBIF departamento rupive.",
        "home.government.title": "Gobierno-pe g̃uara",
        "home.government.body": "Catastro, tributación,气候 riesgo — mba'e abierto planifica-pe g̃uara.",
        "home.cta.investors": "Ehecha 5.784 óga →",
        "home.cta.architects": "Ijurujá capa urbana →",
        "home.cta.farmers": "Ijurujá capa agricola →",
        "home.cta.government": "Ijurujá mba'e público →",
        "home.metrics.listings": "Óga oñemobyta",
        "home.metrics.cities": "Táva oñemobyta",
        "home.metrics.sources": "Mba'e fuente",
        "home.metrics.freshness": "Mba'e año mediokuéra",
        "tab.properties": "Óga",
        "tab.climate": "Ati气候",
        "tab.construction": "Ñemobyta",
        "tab.insights": "Mba'e",
        "tab.architect": "Arquitecto",
        "tab.export": "Emboty",
        "filter.city": "Táva",
        "filter.source": "Fuente",
        "filter.price": "Viru",
        "filter.bedrooms": "Kuatiarã",
        "filter.type": "Tipo",
        "filter.apply": "Oñemobyta",
        "filter.reset": "Mopotĩ",
        "listing.beds": "k",
        "listing.baths": "b",
        "listing.area": "m²",
        "listing.price": "Viru",
        "listing.daysOnMarket": "ára mercado-pe",
        "listing.source": "Fuente",
        "listing.openSource": "Ehecha ñemobyta hekoporã",
        "listing.save": "Ñongatu",
        "listing.saved": "Oñongatu ✓",
        "listing.compare": "Oñemohasa",
        "listing.share": "Mbohare",
        "listing.copyLink": "Ehai kopia",
        "listing.linkCopied": "Oñekopia",
        "saved.title": "Nde óga oñongatu",
        "saved.empty": "Ndo'úi mba'eve oñongatu. Eñotĩ ★ ohape listing-pe.",
        "saved.clear": "Mopotĩ opaite",
        "compare.title": "Emohasa óga",
        "compare.empty": "Eiporavo 4 óga peve ha eñotĩ \"Comparar\" oñemohenda asy hendáicha.",
        "compare.table.price": "Viru",
        "compare.table.area": "Supy",
        "compare.table.beds": "Kuatiarã",
        "compare.table.baths": "Baño",
        "compare.table.city": "Táva",
        "compare.table.source": "Fuente",
        "compare.table.pricePerSqm": "Viru / m²",
        "compare.table.title": "Óga",
        "common.loading": "Oñecargando…",
        "common.error": "Mba'e oñefalla",
        "common.retry": "Eñeha'ã jey",
        "common.cancel": "Eheja",
        "common.share": "Mbohare",
        "common.close": "Mbogue",
        "common.menu": "Porupy",
        "common.language": "Ñeñe'ẽ",
        "common.lastUpdated": "Umi ñemoambue paha",
        "common.privacy": "Ñemihápe",
        "common.terms": "Término",
        "common.license": "Código MIT · Mba'e CC0",
        "onboarding.step1.title": "Ko mapa tetã",
        "onboarding.step1.body": "5.784 óga Paraguay-pe, vista peteĩhára.",
        "onboarding.step2.title": "Eñotĩ punto pytã",
        "onboarding.step2.body": "Ehecha hag̃ua viru, supy, kuatiarã ha ñemobyta hekoporã.",
        "onboarding.step3.title": "Embopyahu táva térã fuente rupive",
        "onboarding.step3.body": "Panel derecho-pe. Oñemoactualisa vivo.",
        "onboarding.step4.title": "Eñongatu térã emohasa",
        "onboarding.step4.body": "Eñotĩ ★ ñongatu hag̃ua, térã \"Comparar\" oñemohenda asy hendáicha.",
        "onboarding.step5.title": "Opáma",
        "onboarding.step5.body": "Código oiko MIT-pe, mba'e CC0. Eiporu, ejopy, ejapoporã.",
        "onboarding.skip": "Javy",
        "onboarding.next": "Jepyso",
        "onboarding.done": "Eñepyrũ",
        "feedback.title": "Ñeñe'ẽ",
        "feedback.placeholder": "Mba'épa emoambuéta?",
        "feedback.send": "Mondo",
        "feedback.thanks": "Aguyje!",
        "feedback.reportData": "Eñeñói mba'e oiko'ỹva",
        "cookieBanner.text": "Eiporu ñeñe'ẽ ha óga oñongatu ñongatu hag̃ua. Ambue mba'e ndojuhúi.",
        "cookieBanner.accept": "Acepta",
        "cookieBanner.decline": "Tekotevẽha año",
    },
};

// Server-side helper: returns the right string for a given key + URL param
function getI18n(key, lang) {
    lang = lang || 'es';
    return (i18n[lang] && i18n[lang][key]) || (i18n['es'] && i18n['es'][key]) || key;
}

// Apply all data-i18n tags in document order
function applyI18n(lang) {
    lang = lang || getLang();
    document.documentElement.lang = lang;
    // text content
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
        var key = el.getAttribute('data-i18n');
        var v = (i18n[lang] && i18n[lang][key]) || (i18n['es'] && i18n['es'][key]);
        if (v !== undefined) el.textContent = v;
    });
    // attribute values
    document.querySelectorAll('[data-i18n-attr]').forEach(function (el) {
        var attr = el.getAttribute('data-i18n-attr');
        var key = el.getAttribute('data-i18n');
        var v = (i18n[lang] && i18n[lang][key]) || (i18n['es'] && i18n['es'][key]);
        if (v !== undefined && attr) el.setAttribute(attr, v);
    });
    // title (document.title)
    var titleKey = document.querySelector('meta[name="i18n-title"]');
    if (titleKey) {
        var k = titleKey.getAttribute('content');
        var v = (i18n[lang] && i18n[lang][k]) || (i18n['es'] && i18n['es'][k]);
        if (v) document.title = v;
    }
    // Save back
    try { localStorage.setItem('paraguay-geodata.lang', lang); } catch (e) {}
}

// Detect preferred language: URL ?lang=, localStorage, navigator, fallback to es
function getLang() {
    try {
        var qs = new URLSearchParams(window.location.search).get('lang');
        if (qs && i18n[qs]) return qs;
        var stored = localStorage.getItem('paraguay-geodata.lang');
        if (stored && i18n[stored]) return stored;
        var nav = (navigator.language || 'es').slice(0, 2).toLowerCase();
        if (i18n[nav]) return nav;
    } catch (e) {}
    return 'es';
}

// Build a language switcher <select> and append to the given parent.
// Accepts either a CSS selector string OR a DOM Element.
function buildLangSwitcher(parentSel) {
    var parent = (parentSel && parentSel.nodeType === 1)
        ? parentSel
        : document.querySelector(parentSel);
    if (!parent) return;
    var sel = document.createElement('select');
    sel.id = 'lang-switcher';
    sel.setAttribute('aria-label', getI18n('common.language', getLang()));
    // Style with individual properties (avoids CSS var parse errors in style.cssText)
    sel.style.background = 'var(--bg-elev)';
    sel.style.color = 'var(--fg)';
    sel.style.border = '1px solid var(--line)';
    sel.style.padding = '4px 8px';
    sel.style.borderRadius = '4px';
    sel.style.fontSize = '12px';
    sel.style.cursor = 'pointer';
    sel.style.marginLeft = '8px';
    ['es', 'en', 'pt', 'gn'].forEach(function (l) {
        var opt = document.createElement('option');
        opt.value = l;
        var names = { es: 'Español', en: 'English', pt: 'Português', gn: 'Avañe\'ẽ' };
        opt.textContent = names[l] || l;
        if (l === getLang()) opt.selected = true;
        sel.appendChild(opt);
    });
    sel.addEventListener('change', function () {
        applyI18n(sel.value);
        document.dispatchEvent(new CustomEvent('i18n-changed', { detail: { lang: sel.value } }));
    });
    parent.appendChild(sel);
}

// Init on DOMContentLoaded (auto-runs on every page that loads this script)
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { applyI18n(getLang()); });
    } else {
        applyI18n(getLang());
    }
}

// Export to global namespace (avoid module bundlers so this works inline + script tag)
if (typeof window !== 'undefined') {
    window.PY_I18N = { i18n: i18n, getLang: getLang, applyI18n: applyI18n, buildLangSwitcher: buildLangSwitcher };
}