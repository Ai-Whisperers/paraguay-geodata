// Paraguay Geodata — Data widgets (BCP, INBIO, climate, insights, fair-price, yield, mortgage, affordability, market signals, charts)
// Shared by index.html (sidebar widgets) and datos.html (standalone data page).
// Auto-generated extract from index.html — do not edit here, edit the source and re-extract.

// ========== BCP WIDGET ==========
async function loadBCP() {
    if (!document.getElementById('bcpWidget')) return;

    try {
        const r = await fetch('./data/bcp_snapshot.json');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const d = await r.json();
        const M = d.monetary, Mc = d.macro, B = d.banking_health, R = d.rate_types;
        const widget = document.getElementById('bcpWidget');
        widget.innerHTML = `
            <h3>Banco Central del Paraguay (Feb 2026)</h3>
            <div class="row"><span class="k">TPM</span><span class="v pos">${M.tpm_pct}%</span></div>
            <div class="row"><span class="k">Inflación YoY</span><span class="v ${M.inflacion_interanual_pct < M.meta_inflacion_pct ? 'pos' : 'warn'}">${M.inflacion_interanual_pct}% (meta ${M.meta_inflacion_pct}%)</span></div>
            <div class="row"><span class="k">PIB 2025</span><span class="v pos">+${Mc.pib_2025_growth_pct}%</span></div>
            <div class="row"><span class="k">PIB 2026 (proj.)</span><span class="v">${Mc.pib_2026_proyeccion_pct}%</span></div>
            <div class="row"><span class="k">RIN</span><span class="v">$${Mc.rin_usd_million.toLocaleString()}M</span></div>
            <div class="row"><span class="k">Morosidad bancos</span><span class="v ${B.morosidad_bancos_pct < 3 ? 'pos' : 'warn'}">${B.morosidad_bancos_pct}%</span></div>
            <div class="row"><span class="k">Morosidad financ.</span><span class="v ${B.morosidad_financieras_pct < 3 ? 'pos' : 'neg'}">${B.morosidad_financieras_pct}%</span></div>
            <div class="row"><span class="k">Tasa activa ME</span><span class="v">${R.activa_me_bancos_pct}%</span></div>
            <div class="row"><span class="k">Tasa pasiva ME</span><span class="v">${R.pasiva_me_bancos_pct}%</span></div>
            <div class="row"><span class="k">Remesas 2008-2026</span><span class="v warn">$${d.remesas.total_2008_2026_million_usd.toLocaleString()}M</span></div>
        `;
        document.getElementById('bcpBadge').textContent = `BCP: TPM ${M.tpm_pct}% · PIB +${Mc.pib_2025_growth_pct}%`;
        if (typeof updateLayerCount === 'function') updateLayerCount('bcp_overlay', 'widget-only');
    } catch (e) {
        console.error('BCP load failed:', e);
        document.getElementById('bcpWidget').innerHTML = `<h3>BCP load failed</h3><div style="color:var(--err)">${e.message}</div>`;
    }
}

// ========== INBIO WIDGET ==========
async function loadINBIOWidget() {
    if (!document.getElementById('inbioWidget')) return;

    try {
        const r = await fetch('./data/inbio_zafra_2025_2026.json');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const d = await r.json();
        const fmt = (n) => n == null ? '—' : `${(n/1000).toFixed(0)}K ha`;
        const delta = (cur, prev) => {
            if (cur == null || prev == null) return '—';
            const d = cur - prev;
            const pct = (d / prev * 100).toFixed(1);
            return `${d > 0 ? '+' : ''}${d.toLocaleString()} ha (${d > 0 ? '+' : ''}${pct}%)`;
        };
        const T = d.totals_national;
        const w = document.getElementById('inbioWidget');
        w.innerHTML = `
            <h3>${d.zafra} (satellite ${d.published})</h3>
            <div class="row"><span class="k">Soja total</span><span class="v" style="color:#c084fc">${fmt(T.soja.area_ha_2025_2026)}</span></div>
            <div class="row"><span class="k">  vs 24/25</span><span class="v ${T.soja.delta_ha >= 0 ? '' : 'warn'}">${fmt(T.soja.delta_ha)} (${T.soja.delta_pct > 0 ? '+' : ''}${T.soja.delta_pct.toFixed(1)}%)</span></div>
            <div class="row"><span class="k">Arroz total</span><span class="v">${fmt(T.arroz.area_ha_2025_2026)}</span></div>
            <div class="row"><span class="k">  vs 24/25</span><span class="v warn">${fmt(T.arroz.delta_ha)} (${T.arroz.delta_pct.toFixed(1)}%)</span></div>
            <div class="row"><span class="k">Maíz zafriña</span><span class="v">${fmt(T.maiz_zaf.area_ha_2025_2026)}</span></div>
            <div class="row"><span class="k">  vs 24/25</span><span class="v warn">${fmt(T.maiz_zaf.delta_ha)} (${T.maiz_zaf.delta_pct.toFixed(1)}%)</span></div>
            <div class="insight">⚠️ Arroz down -22%, Maíz zafriña down -29% — south PY (Itapúa, Misiones) drought signal</div>
        `;
    } catch (e) {
        console.error('INBIO widget failed:', e);
        document.getElementById('inbioWidget').innerHTML = `<h3>INBIO load failed</h3><div style="color:var(--err)">${e.message}</div>`;
    }
}

// ========== INSIGHTS PANEL ==========
async function loadInsights() {
    if (!document.getElementById('insightsWidget')) return;

    try {
        const [inbio, bcp, nasa, propsRes] = await Promise.all([
            fetch('./data/inbio_zafra_2025_2026.json').then(r => r.ok ? r.json() : null),
            fetch('./data/bcp_snapshot.json').then(r => r.ok ? r.json() : null),
            fetch('./data/nasa_power_asuncion.json').then(r => r.ok ? r.json() : null),
            fetch('./data/properties_latest.geojson').then(r => r.ok ? r.json() : null),
        ]);

        // 1. Drought signal: where INBIO shows the biggest losses
        let droughtLine = 'No significant crop-loss signal in 2025-2026 zafra.';
        if (inbio && inbio.totals_national) {
            const T = inbio.totals_national;
            const losses = [];
            if (T.arroz.delta_pct < -10) losses.push(`arroz ${T.arroz.delta_pct.toFixed(0)}%`);
            if (T.maiz_zaf.delta_pct < -10) losses.push(`maíz zafriña ${T.maiz_zaf.delta_pct.toFixed(0)}%`);
            if (T.soja.delta_pct < -5) losses.push(`soja ${T.soja.delta_pct.toFixed(0)}%`);
            if (losses.length) {
                const worst = (inbio.rows_by_dept || []).reduce((w, r) => {
                    const d = (r.arroz_25_26 || 0) - (r.arroz_24_25 || 0);
                    return d < w.d ? { d, name: r.depto } : w;
                }, { d: 0, name: '' });
                droughtLine = `Crop loss signal: ${losses.join(', ')} nationally. Worst arroz drop in ${worst.name || 'Misiones'} (−${Math.abs(Math.round(worst.d / 1000))}K ha).`;
            } else if (losses.length === 0 && T.soja.delta_pct > 0) {
                droughtLine = `No drought signal — soja +${T.soja.delta_pct.toFixed(1)}% nationally, arroz stable.`;
            }
        }
        document.getElementById('insightDrought').textContent = droughtLine;

        // 2. Soja expansion
        let sojaLine = 'Soja data not loaded.';
        if (inbio && inbio.totals_national) {
            const T = inbio.totals_national;
            const expanded = (inbio.rows_by_dept || []).filter(r => (r.soja_25_26 || 0) > (r.soja_24_25 || 0))
                .sort((a, b) => (b.soja_25_26 - b.soja_24_25) - (a.soja_25_26 - a.soja_24_25))
                .slice(0, 3);
            const expandedStr = expanded.map(r => `${r.depto} +${((r.soja_25_26 - r.soja_24_25) / 1000).toFixed(0)}K`).join(', ');
            sojaLine = `Soja zafra 2025-26: ${(T.soja.area_ha_2025_2026 / 1e6).toFixed(2)}M ha (+${T.soja.delta_pct.toFixed(1)}% vs 24/25). Top expansion: ${expandedStr || 'n/a'}.`;
        }
        document.getElementById('insightSoja').textContent = sojaLine;

        // 3. Property prices (from already-loaded properties)
        let pricesLine = 'Property data not loaded yet.';
        if (propsRes && propsRes.features && propsRes.features.length) {
            const usds = propsRes.features.map(f => f.properties.price_usd).filter(x => x > 0);
            if (usds.length) {
                usds.sort((a, b) => a - b);
                const median = usds[Math.floor(usds.length / 2)];
                const min = usds[0], max = usds[usds.length - 1];
                const perHa = propsRes.features.map(f => f.properties['$/ha']).filter(x => x > 0);
                perHa.sort((a, b) => a - b);
                const medPerHa = perHa.length ? perHa[Math.floor(perHa.length / 2)] : 0;
                pricesLine = `${usds.length} priced listings: median $${Math.round(median).toLocaleString()} USD (range $${Math.round(min).toLocaleString()}–$${Math.round(max).toLocaleString()}). Median $${Math.round(medPerHa).toLocaleString()}/ha.`;
            }
        }
        document.getElementById('insightPrices').textContent = pricesLine;

        // 4. Macro snapshot
        let macroLine = 'BCP data not loaded.';
        if (bcp) {
            const m = bcp.macro, mon = bcp.monetary;
            macroLine = `PY 2025: PIB +${m.pib_2025_growth_pct}%, TPM ${mon.tpm_pct}%, inflación YoY ${mon.inflacion_interanual_pct}% (meta ${mon.meta_inflacion_pct}%), RIN $${m.rin_usd_million.toLocaleString()}M.`;
        }
        document.getElementById('insightMacros').textContent = macroLine;

        // 5. Listing density: where are listings concentrated?
        let densityLine = 'Property distribution not yet computed.';
        if (propsRes && propsRes.features.length) {
            const byDepto = {};
            propsRes.features.forEach(f => {
                const d = f.properties.depto || 'Unknown';
                byDepto[d] = (byDepto[d] || 0) + 1;
            });
            const sorted = Object.entries(byDepto).sort((a, b) => b[1] - a[1]);
            if (sorted.length) {
                const top = sorted[0];
                const topPct = (top[1] / propsRes.features.length * 100).toFixed(1);
                densityLine = `Top listing deptos: ${sorted.slice(0, 3).map(([k, v]) => `${k} (${v})`).join(', ')}. ${top[0]} = ${topPct}% of all listings.`;
            }
        }
        document.getElementById('insightDensity').textContent = densityLine;
    } catch (e) {
        console.error('Insights failed:', e);
    }
}

// ========== NASA POWER WIDGET ==========
async function loadClimate() {
    if (!document.getElementById('climateWidget')) return;

    try {
        const r = await fetch('./data/nasa_power_asuncion.json');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const d = await r.json();
        const S = d.summary_2024;
        const widget = document.getElementById('climateWidget');
        widget.innerHTML = `
            <h3>${d.point.label} (2024)</h3>
            <div class="row"><span class="k">Avg temp</span><span class="v">${S.T2M.avg}°C</span></div>
            <div class="row"><span class="k">Min / Max</span><span class="v">${S.T2M.min}°C / ${S.T2M.max}°C</span></div>
            <div class="row"><span class="k">Avg precip/day</span><span class="v">${S.PRECTOTCORR.avg} mm</span></div>
            <div class="row"><span class="k">Max precip/day</span><span class="v">${S.PRECTOTCORR.max} mm</span></div>
            <div class="row"><span class="k">Avg solar</span><span class="v">${S.ALLSKY_SFC_SW_DWN.avg} MJ/m²</span></div>
        `;
        if (typeof updateLayerCount === 'function') updateLayerCount('nasa_power_overlay', 'query-based');
    } catch (e) {
        console.error('Climate load failed:', e);
        document.getElementById('climateWidget').innerHTML = `<h3>Climate load failed</h3><div style="color:var(--err)">${e.message}</div>`;
    }
}

// ========== FAIR-PRICE MODEL (ML) ==========
// Use `var` so this declaration doesn't conflict with `var fairPriceModel`
// in the inline scripts of pages that load widgets.js (e.g., index.html).
var fairPriceModel = null;
async function loadFairPriceModel() {
    if (!document.getElementById('fairPriceWidget')) return;

    try {
        const r = await fetch('./data/ml/fair_price_model.json');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        fairPriceModel = await r.json();
        const w = document.getElementById('fairPriceWidget');
        const stats = fairPriceModel.global_stats;
        const nDeptoModels = Object.keys(fairPriceModel.depto_models).length;
        w.innerHTML = `
            <div>Trained on <strong>${fairPriceModel.training_samples.toLocaleString()}</strong> properties</div>
            <div>Median $/ha: <strong>$${Math.round(stats.median_per_ha).toLocaleString()}</strong></div>
            <div>P25–P75: <span style="color:var(--fg-dim)">$${Math.round(stats.p25_per_ha).toLocaleString()} – $${Math.round(stats.p75_per_ha).toLocaleString()}</span></div>
            <div style="margin-top:4px;">Deptos modeled: <strong>${nDeptoModels}</strong> of 18</div>
            <div style="color:var(--fg-dim); font-size:10px; margin-top:4px;">Click any property → fair-price score shown in popup. 🔥 = overpriced, 💰 = deal.</div>
        `;
    } catch (e) {
        document.getElementById('fairPriceWidget').innerHTML = '<div style="color:var(--err)">⚠ Model unavailable</div>';
        console.error('Fair-price model load failed:', e);
    }
}

function fairPricePredict(p, lon, lat) {
    if (!fairPriceModel) return null;
    const depto = p.state_province || 'Unknown';
    const model = fairPriceModel.depto_models[depto] || fairPriceModel.global_fallback;
    if (!model || !p.area_ha) return null;
    const log_area = Math.log10(Math.max(0.01, p.area_ha));
    const log_pred = model.intercept +
        model.coefs.log_area * log_area +
        model.coefs.lat * lat +
        model.coefs.lon * lon +
        model.coefs.beds * (p.bedrooms || 0);
    return Math.pow(10, log_pred) * p.area_ha;  // predicted total price
}

function fairPriceScore(p, lon, lat) {
    if (!fairPriceModel || !p.price_usd) return null;
    const pred = fairPricePredict(p, lon, lat);
    if (!pred) return null;
    const ratio = p.price_usd / pred;
    let flag, color, label;
    if (ratio < 0.5) { flag = '💰 DEAL'; color = 'var(--accent)'; label = `${Math.round((1 - ratio) * 100)}% below market`; }
    else if (ratio < 0.8) { flag = '✓ Cheap'; color = 'var(--accent)'; label = `${Math.round((1 - ratio) * 100)}% below market`; }
    else if (ratio < 1.2) { flag = '✓ Fair'; color = 'var(--fg)'; label = 'market priced'; }
    else if (ratio < 2.0) { flag = '⚠ Premium'; color = 'var(--warn)'; label = `${Math.round((ratio - 1) * 100)}% above market`; }
    else { flag = '🔥 Overpriced'; color = 'var(--err)'; label = `${Math.round((ratio - 1) * 100)}% above market`; }
    return { ratio, flag, color, label, predicted: pred };
}

// ========== YIELD CALCULATOR ==========
function calcYield() {
    if (!document.getElementById('yieldPrice')) return;
    const price = parseFloat(document.getElementById('yieldPrice').value) || 0;
    const rent = parseFloat(document.getElementById('yieldRent').value) || 0;
    const costs = parseFloat(document.getElementById('yieldCosts').value) || 0;
    const annualRent = rent * 12;
    const netYield = ((annualRent - costs) / price) * 100;
    const grossYield = (annualRent / price) * 100;
    const paybackYears = annualRent > 0 ? price / annualRent : Infinity;
    const color = netYield < 3 ? 'var(--err)' : netYield < 6 ? 'var(--warn)' : 'var(--accent)';
    document.getElementById('yieldResult').innerHTML = `
        <div>Gross yield: <strong>${grossYield.toFixed(2)}%</strong></div>
        <div>Net yield: <strong style="color:${color}">${netYield.toFixed(2)}%</strong></div>
        <div>Annual rent: <span style="color:var(--fg-dim)">$${annualRent.toLocaleString()}</span></div>
        <div>Annual costs: <span style="color:var(--fg-dim)">$${costs.toLocaleString()}</span></div>
        <div style="margin-top:4px; font-size:10px; color:var(--fg-dim)">Payback: ${paybackYears < 100 ? paybackYears.toFixed(1) + ' years' : '—'}</div>
    `;
}

// ========== MORTGAGE + AFFORDABILITY ==========
function computeMortgage() {
    if (!document.getElementById('mortValue')) return;
    const value = parseFloat(document.getElementById('mortValue').value) || 0;
    const downPct = parseFloat(document.getElementById('mortDownPct').value) || 0;
    const rate = parseFloat(document.getElementById('mortRate').value) || 0;
    const years = parseFloat(document.getElementById('mortTerm').value) || 0;

    if (!value || !rate || !years) {
        return document.getElementById('mortResult').innerHTML = '<div style="color:var(--fg-dim);">Enter values to compute</div>';
    }

    const downPayment = value * (downPct / 100);
    const loanAmount = value - downPayment;
    const monthlyRate = rate / 100 / 12;
    const numPayments = years * 12;

    let monthlyPayment;
    if (monthlyRate === 0) {
        monthlyPayment = loanAmount / numPayments;
    } else {
        const factor = Math.pow(1 + monthlyRate, numPayments);
        monthlyPayment = loanAmount * (monthlyRate * factor) / (factor - 1);
    }

    const totalPaid = monthlyPayment * numPayments;
    const totalInterest = totalPaid - loanAmount;
    const monthlyInsurance = loanAmount * 0.0003;  // ~0.36%/yr hazard insurance
    const monthlyTotal = monthlyPayment + monthlyInsurance;

    document.getElementById('mortResult').innerHTML = `
        <div style="font-weight:bold; color:var(--accent); margin-bottom:6px;">Monthly: $${monthlyTotal.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</div>
        <div style="display:flex; justify-content:space-between; gap:4px;"><span style="color:var(--fg-dim);">Principal+interest</span><span>$${monthlyPayment.toFixed(0)}</span></div>
        <div style="display:flex; justify-content:space-between; gap:4px;"><span style="color:var(--fg-dim);">Insurance est.</span><span>$${monthlyInsurance.toFixed(0)}</span></div>
        <div style="display:flex; justify-content:space-between; gap:4px;"><span style="color:var(--fg-dim);">Down payment</span><span>$${downPayment.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</span></div>
        <div style="display:flex; justify-content:space-between; gap:4px;"><span style="color:var(--fg-dim);">Loan amount</span><span>$${loanAmount.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</span></div>
        <div style="display:flex; justify-content:space-between; gap:4px;"><span style="color:var(--fg-dim);">Total interest</span><span style="color:var(--warn);">$${totalInterest.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</span></div>
        <div style="display:flex; justify-content:space-between; gap:4px;"><span style="color:var(--fg-dim);">Total paid</span><span>$${(totalPaid + downPayment).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</span></div>
    `;
}
window.computeMortgage = computeMortgage;

// ========== AFFORDABILITY CALCULATOR ==========
function computeAffordability() {
    if (!document.getElementById('affIncome')) return;
    const income = parseFloat(document.getElementById('affIncome').value) || 0;
    const debts = parseFloat(document.getElementById('affDebts').value) || 0;
    const pct = parseFloat(document.getElementById('affPct').value) || 0;

    if (!income) {
        return document.getElementById('affResult').innerHTML = '<div style="color:var(--fg-dim);">Enter values to compute</div>';
    }

    // Front-end ratio: monthly housing payment / income
    const maxHousingPayment = (income * (pct / 100)) - debts;
    // Assume 30y @ 10% interest
    const monthlyRate = 0.10 / 12;
    const numPayments = 360;
    const factor = Math.pow(1 + monthlyRate, numPayments);
    const maxLoan = maxHousingPayment * (factor - 1) / (monthlyRate * factor);
    // With 30% down
    const maxPrice = maxLoan / 0.7;

    // Back-end ratio: total debt / income
    const backEndRatio = ((maxHousingPayment + debts) / income) * 100;

    document.getElementById('affResult').innerHTML = `
        <div style="font-weight:bold; color:var(--accent); margin-bottom:6px;">Max property: $${maxPrice.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</div>
        <div style="display:flex; justify-content:space-between;"><span style="color:var(--fg-dim);">Max housing payment</span><span>$${maxHousingPayment.toFixed(0)}/mo</span></div>
        <div style="display:flex; justify-content:space-between;"><span style="color:var(--fg-dim);">Max loan (30y @ 10%)</span><span>$${maxLoan.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</span></div>
        <div style="display:flex; justify-content:space-between;"><span style="color:var(--fg-dim);">Front-end ratio</span><span>${pct}%</span></div>
        <div style="display:flex; justify-content:space-between;"><span style="color:var(--fg-dim);">Back-end ratio</span><span>${backEndRatio.toFixed(0)}%</span></div>
        ${backEndRatio > 36 ? '<div style="margin-top:4px; color:var(--warn);">⚠ Back-end ratio >36% — bank may reject</div>' : ''}
    `;
}
window.computeAffordability = computeAffordability;


// ========== MARKET SIGNALS (renders into #marketSignals) ==========
function renderMarketSignals(features) {
    const signals = document.getElementById('marketSignals');
    if (!signals) return;
    const buckets = {
        total: 0, byType: {}, byDepto: {}, byListing: { sale: 0, rent: 0, short_rent: 0 },
        priceUsdSum: 0, priceUsdCount: 0, areaSum: 0, areaCount: 0,
        bedsTotal: 0, bedsCount: 0, withImages: 0, dateBuckets: {},
    };
    const thisMonth = new Date().toISOString().substring(0, 7);
    for (const f of features) {
        const p = f.properties || {};
        buckets.total++;
        const t = p.property_type || 'unknown';
        buckets.byType[t] = (buckets.byType[t] || 0) + 1;
        const d = p.state_province || 'Unknown';
        buckets.byDepto[d] = (buckets.byDepto[d] || 0) + 1;
        const lt = p.listing_type || 'sale';
        buckets.byListing[lt] = (buckets.byListing[lt] || 0) + 1;
        if (p.price_usd && p.price_usd > 0) {
            buckets.priceUsdSum += p.price_usd;
            buckets.priceUsdCount++;
        }
        if (p.area_ha && p.area_ha > 0) { buckets.areaSum += p.area_ha; buckets.areaCount++; }
        if (p.bedrooms) { buckets.bedsTotal += p.bedrooms; buckets.bedsCount++; }
        if (p.images && p.images.length) buckets.withImages++;
        const dt = (p.scraped_at_utc || '').substring(0, 7);
        if (dt) buckets.dateBuckets[dt] = (buckets.dateBuckets[dt] || 0) + 1;
    }
    const median = arr => { const s = arr.sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : 0; };
    const prices = features.map(f => f.properties.price_usd).filter(x => x > 0);
    const areas = features.map(f => f.properties.area_ha).filter(x => x > 0);
    const beds = features.map(f => f.properties.bedrooms).filter(x => x > 0);
    const medianPrice = median(prices.slice());
    const medianArea = median(areas.slice());
    const medianBeds = median(beds.slice());
    const thisMonthCount = buckets.dateBuckets[thisMonth] || 0;
    const lastMonth = new Date(Date.now() - 30 * 86400000).toISOString().substring(0, 7);
    const lastMonthCount = buckets.dateBuckets[lastMonth] || 0;
    const supplyChange = lastMonthCount > 0 ? ((thisMonthCount - lastMonthCount) / lastMonthCount * 100) : 0;
    const topDeptos = Object.entries(buckets.byDepto).sort((a, b) => b[1] - a[1]).slice(0, 3);
    const topTypes = Object.entries(buckets.byType).sort((a, b) => b[1] - a[1]).slice(0, 4);
    const ratio = buckets.byListing.rent / Math.max(1, buckets.byListing.sale);
    const ratioText = ratio < 0.1 ? 'rent/sale ratio very low' : ratio < 0.2 ? 'rent/sale ratio low' : ratio < 0.5 ? 'rent/sale ratio moderate' : 'rent/sale ratio high (rental market)';
    signals.innerHTML = `
        <div><strong>${buckets.total.toLocaleString()}</strong> listings indexed <span style="color:var(--fg-dim)">(${buckets.withImages.toLocaleString()} with photos)</span></div>
        <div>Median price: <strong>$${medianPrice.toLocaleString()}</strong> USD <span style="color:var(--fg-dim)">(${buckets.priceUsdCount.toLocaleString()} priced)</span></div>
        <div>Median area: <strong>${medianArea.toFixed(2)} ha</strong> ${buckets.areaCount > 0 ? `<span style="color:var(--fg-dim)">(${(buckets.areaSum / buckets.areaCount).toFixed(2)} avg)</span>` : ''}</div>
        <div>Median beds: <strong>${medianBeds}</strong> ${buckets.bedsCount > 0 ? `<span style="color:var(--fg-dim)">(${(buckets.bedsTotal / buckets.bedsCount).toFixed(1)} avg)</span>` : ''}</div>
        <div>Top deptos: ${topDeptos.map(([k, v]) => `<span style="color:var(--accent)">${k}</span> ${v}`).join(' · ')}</div>
        <div>Top types: ${topTypes.map(([k, v]) => `${k} ${v}`).join(' · ')}</div>
        <div>${buckets.byListing.sale.toLocaleString()} sale · ${buckets.byListing.rent.toLocaleString()} rent · ${buckets.byListing.short_rent || 0} short</div>
        <div style="color:${ratio < 0.1 ? 'var(--err)' : ratio < 0.2 ? 'var(--warn)' : 'var(--accent)'}">${ratioText}: ${(ratio * 100).toFixed(1)}%</div>
        <div>This month: ${thisMonthCount} new ${lastMonthCount > 0 ? `<span style="color:${supplyChange >= 0 ? 'var(--accent)' : 'var(--err)'}">(${supplyChange >= 0 ? '+' : ''}${supplyChange.toFixed(0)}% vs last month)</span>` : ''}</div>
    `;
}

// ========== PROPERTY CHARTS (Chart.js) ==========
function renderPropertyCharts(features) {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.color = 'rgba(230, 234, 242, 0.7)';
    Chart.defaults.borderColor = 'rgba(31, 41, 68, 0.6)';
    Chart.defaults.font.size = 10;
    const chartBuckets = { byType: {}, byDepto: {}, priceByDepto: {} };
    for (const f of features) {
        const p = f.properties || {};
        const t = p.property_type || 'unknown';
        chartBuckets.byType[t] = (chartBuckets.byType[t] || 0) + 1;
        const d = p.state_province || 'Unknown';
        chartBuckets.byDepto[d] = (chartBuckets.byDepto[d] || 0) + 1;
        if (p['$/ha'] && p.state_province && p['$/ha'] > 0 && p['$/ha'] < 100_000_000) {
            if (!chartBuckets.priceByDepto[d]) chartBuckets.priceByDepto[d] = { sum: 0, count: 0 };
            chartBuckets.priceByDepto[d].sum += p['$/ha'];
            chartBuckets.priceByDepto[d].count++;
        }
    }
    // Property types doughnut
    const typeCanvas = document.getElementById('chartPropertyTypes');
    if (typeCanvas) {
        if (Chart.getChart(typeCanvas)) Chart.getChart(typeCanvas).destroy();
        new Chart(typeCanvas, {
            type: 'doughnut',
            data: { labels: Object.keys(chartBuckets.byType), datasets: [{ data: Object.values(chartBuckets.byType), backgroundColor: ['#2dd4bf','#60a5fa','#f59e0b','#a78bfa','#ef4444','#10b981','#8b94a8'] }] },
            options: { plugins: { legend: { position: 'right', labels: { boxWidth: 8 } } }, maintainAspectRatio: false }
        });
    }
    // Top 10 deptos bar
    const deptosArr = Object.entries(chartBuckets.byDepto).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const deptosCanvas = document.getElementById('chartDeptos');
    if (deptosCanvas) {
        if (Chart.getChart(deptosCanvas)) Chart.getChart(deptosCanvas).destroy();
        new Chart(deptosCanvas, {
            type: 'bar',
            data: { labels: deptosArr.map(d => d[0]), datasets: [{ label: 'listings', data: deptosArr.map(d => d[1]), backgroundColor: '#2dd4bf' }] },
            options: { indexAxis: 'y', plugins: { legend: { display: false } }, maintainAspectRatio: false, scales: { x: { grid: { color: 'rgba(31, 41, 68, 0.4)' } } } }
        });
    }
    // $/ha by depto
    const arr = Object.entries(chartBuckets.priceByDepto).map(([k, v]) => [k, Math.round(v.sum / v.count), v.count]).sort((a, b) => b[1] - a[1]).slice(0, 12);
    const canvas = document.getElementById('chartPriceByDepto');
    if (canvas) {
        if (Chart.getChart(canvas)) Chart.getChart(canvas).destroy();
        new Chart(canvas, {
            type: 'bar',
            data: { labels: arr.map(a => a[0]), datasets: [
                { label: 'avg $/ha', data: arr.map(a => a[1]), backgroundColor: '#2dd4bf', yAxisID: 'y' },
                { label: 'listings', data: arr.map(a => a[2]), backgroundColor: 'rgba(96, 165, 250, 0.5)', yAxisID: 'y1', type: 'line', tension: 0.3 },
            ] },
            options: {
                plugins: { legend: { labels: { boxWidth: 10 } } },
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + (v/1000).toFixed(0) + 'k' } }, y1: { position: 'right', beginAtZero: true, grid: { display: false } } },
            },
        });
    }
}

// ========== WIRE UP CALCULATOR INPUTS (safe to call multiple times) ==========
function wireCalculators() {
    ['mortValue', 'mortDownPct', 'mortRate', 'mortTerm'].forEach(id => {
        const el = document.getElementById(id);
        if (el && !el._wired) {
            el.addEventListener('input', computeMortgage);
            el._wired = true;
        }
    });
    ['affIncome', 'affDebts', 'affPct'].forEach(id => {
        const el = document.getElementById(id);
        if (el && !el._wired) {
            el.addEventListener('input', computeAffordability);
            el._wired = true;
        }
    });
    ['yieldPrice', 'yieldRent', 'yieldCosts'].forEach(id => {
        const el = document.getElementById(id);
        if (el && !el._wired) {
            el.addEventListener('input', calcYield);
            el._wired = true;
        }
    });
}
