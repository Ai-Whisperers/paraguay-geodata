# Money Markets & Financial Data — Data Sources

The map should overlay **money flows** — interest rates, bank density, mortgage availability, remittances, capital market activity — because these directly affect property affordability, business viability, and economic vitality.

This is **the most under-served dimension** of geo data in Paraguay today. Most real-estate platforms show you a parcel; few show you whether the financing is available locally to buy it.

---

## 1. BCP — Banco Central del Paraguay (THE PRIMARY SOURCE)

| Field | Value |
|---|---|
| URL | https://www.bcp.gov.py/ |
| Auth | None for public data |
| License | Public info |
| Format | XLSX, PDF, JSON (varies per dataset) |
| Refresh | Monthly to daily (varies) |

### What we extract — the foundational 8 indicators

| Indicator | URL | Periodicity | Series from |
|---|---|---|---|
| **TPM** (Tasa de Política Monetaria) | Homepage hero | Daily | 2010+ |
| **Tasa Interbancaria** | Homepage hero | Daily | 2010+ |
| **IPC** (Índice de Precios al Consumidor) | /web/IPC | Monthly | 2008+ |
| **IPP** (Índice de Precios del Productor) | /web/IPP | Monthly | 2008+ |
| **IMAEP** (Indicador Mensual Actividad Económica) | /web/IMAEP | Monthly | 1994+ |
| **PIB** (Producto Interno Bruto) | /web/cuentas-nacionales | Quarterly + Annual | 1994+ |
| **RIN** (Reservas Internacionales Netas) | Homepage hero | Daily | 2000+ |
| **Tipo de cambio PYG/USD** | Multiple | Daily | 1990+ |

**Use**: per-department inflation proxy, FX for property price conversion, GDP per district (when disaggregated).

### 2. Indicadores Financieros (THE MORTGAGE / CREDIT GOLDMINE)

| Field | Value |
|---|---|
| URL | https://www.bcp.gov.py/en/resumen-mensual-tasas-de-interes |
| Auth | None |
| Format | XLSX (one per month, since 1991) |
| Refresh | Monthly (1-month lag) |

### What we extract — interest rate series

| Rate | What it is | Per series |
|---|---|---|
| **Tasa activa promedio ponderada bancos** (MN + ME) | What banks charge on loans | Moneda nacional + moneda extranjera |
| **Tasa pasiva promedio ponderada bancos** | What banks pay on deposits | Moneda nacional + moneda extranjera |
| **Tasa activa por tipo de crédito** | Commercial, consumer, mortgage, microcredit | 5+ sub-types |
| **Tasa de financieras** | Finance companies (separate from banks) | MN + ME |
| **Spread bancario** | Active − passive margin | Per-bank + aggregate |
| **Tasa usuraria** | Usury ceiling (interest rate cap) | MN + ME |
| **Morosidad bancaria** | % of non-performing loans | Aggregate + per-bank |
| **Adecuación patrimonial** | Capital adequacy ratio | Banks + financieras |

### Current snapshot (Feb 2026, from the extracted homepage)

| Indicator | Value |
|---|---|
| Inflación interanual | 2.3% (target 3.5%) |
| TPM | 5.50% |
| Tasa interbancaria | 5.36% |
| PIB 2025 | 6% growth |
| PIB 2026 proyectado | 4.2% |
| RIN | $11,611.4M |
| Adecuación patrimonial bancos | 16.43% (well above 10% Basel) |
| Adecuación patrimonial financieras | 15.34% |
| **Morosidad bancos** | **2.29%** |
| **Morosidad financieras** | **7.46%** |
| Tasa usuraria MN | 27.03% |
| Tasa usuraria ME | 11.14% |
| Tasa activa ME bancos | 8.07% (Jan 2026) |
| Tasa pasiva ME bancos | 3.89% (Jan 2026) |

**Use**:
- Per-property affordability: at 8% ME active rate + 30-year amortization, monthly payment on $100K = ~$734/mo
- Per-district risk: where financial inclusion is poor, properties need to be 20% cheaper to attract buyers
- Cross-reference with listings: "Is this listing using the right FX rate? Is the implied cap rate reasonable?"

### Implementation plan

| Tool | What it does |
|---|---|
| `tools/fetch_bcp_rates.py` | Monthly fetch of Tasas Bancos + Tasas Financieras XLSX → `data/bcp/rates_<date>.xlsx` + `data/bcp/rates_latest.csv` |
| `tools/build_rate_trends.py` | Per-rate time series, 1991-present, sparkline data for viewer |
| `tools/build_credit_affordability.py` | Compute monthly payment for $X at current rate (Phase 2) |

---

## 3. BCP Remesas Familiares

| Field | Value |
|---|---|
| URL | https://www.bcp.gov.py/remesas-familiares |
| Auth | None |
| Format | XLSX per year |
| Series from | 2008 |
| Refresh | Quarterly |

### What we extract

| Breakdown | Use |
|---|---|
| **By country** | Top remittance source: España, Argentina, USA, Brazil |
| **By region** | Top remittance destinations in PY: Central, Alto Paraná, Asunción, Itapúa, Caaguazú |
| **Total volume** | $300-450M/year (varies by FX + global economy) |
| **Year-over-year trend** | Indicator of migration health |

**Use**:
- Per-district remittance intensity overlay = **proxy for purchasing power in rural areas**
- Areas with high remittance flow = better property affordability (cash buyers vs mortgage-dependent)
- Migration corridor overlay: which PY districts send/receive the most

### 2008-2026 total (per ABC Color Jun 2026)

- **Total accumulated**: **$11,907.1M USD** (~$12B en 18 años)
- 2008-2025: $11,588.1M
- YTD 2026: $318.9M

### Implementation plan

- `tools/fetch_bcp_remesas.py` — quarterly + historical fetch
- `tools/build_remesas_heatmap.py` — choropleth by remittance intensity per district

---

## 4. BCP Mercado de Valores — Superintendencia de Valores

| Field | Value |
|---|---|
| URL | https://www.bcp.gov.py/web/supervision-de-valores |
| New portal (Dec 2025) | https://www.bcp.gov.py/ + (institutional "Portal de Datos del Mercado de Valores y Productos") |
| Auth | None for public data |
| License | Public info |

### What we extract

| Layer | What it is |
|---|---|
| **Bonos soberanos** | Government bonds outstanding (DEMRE/BCP) |
| **Bonos corporativos** | Corporate bond registry |
| **Acciones cotizadas** | Stocks on BVPASA (Bolsa de Valores de Paraguay) |
| **Fondos de inversión** | Mutual funds + asset managers (registry) |
| **Operaciones registradas** | Trade volume by security |
| **Emisores activos** | Active issuers count |

**Use**:
- BVPASA index trend over time
- Corporate bond yields (proxy for "what a PY company pays for capital")
- Stock market cap by issuer

### BVPASA Bolsa — Stock Exchange

| Field | Value |
|---|---|
| URL | https://www.bvpasa.com.py/ |
| Auth | Public market data free, intraday paid |
| Companies | ~80 listed |

**What we extract**:
- Listed companies (registry + sector + market cap)
- Index value (BVIPA — Paraguay Stock Index)
- Daily trading volume
- Top gainers / losers

---

## 5. AFD — Agencia Financiera de Desarrollo (DEVELOPMENT BANK)

| Field | Value |
|---|---|
| URL | https://www.afd.gov.py/ |
| Auth | None |
| License | Public info |

### What we extract

| Layer | What it is |
|---|---|
| **Catálogo de IFI** | All Intermediary Financial Institutions authorized to channel AFD credit lines |
| **Cooperativas habilitadas** | Cooperatives authorized for public-backed credit |
| **Líneas de crédito activas** | Active credit programs by sector (housing, SME, agriculture, green) |
| **Volumen prestado por sector** | Quarterly disbursement by sector |
| **Tasa preferencial** | First-tier rates for housing (typically 6-8% vs commercial 10-15%) |

**Use**:
- **Affordable housing overlay**: which districts have access to AFD first-tier mortgage programs?
- SME lending density: where can a small business get affordable credit?
- Climate finance: AFD green lines for solar, reforestation, sustainable agriculture

### Implementation plan

- `tools/fetch_afd.py` — quarterly fetch of IFI catalog + disbursements
- `tools/build_credit_access.py` — per-district financial inclusion overlay

---

## 6. INCOOP — Instituto Nacional de Cooperativismo

| Field | Value |
|---|---|
| URL | https://www.incoop.gov.py/ |
| Auth | None for registry |
| License | Public info |

### What we extract

| Layer | What it is |
|---|---|
| **Cooperativas activas** | ~1,000+ cooperatives by category (Type A: ahorro/crédito, Type B: producción, Type C: servicios) |
| **Cooperativas de ahorro y crédito** | Credit cooperatives — major source of rural finance |
| **Cooperativas de producción** | Agricultural production cooperatives |
| **Centrales cooperativas** | Apex cooperatives (e.g., Cooperativa Ñandutí, Chortitzer, Neuland, Loma Plata) |

**Use**:
- Rural financial inclusion overlay (cooperatives = bank where no bank is)
- Mennonite/Chaco/indigenous community financial layer (cooperatives serve unbanked populations)
- Agricultural cooperative strength (proxy for farming collective power)

### Mennonite cooperatives (the unbanked-mapped sector)

| Cooperative | Region | Sector | Members |
|---|---|---|---|
| Cooperativa Chortitzer | Chaco (Loma Plata) | Dairy, agriculture | ~5,000 families |
| Cooperativa Neuland | Chaco (Filadelfia) | Dairy, agriculture | ~3,500 families |
| Cooperativa Fernheim | Chaco | Agriculture | ~2,000 families |
| Cooperativa Ñandutí | Central | Cob artisans + small credit | ~50 (small but documented) |

---

## 7. MUVH — Ministerio de Urbanismo, Vivienda y Hábitat

| Field | Value |
|---|---|
| URL | https://www.muvh.gov.py/ |
| Auth | None |
| License | Public info |

### What we extract

| Layer | What it is |
|---|---|
| **Listado de cooperativas e IFI** | Cooperatives + IFIs authorized for housing programs |
| **Programas de vivienda** | National housing programs (FONAVIS — Fondo Nacional de Vivienda Social, etc.) |
| **Viviendas construidas** | Cumulative housing units built per program |
| **Créditos hipotecarios** | Public-backed mortgage portfolio |

### FONAVIS — the PY social housing program

- National subsidy program for low-income housing (~$15K-30K per unit)
- Operates through cooperatives + IFI channels
- ~30,000-40,000 units/year
- Per-district allocation maps

**Use**:
- Where is public housing being built? (suburb expansion signal)
- Where are CHEAP housing opportunities? (FONAVIS listings, often not on infocasas)
- Subsidy zone overlay

---

## 8. Seprelad — Secretaría de Prevención de Lavado de Dinero

| Field | Value |
|---|---|
| URL | https://www.seprelad.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

| Layer | What it is |
|---|---|
| **Registro de entidades obligadas** | Banks, financieras, cooperatives, real estate agencies, lawyers, accountants — registered for AML reporting |
| **Sanciones** | Public fines + sanctions |
| **Reportes de operaciones sospechosas** | Aggregated (not individual) |

**Use**:
- Validate listing agency legitimacy (is the agency a Seprelad-registered entity?)
- Money-laundering risk overlay (cross-reference against high-value listings)

---

## 9. BACN — Bolsa de Productos del Paraguay

| Field | Value |
|---|---|
| URL | https://www.bacn.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

| Layer | What it is |
|---|---|
| **Productos registrados** | Commodities traded (yerba mate, sesame, cattle) |
| **Volumen de operaciones** | Trade volume by product |
| **Precios** | Reference prices per commodity per period |

**Use**: agricultural commodity price reference for INBIO yield × price overlay.

---

## 10. BCP — Indicadores de Inclusión Financiera

| Field | Value |
|---|---|
| URL | https://www.bcp.gov.py/inclusion-financiera |
| Auth | None |
| Refresh | Annual |

### What we extract

| Layer | What it is |
|---|---|
| **Tenencia de cuentas bancarias** | % adults with bank account per district |
| **Crédito al sector privado / PIB** | Credit penetration per dept |
| **Acceso a seguros** | Insurance penetration |
| **Bancarización rural** | Rural vs urban gap |

**Use**: financial inclusion overlay (correlates with property liquidity + economic vitality).

---

## 11. Private / Third-party (PAGA SI QUEREMOS)

| Source | Cost | What we get |
|---|---|---|
| **Bloomberg / Refinitiv** | $$$$ | Intraday bond + FX data |
| **Wind / Choice** | $$$ | Cross-country macro + flows |
| **Moody's / S&P** | $$$$ | PY sovereign rating (Ba1 stable) |
| **IMF Article IV reports** | Free (annual) | Macro analysis + recommendations |
| **World Bank Doing Business (legacy)** | Free | Per-country business climate |
| **Heritage Index of Economic Freedom** | Free (annual) | Per-country score |
| **Reuters / AFP news feeds** | $500/mo | Market news |

**Use case**: only if we need cross-border capital flows (foreign investment in PY) or institutional-grade risk overlay.

---

## 12. Money flows — what we already have for free

| Layer | Source |
|---|---|
| **DNCP public tenders** | Already in `businesses.md` (~$3-4B/yr) |
| **SET/RUC activity** | Already in `businesses.md` (~90K contributors) |
| **BCP MACRO** | This doc |
| **AHK/UIP foreign investment** | Already in `socioeconomic.md` |

---

## What we DO NOT integrate

- Per-account bank balance (bank secrecy)
- Per-transaction commercial (commercial sensitivity)
- Tax filings detail beyond RUC
- Stock-by-stock proprietary analysis
- Wire-by-wire AML alerts (Seprelad restricted)

---

## Map overlay design (financial intelligence)

```
┌──────────────────────────────────────────────┐
│ MONEY MARKETS (toggleable)                    │
│                                               │
│  ▣ Bank branches (BCP + OSM)                  │
│  ▣ Cooperative branches (INCOOP)              │
│  ▣ AFD IFI offices                            │
│  ▣ MUVH FONAVIS programs (district overlay)   │
│  ▣ Remittance intensity per district (BCP)    │
│  ▣ Banking penetration per district (BCP)     │
│  ▣ Active rates trend (MN + ME)               │
│  ▣ Mortgage affordability (derived)           │
│  ▣ Capital market activity (BVPASA index)     │
│  ▣ Insurance penetration (Seprelad)           │
│  ▣ Distance-to-bank (derived)                 │
│  ▣ Distance-to-cooperative (derived)          │
└──────────────────────────────────────────────┘
```

## Why this matters for the map

| Question | Source |
|---|---|
| What's the current mortgage rate? | BCP Tasas |
| Can I get a 30-year USD mortgage? | BCP Tasas + AFD programs |
| What's the USD/PYG today? | BCP tipo de cambio |
| Is this district financially healthy? | BCP morosidad + inclusión |
| Is there an AFD-backed mortgage program here? | AFD IFI catalog per district |
| What % of households here have bank accounts? | BCP inclusión financiera |
| Where do remittances drive the economy? | BCP remesas by region |
| Is this listing agency legit? | Seprelad registry cross-ref |
| What's the local bank spread? | BCP Tasas per bank |
| What does this district pay for credit? | BCP Tasas bancarias + financieras |

## Implementation priority

| Layer | Phase | Source | Reason |
|---|---|---|---|
| BCP Tasas history | 1.5 | BCP | Foundational rates overlay |
| BCP tipo de cambio | 1.5 | BCP | Foundational FX |
| BCP RIN + TPM | 1.5 | BCP | Macro dashboard widget |
| Bank branches | 1 | OSM + BCP | Already partly in OSM |
| BCP Remesas | 2 | BCP | Migration overlay |
| AFD IFI catalog | 2 | AFD | Affordable housing overlay |
| INCOOP cooperatives | 2 | INCOOP | Rural finance overlay |
| MUVH FONAVIS | 2.5 | MUVH | Public housing overlay |
| BVPASA Bolsa | 3 | BVPASA | Capital market widget |
| Seprelad registry | 2.5 | Seprelad | Listing legitimacy check |
| Mortgage affordability calc | 2 | derived | Per-property overlay |

---

## Cost

| Layer | Cost |
|---|---|
| BCP datasets | $0 |
| AFD catalog | $0 |
| INCOOP | $0 |
| MUVH | $0 |
| Seprelad | $0 |
| BVPASA public | $0 |
| BVPASA intraday | $200-500/mo |
| Bloomberg / Refinitiv | $1,500+/mo per terminal |

**Floor**: $0 for the core financial intelligence layer.
**Recommended add-on**: $0 unless you want intraday market data.

---

## See also

- `docs/operations/data-inventory.md` — master catalog
- `docs/sources/businesses.md` — DNCP tenders + RUC
- `docs/sources/socioeconomic.md` — EPH + IPM
- `docs/operations/properties-pipeline.md` — listings + escritura anchors