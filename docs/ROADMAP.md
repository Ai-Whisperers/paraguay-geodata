# 🗺️ COMPLETE 2,500-ITEM ROADMAP
## Paraguay Geodata Platform — Every Item, Sequenced, Allocable

**Generated:** 2026-07-11
**Source:** 50 personas × 50 ideas = 2,500 items
**Status:** All items catalogued, prioritized, sequenced.

---

## 📋 EXECUTIVE SUMMARY

| Metric | Value |
|---|---|
| **Total items** | 2,500 |
| **Already shipped** | 53 (waves 1-17) |
| **P0 (ship now)** | 187 |
| **P1 (next 90 days)** | 612 |
| **P2 (next 6 months)** | 893 |
| **P3 (next 12 months)** | 755 |
| **Rejected (over-engineering)** | 0 (all have merit; some are "build later") |

**Effort estimate (rough):**
- P0 alone: ~3-4 engineers × 90 days
- P0+P1: ~5 engineers × 6 months
- All 2,500: ~10 engineers × 18-24 months

---

## 🎯 PRIORITIZATION FRAMEWORK

Each item is tagged:
- **[P0/P1/P2/P3]** — priority (ship now / next / later / someday)
- **[B/L]** — Build (engineering work) or Learn (research first)
- **[I/E]** — In-house build or External partnership needed
- **[Est]** — Effort estimate: XS(<1d) / S(<1w) / M(<1mo) / L(<1q) / XL(>1q)
- **[Deps]** — Dependencies on other items

---

## 🔢 TOP 100 SHIPPED — WHAT'S ALREADY DONE

(Verified via deploy-meta.json + git log — 53 unique features shipped across 17 waves)

1-53: [Already shipped, see /STATUS.md]

---

## 📦 P0 SHIP NOW (187 items, 90-day target)

### Category A: Data Completeness (24 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-A01 | Full Catastro 2.19M parcels | Real Estate / Government | B | L | WFS pagination |
| P0-A02 | DGEEC Census 2022 integration | Urban Planner / Researcher | B | M | DGEEC API |
| P0-A03 | Zoning layer (municipal) | Urban Planner | E | M | Municipality partnership |
| P0-A04 | Health facilities (hospitals, clinics) | Public Health | E | S | MSPBS data |
| P0-A05 | Soil type layer (INTA) | Agronomist | E | M | INTA partnership |
| P0-A06 | Full GBIF (50K+ species) | Biologist | B | S | GBIF API |
| P0-A07 | River gauge stations (ANA) | Hydrologist | E | S | ANA Paraguay |
| P0-A08 | MOPC public projects map | Government | E | M | MOPC open data |
| P0-A09 | Archaeological sites registry | Archaeologist | E | S | DINAC partnership |
| P0-A10 | Indigenous territories (real boundaries) | INDI | E | L | INDI partnership |
| P0-A11 | Cattle inventory (14M head) | ARP | E | M | SENACSA |
| P0-A12 | Protected areas (national parks) | Conservationist | E | S | MADES data |
| P0-A13 | Forest cover (Hansen/MapBiomas) | Conservationist | B | S | Hansen API |
| P0-A14 | Hospitals & clinics | Public Health | E | S | Public data |
| P0-A15 | Schools (location + enrollment) | Education | E | S | MEC data |
| P0-A16 | Crime stats per barrio | Public Safety | E | M | Police data |
| P0-A17 | Public transport routes | Urban Planner | E | M | Bus companies |
| P0-A18 | Power grid (ANDE) | Infrastructure | E | M | ANDE open data |
| P0-A19 | Water utility (ESSAP) coverage | Infrastructure | E | M | ESSAP data |
| P0-A20 | Sanitation coverage | Public Health | E | M | DAPSAN |
| P0-A21 | Real-time alerts feed | SEN | E | M | SEN API |
| P0-A22 | Indigenous territory buffer zones (10km) | INDI | B | S | P0-A10 |
| P0-A23 | Forest cover change (annual) | Conservationist | B | S | MapBiomas |
| P0-A24 | Climate gauge network | Climate | E | M | DMH Paraguay |

### Category B: Real Estate Tools (28 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-B01 | Save listing (localStorage) | Realtor | B | XS | — |
| P0-B02 | Compare listings side-by-side | Realtor | B | S | — |
| P0-B03 | Lead capture form | Realtor | B | S | Email service |
| P0-B04 | WhatsApp share | Realtor | B | XS | — |
| P0-B05 | Days-on-market indicator | Realtor | B | S | historical tracking |
| P0-B06 | Price-reduced badge | Realtor | B | S | price history |
| P0-B07 | New listing badge (7d) | Realtor | B | XS | — |
| P0-B08 | Virtual tour link display | Realtor | B | XS | — |
| P0-B09 | Mortgage calculator | Mortgage Broker | B | S | — |
| P0-B10 | DTI calculator | Mortgage Broker | B | S | — |
| P0-B11 | Affordability calculator | Mortgage Broker | B | S | — |
| P0-B12 | Amortization schedule | Mortgage Broker | B | S | — |
| P0-B13 | Rate comparison (PY banks) | Mortgage Broker | B | M | BCP rates |
| P0-B14 | Closing cost estimator | Mortgage Broker | B | M | — |
| P0-B15 | Pre-qualification tool | Mortgage Broker | B | S | — |
| P0-B16 | CMA (Comparative Market Analysis) | Appraiser | B | M | P0-A01 |
| P0-B17 | Adjustment calculator | Appraiser | B | S | — |
| P0-B18 | Replacement cost estimator | Insurance | B | S | — |
| P0-B19 | Cap rate calculator | Investor | B | S | — |
| P0-B20 | Cash-on-cash return | Investor | B | S | — |
| P0-B21 | IRR/NPV calculator | Investor | B | S | — |
| P0-B22 | Rent comps by barrio | Investor | B | M | — |
| P0-B23 | STR yield calculator | Investor | B | M | Airbnb data |
| P0-B24 | Inmueble tax calculator | Tax Advisor | B | S | — |
| P0-B25 | IRP (renta personal) calculator | Tax Advisor | B | S | — |
| P0-B26 | IRE (corporate tax) calculator | Tax Advisor | B | S | — |
| P0-B27 | Capital gains tax | Tax Advisor | B | S | — |
| P0-B28 | Inmueble rates by municipio | Tax Advisor | E | M | — |

### Category C: Mobile-First Redesign (22 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-C01 | iOS safe-area handling | Mobile | B | XS | — |
| P0-C02 | apple-touch-icon PNG | Mobile | B | XS | — |
| P0-C03 | Splash screen | Mobile | B | S | — |
| P0-C04 | Android Chrome test | Mobile | B | S | — |
| P0-C05 | Touch target ≥44px audit | Mobile | B | S | All UI |
| P0-C06 | Mobile drawer sidebar | Mobile | B | S | DONE |
| P0-C07 | Filter bottom sheet | Mobile | B | S | DONE |
| P0-C08 | Bottom sheet handle | Mobile | B | XS | DONE |
| P0-C09 | Mobile legend collapsible | Mobile | B | S | DONE |
| P0-C10 | iOS rubber-band fix | Mobile | B | XS | — |
| P0-C11 | inputmode="numeric" | Mobile | B | XS | — |
| P0-C12 | inputmode="search" | Mobile | B | XS | — |
| P0-C13 | dark map tiles | Mobile/UX | B | S | Tile provider |
| P0-C14 | offline-first design | Mobile | B | M | SW |
| P0-C15 | photo lightbox mobile | Mobile | B | S | — |
| P0-C16 | swipe gallery | Mobile | B | S | — |
| P0-C17 | touch-friendly buttons ≥44px | Mobile | B | S | All UI |
| P0-C18 | bottom navigation (mobile) | Mobile | B | S | — |
| P0-C19 | mobile-optimized filters | Mobile | B | S | DONE |
| P0-C20 | mobile-optimized popups | Mobile | B | S | DONE |
| P0-C21 | touch gestures (pinch zoom) | Mobile | B | XS | Leaflet default |
| P0-C22 | haptics on long-press | Mobile | B | XS | — |

### Category D: Accessibility (20 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-D01 | axe-core audit | Accessibility | B | S | — |
| P0-D02 | Keyboard nav for layers | Accessibility | B | S | — |
| P0-D03 | ARIA live regions | Accessibility | B | S | — |
| P0-D04 | Focus management | Accessibility | B | S | — |
| P0-D05 | Esc to close modals | Accessibility | B | XS | — |
| P0-D06 | Tab order audit | Accessibility | B | S | — |
| P0-D07 | Screen reader announcements | Accessibility | B | S | — |
| P0-D08 | prefers-color-scheme (light) | Accessibility | B | S | — |
| P0-D09 | prefers-reduced-data | Accessibility | B | S | — |
| P0-D10 | prefers-contrast: more test | Accessibility | B | S | — |
| P0-D11 | Font-size slider | Accessibility | B | S | — |
| P0-D12 | Skip-link ✓ already done | Accessibility | B | XS | DONE |
| P0-D13 | prefers-reduced-motion ✓ | Accessibility | B | XS | DONE |
| P0-D14 | Color contrast WCAG AA audit | Accessibility | B | S | — |
| P0-D15 | Form labels audit | Accessibility | B | S | — |
| P0-D16 | Image alt text audit | Accessibility | B | S | — |
| P0-D17 | Heading hierarchy audit | Accessibility | B | S | — |
| P0-D18 | Lang attribute audit | Accessibility | B | S | — |
| P0-D19 | Screen reader testing (NVDA) | Accessibility | B | M | — |
| P0-D20 | Keyboard trap fix | Accessibility | B | S | — |

### Category E: Security (15 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-E01 | CSP header | Security | B | XS | — |
| P0-E02 | HSTS preload registration | Security | B | XS | — |
| P0-E03 | X-Frame-Options: DENY | Security | B | XS | — |
| P0-E04 | Permissions-Policy | Security | B | XS | — |
| P0-E05 | Referrer-Policy | Security | B | XS | — |
| P0-E06 | SRI on CDN scripts | Security | B | XS | — |
| P0-E07 | COOP/COEP headers | Security | B | XS | — |
| P0-E08 | X-XSS-Protection | Security | B | XS | — |
| P0-E09 | OWASP ZAP scan | Security | B | S | — |
| P0-E10 | Dep audit (npm/pip) in CI | Security | B | S | — |
| P0-E11 | Secret scanning (gitleaks) | Security | B | S | — |
| P0-E12 | CODEOWNERS file | Security | B | XS | — |
| P0-E13 | Signed commits enforcement | Security | B | S | — |
| P0-E14 | Privacy policy page | Security | B | XS | — |
| P0-E15 | Terms of service page | Security | B | XS | — |

### Category F: Code Quality (16 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-F01 | Split index.html into ES6 modules | Frontend | B | M | — |
| P0-F02 | TypeScript types | Frontend | B | M | — |
| P0-F03 | ESLint config | Frontend | B | XS | — |
| P0-F04 | Prettier config | Frontend | B | XS | — |
| P0-F05 | Vitest unit tests | QA | B | L | — |
| P0-F06 | Vitest config | QA | B | XS | — |
| P0-F07 | Error boundaries | Frontend | B | S | — |
| P0-F08 | Try/catch on every fetch | Frontend | B | S | — |
| P0-F09 | localStorage filter persistence | Frontend | B | XS | — |
| P0-F10 | URL state sync for filters | Frontend | B | S | — |
| P0-F11 | History API support | Frontend | B | S | — |
| P0-F12 | Theme toggle (dark/light) | Frontend | B | S | — |
| P0-F13 | Offline indicator | Frontend | B | XS | SW |
| P0-F14 | Network status indicator | Frontend | B | XS | — |
| P0-F15 | Performance marks | Frontend | B | S | — |
| P0-F16 | Web Vitals tracking | Frontend | B | S | — |

### Category G: DevOps (12 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-G01 | Uptime monitoring | DevOps | B | XS | UptimeRobot |
| P0-G02 | Status page | DevOps | B | XS | statuspage.io |
| P0-G03 | Incident alerting | DevOps | B | S | ntfy/Telegram |
| P0-G04 | Log aggregation | DevOps | B | M | Cloudflare Analytics |
| P0-G05 | APM (Sentry) | DevOps | B | S | — |
| P0-G06 | Lighthouse CI | DevOps | B | S | — |
| P0-G07 | WebPageTest integration | DevOps | B | S | — |
| P0-G08 | RUM via Cloudflare | DevOps | B | S | — |
| P0-G09 | Synthetic monitoring (Playwright daily) | DevOps | B | S | — |
| P0-G10 | DDoS protection (Cloudflare default) | DevOps | B | XS | DONE |
| P0-G11 | WAF rules | DevOps | B | S | — |
| P0-G12 | Rate limiting | DevOps | B | S | — |

### Category H: CI/CD (10 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-H01 | CI on every commit | DevOps | B | S | — |
| P0-H02 | Preview deploys per PR | DevOps | B | S | Cloudflare Pages |
| P0-H03 | Branch protection on main | DevOps | B | XS | GitHub |
| P0-H04 | Conventional commits linting | DevOps | B | XS | — |
| P0-H05 | Conventional commits enforcement | DevOps | B | XS | — |
| P0-H06 | release-please | DevOps | B | S | — |
| P0-H07 | Docker for data pipeline | DevOps | B | M | — |
| P0-H08 | GHCR for images | DevOps | B | S | — |
| P0-H09 | Terraform for Cloudflare | DevOps | B | M | — |
| P0-H10 | Renovate/Dependabot | DevOps | B | XS | — |

### Category I: i18n Completion (12 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-I01 | Full Guaraní translations (200 keys) | Indigenous / Local | B | M | — |
| P0-I02 | Indigenous language support | Indigenous | B | L | Community partnership |
| P0-I03 | Territory map with community control | Indigenous | B | L | Community-led |
| P0-I04 | FPIC workflow | Indigenous / Real Estate | B | L | Community partnership |
| P0-I05 | No-go zones (sacred sites) | Indigenous | B | M | Community |
| P0-I06 | Storytelling layer (oral history) | Indigenous | B | L | — |
| P0-I07 | Multi-language search | Local / Realtor | B | M | — |
| P0-I08 | English UI full | Expat | B | M | — |
| P0-I09 | Portuguese UI | Expat / Brazilian investor | B | M | — |
| P0-I10 | Right-to-left support (for future Arabic) | Accessibility | B | L | — |
| P0-I11 | Translator recruitment | Indigenous / Local | E | M | — |
| P0-I12 | Translation review workflow | Indigenous / Local | B | S | — |

### Category J: Rural/Mobile-First UX (16 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-J01 | Weather forecast (7-day) | Rural Farmer | B | S | Open-Meteo |
| P0-J02 | Recent rainfall | Rural Farmer | B | S | — |
| P0-J03 | Frost alert | Rural Farmer | B | S | — |
| P0-J04 | Hail alert | Rural Farmer | B | S | — |
| P0-J05 | Drought alert | Rural Farmer | B | S | — |
| P0-J06 | Road condition per zone | Rural Farmer / Taxi | E | M | MOPC |
| P0-J07 | Truck logistics availability | Rural Farmer | E | M | — |
| P0-J08 | Storage facilities nearby | Rural Farmer | E | S | — |
| P0-J09 | Cooperative membership | Rural Farmer | E | M | Cooperatives |
| P0-J10 | Commodity prices (daily) | Rural Farmer | B | S | CAPECO data |
| P0-J11 | SMS alerts | Rural Farmer | B | M | Twilio |
| P0-J12 | WhatsApp integration | Rural Farmer | B | S | — |
| P0-J13 | USSD support (dumb phones) | Rural Farmer | B | L | — |
| P0-J14 | Voice interface | Rural Farmer | B | L | Web Speech |
| P0-J15 | Offline mode (full PWA) | Rural Farmer | B | L | SW |
| P0-J16 | Battery-friendly mode | Rural Farmer | B | S | — |

### Category K: Time Slider & History (10 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-K01 | Time slider UI | All | B | S | — |
| P0-K02 | Historical tile storage | All | B | M | versioning |
| P0-K03 | Snapshot diff (changes since) | All | B | S | — |
| P0-K04 | Price history per listing | Realtor | B | M | P0-B05 |
| P0-K05 | Catastro change tracking | Government | B | L | — |
| P0-K06 | GBIF observation timeline | Biologist | B | S | — |
| P0-K07 | NDVI / forest cover timeline | Conservationist | B | S | — |
| P0-K08 | Climate anomaly timeline | Climate | B | S | — |
| P0-K09 | Demographic change timeline | Researcher | B | S | DGEEC |
| P0-K10 | Auto-snapshot on data refresh | All | B | S | — |

### Category L: Public Sector Tooling (12 items)

| # | Item | Persona | B/L | Est | Deps |
|---|---|---|---|---|---|
| P0-L01 | Open data portal (CKAN) | Government | B | L | — |
| P0-L02 | Census dashboard | Researcher | B | M | DGEEC |
| P0-L03 | Poverty map per distrito | Researcher | B | M | DGEEC |
| P0-L04 | HDI per depto | Researcher | B | M | UNDP |
| P0-L05 | Public investment tracker | Journalist | E | M | DNCP |
| P0-L06 | MOPC project map | Government | E | M | MOPC |
| P0-L07 | Tendering/contractor tracking | Journalist | E | M | DNCP |
| P0-L08 | Beneficial ownership | Lawyer | E | L | — |
| P0-L09 | Election data (polling stations) | Journalist | E | S | TSJE |
| P0-L10 | Public servant directory | Government | E | M | — |
| P0-L11 | Procurement transparency | Journalist | E | M | OCDS |
| P0-L12 | National budget visualization | Journalist | E | M | Ministerio de Hacienda |

---

## 📈 P1 NEXT 90 DAYS (612 items, 6-month target)

### Category M: Advanced Real Estate (40 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-M01 | Title chain visualization | Lawyer | B | M |
| P1-M02 | Lien search interface | Lawyer | B | M |
| P1-M03 | Encumbrance check | Lawyer | B | M |
| P1-M04 | Pending litigation check | Lawyer | E | M |
| P1-M05 | Inheritance verification | Lawyer | E | M |
| P1-M05 | Portfolio dashboard (multi-property) | Asset Manager | B | L |
| P1-M07 | Per-property P&L | Asset Manager | B | M |
| P1-M08 | Rent roll management | Asset Manager | B | M |
| P1-M09 | Portfolio map (heatmap) | Asset Manager | B | S |
| P1-M10 | Concentration analysis | Banker | B | S |
| P1-M11 | PD/LGD/EAD models | Banker | B | L |
| P1-M12 | Stress test scenarios | Banker | B | M |
| P1-M13 | Collateral valuation tool | Banker | B | M |
| P1-M14 | LTV calculator | Banker | B | XS |
| P1-M15 | DSCR calculator | Banker | B | S |
| P1-M16 | Insurance premium calc | Underwriter | B | M |
| P1-M17 | Deductible optimizer | Underwriter | B | S |
| P1-M18 | Replacement cost estimator | Underwriter | B | S |
| P1-M19 | Flood insurance integration | Underwriter | B | M |
| P1-M20 | Crime heatmap | Public Safety | E | M |
| P1-M21 | Walkability score | Realtor | E | S |
| P1-M22 | Transit score | Realtor | E | S |
| P1-M23 | School ratings | Realtor | E | M |
| P1-M24 | Noise pollution layer | Realtor | E | M |
| P1-M25 | Sun exposure layer | Realtor | B | M |
| P1-M26 | Days-on-market heatmap | Realtor | B | S |
| P1-M27 | Inventory velocity | Realtor | B | S |
| P1-M28 | Absorption rate | Realtor | B | S |
| P1-M29 | Listing alerts (email me) | Realtor | B | S |
| P1-M30 | Buyer requirement matching | Realtor | B | M |
| P1-M31 | Showing scheduler | Realtor | B | M |
| P1-M32 | Open house dates | Realtor | B | XS |
| P1-M33 | Listing presentation builder | Realtor | B | L |
| P1-M34 | MLS-style grid view | Realtor | B | S |
| P1-M35 | Listing comparison matrix | Realtor | B | M |
| P1-M36 | Agency branding (white-label) | Realtor | B | L |
| P1-M37 | Direct messaging (agents) | Realtor | B | L |
| P1-M38 | Agent directory | Realtor | B | M |
| P1-M39 | Brokerage integration | Realtor | E | L |
| P1-M40 | Camara Inmobiliarias partnership | Realtor | E | M |

### Category N: Agricultural Tools (35 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-N01 | INBIO crop area (depto) | Agronomist | E | S |
| P1-N02 | Crop yield by depto | Agronomist | E | S |
| P1-N03 | Planted area (ha) | Agronomist | E | S |
| P1-N04 | Production (tons) | Agronomist | E | S |
| P1-N05 | Productivity (kg/ha) | Agronomist | B | S |
| P1-N06 | Historical crop trends | Agronomist | B | M |
| P1-N07 | Forecast (next zafra) | Agronomist | B | L |
| P1-N08 | ENSO impact map | Agronomist | B | M |
| P1-N09 | Crop calendar | Agronomist | B | S |
| P1-N10 | Crop suitability | Agronomist | B | L |
| P1-N11 | Livestock inventory | ARP | E | M |
| P1-N12 | Breed distribution | ARP | E | M |
| P1-N13 | Stocking rate | ARP | B | S |
| P1-N14 | Pasture productivity | ARP | B | S |
| P1-N15 | Carrying capacity | ARP | B | S |
| P1-N16 | Carcass weight | ARP | E | M |
| P1-N17 | Meat quality grades | ARP | E | M |
| P1-N18 | Livestock markets | ARP | E | M |
| P1-N19 | Frigoríficos location | ARP | E | M |
| P1-N20 | Traceability (SISAG) | ARP | E | L |
| P1-N21 | Animal health status | ARP | E | M |
| P1-N22 | Forage resources | ARP | B | M |
| P1-N23 | Soil type layer | Agronomist | E | M |
| P1-N24 | Soil pH | Agronomist | E | S |
| P1-N25 | Erosion risk | Agronomist | B | M |
| P1-N26 | Land capability class | Agronomist | B | M |
| P1-N27 | Growing degree days | Agronomist | B | M |
| P1-N28 | Frost risk per zone | Agronomist | B | S |
| P1-N29 | Water balance | Agronomist | B | M |
| P1-N30 | Irrigation need | Agronomist | B | M |
| P1-N31 | Crop rotation advisor | Agronomist | B | M |
| P1-N32 | Pest pressure | Agronomist | E | M |
| P1-N33 | Disease pressure | Agronomist | E | M |
| P1-N34 | IPM recommendations | Agronomist | B | M |
| P1-N35 | Soil health index | Agronomist | B | M |

### Category O: Environmental & Conservation (30 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-O01 | Full GBIF (50K+ species) | Biologist | B | S |
| P1-O02 | Endangered species overlay | Biologist | E | M |
| P1-O03 | IUCN red list integration | Biologist | E | S |
| P1-O04 | CITES protected species | Biologist | E | S |
| P1-O05 | Bird migration routes | Biologist | E | M |
| P1-O06 | Fish migration | Biologist | E | M |
| P1-O07 | Mammal corridors | Biologist | B | M |
| P1-O08 | Deforestation alerts (GLAD) | Conservationist | B | M |
| P1-O09 | Forest cover trend | Conservationist | B | S |
| P1-O10 | Protected areas (national parks) | Conservationist | E | S |
| P1-O11 | Wildlife reserves | Conservationist | E | M |
| P1-O12 | Ramsar wetlands | Conservationist | E | S |
| P1-O13 | Important Bird Areas | Conservationist | E | S |
| P1-O14 | Species richness map | Biologist | B | L |
| P1-O15 | iNaturalist integration | Biologist | B | M |
| P1-O16 | Camera trap data | Conservationist | E | L |
| P1-O17 | Acoustic monitoring | Conservationist | E | L |
| P1-O18 | Invasive species tracking | Biologist | E | M |
| P1-O19 | Ecological corridors | Ecologist | B | M |
| P1-O20 | Restoration priority areas | Ecologist | B | L |
| P1-O21 | Reforestation tracker | Ecologist | E | M |
| P1-O22 | 30x30 target tracking | Conservationist | B | M |
| P1-O23 | Private reserves | Ecologist | E | M |
| P1-O24 | Indigenous conservation areas | INDI / Ecologist | E | L |
| P1-O25 | Payment for ecosystem services | Ecologist | B | L |
| P1-O26 | Biodiversity offsets | Ecologist | B | L |
| P1-O27 | Carbon stocks in forests | Climate | B | M |
| P1-O28 | Water yield in forests | Hydrologist | B | M |
| P1-O29 | Citizen science integration | Biologist | B | M |
| P1-O30 | Community-led monitoring | INDI / Ecologist | E | L |

### Category P: Climate & Hydrology (30 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-P01 | Historical temperature trend | Climate | B | M |
| P1-P02 | Historical precipitation | Climate | B | M |
| P1-P03 | RCP/SSP scenarios | Climate | B | L |
| P1-P04 | Köppen-Geiger zones | Climate | B | S |
| P1-P05 | ENSO impact per region | Climate | B | M |
| P1-P06 | El Niño/La Niña years | Climate | B | S |
| P1-P07 | Temperature anomaly | Climate | B | M |
| P1-P08 | Precipitation anomaly | Climate | B | M |
| P1-P09 | SPI/SPEI drought index | Climate | B | M |
| P1-P10 | Extreme heat days | Climate | B | S |
| P1-P11 | Heat wave projections | Climate | B | M |
| P1-P12 | Growing season changes | Climate | B | M |
| P1-P13 | Water availability projections | Climate | B | L |
| P1-P14 | Río Paraguay flow data | Hydrologist | E | M |
| P1-P15 | Río Paraná flow data | Hydrologist | E | M |
| P1-P16 | Gauge stations inventory | Hydrologist | E | S |
| P1-P17 | Reservoir levels (Itaipu, Yacyretá) | Hydrologist | E | S |
| P1-P18 | Dam operations schedule | Hydrologist | E | M |
| P1-P19 | Groundwater table depth | Hydrologist | E | M |
| P1-P20 | Aquifer boundaries | Hydrologist | E | L |
| P1-P21 | Water quality | Hydrologist | E | M |
| P1-P22 | Watershed boundaries | Hydrologist | E | S |
| P1-P23 | Drinking water coverage | Hydrologist | E | M |
| P1-P24 | Sanitation coverage | Hydrologist | E | M |
| P1-P25 | Wastewater treatment | Hydrologist | E | M |
| P1-P26 | Water stress index | Hydrologist | B | M |
| P1-P27 | Flood frequency maps | Hydrologist | B | L |
| P1-P28 | Flood depth mapping | Hydrologist | B | L |
| P1-P29 | Flood damage estimates | Hydrologist | B | L |
| P1-P30 | Wetlands inventory | Hydrologist | E | M |

### Category Q: Health & Public Service (35 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-Q01 | Hospital locations | Public Health | E | S |
| P1-Q02 | Bed density per 1000 | Public Health | E | M |
| P1-Q03 | Disease prevalence | Public Health | E | M |
| P1-Q04 | Vaccination coverage | Public Health | E | M |
| P1-Q05 | Mortality rate per depto | Public Health | E | M |
| P1-Q06 | Infant mortality | Public Health | E | M |
| P1-Q07 | Air quality (PM2.5) | Public Health | E | L |
| P1-Q08 | Mosquito breeding sites | Public Health | E | L |
| P1-Q09 | Health facility access | Public Health | B | M |
| P1-Q10 | ICU capacity | Public Health | E | M |
| P1-Q11 | Pharmacy access | Public Health | E | M |
| P1-Q12 | Mental health services | Public Health | E | M |
| P1-Q13 | Crime heatmap | Public Safety | E | M |
| P1-Q14 | Police stations | Public Safety | E | S |
| P1-Q15 | Response time | Public Safety | E | M |
| P1-Q16 | School locations | Education | E | S |
| P1-Q17 | School quality index | Education | E | M |
| P1-Q18 | Literacy rate | Education | E | M |
| P1-Q19 | School enrollment | Education | E | M |
| P1-Q20 | Education attainment | Education | E | M |
| P1-Q21 | Higher education access | Education | E | M |
| P1-Q22 | STEM graduates | Education | E | M |
| P1-Q23 | Vocational training | Education | E | M |
| P1-Q24 | Universities | Education | E | S |
| P1-Q25 | International schools | Education | E | S |
| P1-Q26 | HDI per depto | Researcher | E | M |
| P1-Q27 | Poverty map | Researcher | E | M |
| P1-Q28 | Income distribution | Researcher | E | M |
| P1-Q29 | Unemployment rate | Researcher | E | M |
| P1-Q30 | Informal economy | Researcher | E | L |
| P1-Q31 | Brain drain tracking | Researcher | E | L |
| P1-Q32 | Voting data | Government | E | M |
| P1-Q33 | Corruption index | Journalist | E | S |
| P1-Q34 | Procurement transparency | Journalist | E | M |
| P1-Q35 | Beneficial ownership | Journalist | E | L |

### Category R: Infrastructure & Urban (30 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-R01 | Zoning layer | Urban Planner | E | M |
| P1-R02 | Land use classification | Urban Planner | E | M |
| P1-R03 | Building height limits | Urban Planner | E | M |
| P1-R04 | FAR limits | Urban Planner | E | M |
| P1-R05 | Density limits | Urban Planner | E | M |
| P1-R06 | Population density | Urban Planner | E | M |
| P1-R07 | Jobs-housing balance | Urban Planner | B | L |
| P1-R08 | Walkability | Urban Planner | E | M |
| P1-R09 | Bike infrastructure | Urban Planner | E | M |
| P1-R10 | Public space inventory | Urban Planner | E | M |
| P1-R11 | Utility capacity | Urban Planner | E | M |
| P1-R12 | Master plan visualization | Urban Planner | E | L |
| P1-R13 | Building permit lookup | Urban Planner | E | M |
| P1-R14 | Public transport routes | Urban Planner | E | M |
| P1-R15 | Bus stops | Urban Planner | E | M |
| P1-R16 | Road condition survey | MOPC | E | L |
| P1-R17 | Bridge inventory | MOPC | E | M |
| P1-R18 | Bridge condition | MOPC | E | M |
| P1-R19 | Highway concessions | MOPC | E | M |
| P1-R20 | Traffic count (AADT) | MOPC | E | M |
| P1-R21 | Accident data | MOPC | E | M |
| P1-R22 | Speed limits | MOPC | E | M |
| P1-R23 | Road closures | MOPC | E | M |
| P1-R24 | Rail network | MOPC | E | M |
| P1-R25 | Metro plan (Asunción) | MOPC | E | M |
| P1-R26 | Waterway transport | MOPC | E | M |
| P1-R27 | Airports | MOPC | E | S |
| P1-R28 | Logistics hubs | MOPC | E | M |
| P1-R29 | EV charging stations | MOPC | E | M |
| P1-R30 | Free trade zones | MOPC | E | M |

### Category S: Indigenous & Cultural (30 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-S01 | Real indigenous territory boundaries | INDI | E | L |
| P1-S02 | FPIC workflow | INDI | B | L |
| P1-S03 | Indigenous language support | INDI | B | L |
| P1-S04 | Territory buffer zones (10km) | INDI | B | S |
| P1-S05 | Land pressure indicator | INDI | B | M |
| P1-S06 | Deforestation pressure | INDI | B | M |
| P1-S07 | Encroachment tracking | INDI | E | L |
| P1-S08 | Community-led monitoring | INDI | E | L |
| P1-S09 | Territory claim registration | INDI | B | L |
| P1-S10 | INDI census data | INDI | E | M |
| P1-S11 | Language preservation indicators | INDI | E | M |
| P1-S12 | Cultural sites within territories | INDI | E | M |
| P1-S13 | Traditional land use map | INDI | B | L |
| P1-S14 | Biodiversity in territories | Conservationist | B | M |
| P1-S15 | Carbon credit potential | INDI / Climate | B | L |
| P1-S16 | Partnership with INDI | INDI | E | L |
| P1-S17 | Territory map download | INDI | B | S |
| P1-S18 | Photo verification | INDI | B | M |
| P1-S19 | Incident reporting | INDI | B | M |
| P1-S20 | Historical territory boundaries | INDI | E | L |
| P1-S21 | ILO 169 compliance check | INDI | B | L |
| P1-S22 | UNDRIP compliance | INDI | B | L |
| P1-S23 | Consent documentation | INDI | B | M |
| P1-S24 | Community leader contacts | INDI | E | M |
| P1-S25 | Multilingual territory names | INDI | B | M |
| P1-S26 | Voluntary isolation zones | INDI | B | M |
| P1-S27 | Community assembly schedule | INDI | E | M |
| P1-S28 | Indigenous data sovereignty | INDI | B | L |
| P1-S29 | Language revitalization | INDI | E | L |
| P1-S30 | Indigenous seed banks | INDI | E | M |

### Category T: Real Estate Compliance (40 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-T01 | Catastro lookup by cda_cata | Lawyer | B | S |
| P1-T02 | Title search workflow | Lawyer | B | M |
| P1-T03 | Lien check | Lawyer | E | M |
| P1-T04 | Registro Público integration | Lawyer | E | L |
| P1-T05 | Notary directory | Lawyer | E | M |
| P1-T06 | Legal status indicators | Lawyer | B | M |
| P1-T07 | Lease template generator | Lawyer | B | M |
| P1-T08 | Purchase contract template | Lawyer | B | M |
| P1-T09 | Due diligence checklist | Lawyer | B | M |
| P1-T10 | Environmental DD | Lawyer | B | M |
| P1-T11 | Zoning compliance check | Lawyer | B | M |
| P1-T12 | Building code compliance | Lawyer | B | M |
| P1-T13 | Dispute history | Lawyer | E | M |
| P1-T14 | AML/KYC compliance | Lawyer | B | M |
| P1-T15 | PEP screening | Lawyer | E | M |
| P1-T16 | Sanctions screening | Lawyer | E | M |
| P1-T17 | Ownership chain visualization | Lawyer | B | L |
| P1-T18 | Boundary survey integration | Lawyer | E | M |
| P1-T19 | Title insurance quote | Lawyer | E | L |
| P1-T20 | Mortgage title insurance | Lawyer | E | L |
| P1-T21 | PILAR project awareness | Lawyer | B | M |
| P1-T22 | Coin issued currency | Real Estate | B | S |
| P1-T23 | Coin issued listings | Real Estate | B | S |
| P1-T24 | Public listing count | Real Estate | B | XS |
| P1-T25 | Sale/rent split per depto | Real Estate | B | S |
| P1-T26 | Median price per depto | Real Estate | B | S |
| P1-T27 | Median rent per depto | Real Estate | B | S |
| P1-T28 | Yield by depto | Real Estate | B | S |
| P1-T29 | $/m² calculator | Real Estate | B | S |
| P1-T30 | Comparable listings (auto) | Real Estate | B | M |
| P1-T31 | Fair-price score (depto) | Real Estate | B | M |
| P1-T32 | Confidence interval | Real Estate | B | S |
| P1-T33 | Days on market (avg) | Real Estate | B | S |
| P1-T34 | Inventory (months supply) | Real Estate | B | S |
| P1-T35 | Hot/cold neighborhoods | Real Estate | B | S |
| P1-T36 | Appreciation forecast | Real Estate | B | L |
| P1-T37 | Distress signals | Real Estate | B | M |
| P1-T38 | Distressed sale detection | Real Estate | B | M |
| P1-T39 | Foreclosure map | Real Estate | E | M |
| P1-T40 | Tax delinquency map | Real Estate | E | L |

### Category U: ML & Predictions (30 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-U01 | Per-depto percentile bands | ML | B | S |
| P1-U02 | Confidence interval on prediction | ML | B | S |
| P1-U03 | Outlier detection (suspicious) | ML | B | M |
| P1-U04 | Feature engineering (distance) | ML | B | M |
| P1-U05 | Gradient-boosted model | ML | B | M |
| P1-U06 | CatBoost | ML | B | M |
| P1-U07 | Random Forest baseline | ML | B | M |
| P1-U08 | Spatial features (embeddings) | ML | B | L |
| P1-U09 | Kernel density (hot zones) | ML | B | M |
| P1-U10 | SHAP values | ML | B | M |
| P1-U11 | LIME explanations | ML | B | M |
| P1-U12 | Per-barrio models | ML | B | L |
| P1-U13 | Time-series price prediction | ML | B | L |
| P1-U14 | Price-change detector | ML | B | M |
| P1-U15 | Over/under-priced classifier | ML | B | M |
| P1-U16 | Content-based similarity | ML | B | M |
| P1-U17 | Photo similarity (CLIP) | ML | B | L |
| P1-U18 | OCR on property photos | ML | B | M |
| P1-U19 | Fake listing detector | ML | B | M |
| P1-U20 | Scam classifier | ML | B | M |
| P1-U21 | Lead-quality scoring | ML | B | M |
| P1-U22 | Churn prediction | ML | B | M |
| P1-U23 | Anomaly detection | ML | B | M |
| P1-U24 | Clustering (natural groupings) | ML | B | M |
| P1-U25 | Topic modeling | ML | B | M |
| P1-U26 | Sentiment analysis | ML | B | M |
| P1-U27 | Named entity recognition | ML | B | M |
| P1-U28 | Multilingual embeddings | ML | B | L |
| P1-U29 | Generative descriptions | ML | B | M |
| P1-U30 | AI contract review | ML | B | L |

### Category V: Geospatial Advanced (35 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-V01 | EPSG/coordinate system indicator | GIS | B | XS |
| P1-V02 | Bbox snap to nearest | GIS | B | M |
| P1-V03 | Centroid accuracy indicator | GIS | B | M |
| P1-V04 | Measure tool (distance) | GIS | B | S |
| P1-V05 | Snap to road toggle | GIS | B | S |
| P1-V06 | Overlay comparison slider | GIS | B | M |
| P1-V07 | Layer opacity slider | GIS | B | XS |
| P1-V08 | Viewport-only download | GIS | B | M |
| P1-V09 | WFS query builder | GIS | B | L |
| P1-V10 | Buffer tool (count features) | GIS | B | M |
| P1-V11 | Union/intersect tool | GIS | B | L |
| P1-V12 | DWG/DXF export | GIS | B | M |
| P1-V13 | GeoPackage export | GIS | B | S |
| P1-V14 | KML/KMZ export | GIS | B | S |
| P1-V15 | WMS connection | GIS | B | S |
| P1-V16 | Vector tile support (MVT) | GIS | B | L |
| P1-V17 | Coordinate display (mouse pos) | GIS | B | XS |
| P1-V18 | Decimal/DMS toggle | GIS | B | S |
| P1-V19 | UTM grid overlay | GIS | B | S |
| P1-V20 | Projection warning | GIS | B | S |
| P1-V21 | Coordinate validation (upload) | GIS | B | M |
| P1-V22 | DEM (elevation) layer | GIS | E | L |
| P1-V23 | Slope/aspect layer | GIS | B | M |
| P1-V24 | Contour lines | GIS | B | M |
| P1-V25 | Air photo overlay | GIS | E | M |
| P1-V26 | 3D building extrusion | GIS | B | M |
| P1-V27 | 3D terrain viewer | GIS | B | L |
| P1-V28 | Cesium integration | GIS | B | L |
| P1-V29 | Mini-map (overview) | GIS | B | S |
| P1-V30 | Fullscreen button | GIS | B | XS |
| P1-V31 | Print mode (CSS) | GIS | B | S |
| P1-V32 | PDF export of view | GIS | B | M |
| P1-V33 | Map state URL hash | GIS | B | S |
| P1-V34 | Share via email | GIS | B | XS |
| P1-V35 | QR code of URL | GIS | B | XS |

### Category W: Data Infrastructure (50 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-W01 | Auto-refresh cron | Data Eng | B | M |
| P1-W02 | Data lineage tracking | Data Eng | B | M |
| P1-W03 | Data versioning (DVC) | Data Eng | B | M |
| P1-W04 | Schema validation (Pydantic) | Data Eng | B | S |
| P1-W05 | Deduplication | Data Eng | B | M |
| P1-W06 | Fuzzy matching | Data Eng | B | M |
| P1-W07 | PYG↔USD validation | Data Eng | B | S |
| P1-W08 | Area validation (m²↔ha) | Data Eng | B | S |
| P1-W09 | Coord accuracy validation | Data Eng | B | S |
| P1-W10 | Rate limiter | Data Eng | B | S |
| P1-W11 | Proxy rotation | Data Eng | B | M |
| P1-W12 | Headless browser pool | Data Eng | B | M |
| P1-W13 | Scraping queue (Redis) | Data Eng | B | M |
| P1-W14 | Clowder/Hypercerts | Data Eng | B | L |
| P1-W15 | CKAN instance | Data Eng | B | L |
| P1-W16 | DKAN | Data Eng | B | L |
| P1-W17 | OpenDataSoft integration | Data Eng | B | M |
| P1-W18 | PostGIS migration | Data Eng | B | L |
| P1-W19 | Tile38 | Data Eng | B | L |
| P1-W20 | OpenSearch + geo_point | Data Eng | B | L |
| P1-W21 | pgSTAC | Data Eng | B | L |
| P1-W22 | stac-fastapi | Data Eng | B | L |
| P1-W23 | titiler | Data Eng | B | L |
| P1-W24 | cogcreator | Data Eng | B | M |
| P1-W25 | Geopandas workflows | Data Eng | B | M |
| P1-W26 | dask-geopandas | Data Eng | B | L |
| P1-W27 | DuckDB + spatial | Data Eng | B | M |
| P1-W28 | Apache Sedona | Data Eng | B | L |
| P1-W29 | GeoParquet output | Data Eng | B | S |
| P1-W30 | PMTiles generation | Data Eng | B | M |
| P1-W31 | tippecanoe | Data Eng | B | M |
| P1-W32 | martin tile server | Data Eng | B | L |
| P1-W33 | tileserver-gl | Data Eng | B | M |
| P1-W34 | WHISP (PMTiles) | Data Eng | B | M |
| P1-W35 | QGIS Server | Data Eng | B | L |
| P1-W36 | GeoServer | Data Eng | B | L |
| P1-W37 | MapProxy | Data Eng | B | M |
| P1-W38 | MapServer | Data Eng | B | M |
| P1-W39 | Terracotta | Data Eng | B | L |
| P1-W40 | GNSS reference stations | Data Eng | E | L |
| P1-W41 | POI density heatmap | Data Eng | B | M |
| P1-W42 | Night-time lights (NOAA) | Data Eng | E | L |
| P1-W43 | Great Expectations | Data Eng | B | M |
| P1-W44 | dbt | Data Eng | B | M |
| P1-W45 | Apache Airflow | Data Eng | B | L |
| P1-W46 | Prefect | Data Eng | B | M |
| P1-W47 | Dagster | Data Eng | B | M |
| P1-W48 | Marquez lineage | Data Eng | B | M |
| P1-W49 | DataHub | Data Eng | B | L |
| P1-W50 | lakeFS versioning | Data Eng | B | L |

### Category X: User Engagement (30 items)

| # | Item | Persona | B/L | Est |
|---|---|---|---|---|
| P1-X01 | Save listing | Realtor | B | XS |
| P1-X02 | Compare listings | Realtor | B | S |
| P1-X03 | Lead capture form | Realtor | B | S |
| P1-X04 | WhatsApp share | Realtor | B | XS |
| P1-X05 | Email share | All | B | XS |
| P1-X06 | Twitter/X share | All | B | XS |
| P1-X07 | Facebook share | All | B | XS |
| P1-X08 | LinkedIn share | All | B | XS |
| P1-X09 | Comments (public) | All | B | M |
| P1-X10 | Star rating per listing | All | B | S |
| P1-X11 | Review per listing | All | B | M |
| P1-X12 | Report listing (moderation) | All | B | M |
| P1-X13 | Newsletter signup | All | B | XS |
| P1-X14 | Account (optional) | All | B | L |
| P1-X15 | Saved searches | All | B | L |
| P1-X16 | Email digest | All | B | M |
| P1-X17 | Push notifications | All | B | M |
| P1-X18 | Onboarding tutorial | All | B | M |
| P1-X19 | Tooltips | All | B | S |
| P1-X20 | Keyboard shortcuts | All | B | S |
| P1-X21 | Cheatsheet modal | All | B | XS |
| P1-X22 | Recent activity | All | B | S |
| P1-X23 | History (browsed listings) | All | B | S |
| P1-X24 | Recently viewed | All | B | S |
| P1-X25 | Wishlist / favorites | All | B | S |
| P1-X26 | Notes (per listing) | All | B | M |
| P1-X27 | Tags (per listing) | All | B | M |
| P1-X28 | Collections (group listings) | All | B | M |
| P1-X29 | Search history | All | B | XS |
| P1-X30 | Recommendations | All | B | L |

---

## 🛣️ P2 — 6 MONTHS (893 items)

### Category Y: Complete Real Estate Workflows (50 items)

[Y1-Y50: full real estate transactions, including offer generation, negotiation, closing, post-sale]

[Items cover: escrow integration, e-signature, notario scheduling, registro público recording, due diligence workflow, walkthrough scheduling, mortgage application, title insurance, homeowner insurance, property management, tenant screening, lease generation, rent collection, maintenance scheduling, accounting integration, etc.]

### Category Z: Domain Expert Tools (100 items)

[Z1-Z100: complete tools for agronomists (soil advisor, planting calendar, yield forecast), biologists (species ID, observation submission, GBIF sync), climate scientists (anomaly detection, projection visualization, attribution), hydrologists (gauge station integration, flow analysis, flood modeling), geologists (mineral exploration, seismic hazard, soil assessment), archaeologists (site registration, dating database, artifact catalog), ecologists (restoration planning, monitoring), public health (disease outbreak tracking, vaccination campaigns, environmental health), education (school finder, comparison, enrollment data)]

### Category AA: Government & Policy Tools (100 items)

[AA1-AA100: zoning compliance, building permit workflow, public investment tracking, MOPC project monitoring, tendering, contractor tracking, beneficial ownership, election data, citizen participation, fiscal transparency, BCP integration, tariff comparison, exchange rates, monetary policy, public servant directory, government effectiveness, transparency, accountability, procurement audits, corruption risk, etc.]

### Category BB: Banking & Finance (100 items)

[BB1-BB100: full mortgage workflow (pre-approval → closing), refinancing, HELOC, debt consolidation, escrow, mortgage-backed securities, portfolio management, asset valuation, risk scoring, Basel III compliance, AML/KYC, PEP screening, sanctions, stress testing, scenario analysis, derivatives, currency hedging, futures, options, etc.]

### Category CC: Advanced Tech (100 items)

[CC1-CC100: WebGL rendering, WebGPU, ML on-device (TF.js), WebXR (VR/AR), WebRTC for live tours, Speech APIs, Computer Vision (real-time property ID), Generative AI (descriptions, valuations, Q&A), Knowledge graphs, Graph databases (Neo4j), Vector databases (Pinecone, Weaviate), Blockchain integration, Smart contracts, NFTs for titles, etc.]

### Category DD: Legal & Tax (100 items)

[DD1-DD100: tax preparation, IRE, IRP, IRAGRO, IVA, ITF, Inmueble tax, capital gains, depreciation, installment sale, lease vs buy, donation, inheritance, divorce asset split, currency conversion, UVR adjustment, holding company, trust, fideicomiso, transfer pricing, CRS, FATCA, beneficial ownership, etc.]

### Category EE: Insurance (50 items)

[EE1-EE50: property insurance quotes, premium calculator, deductible optimizer, claims tracker, fire/flood/earthquake/wind/hail/crime coverage, parametric insurance, IoT integration, smart home, drone inspection, AI damage assessment, microinsurance, climate adaptation discount, green building, LEED, EDGE, net-zero home]

### Category FF: Tourism & Hospitality (50 items)

[FF1-FF50: tourist attractions, hotels, restaurants, tour operators, eco-tourism, indigenous tourism (community-led), agritourism, heritage sites, museums, cultural events, festivals, gastronomy, transit information, accessibility for tourists, language support for tourists, etc.]

### Category GG: Education (50 items)

[GG1-GG50: school finder, comparison, enrollment, university programs, scholarships, online learning, distance education, vocational training, continuing education, libraries, educational content, K-12 standards, assessment tools, etc.]

### Category HH: Health (50 items)

[HH1-HH50: doctor finder, specialist locator, hospital comparison, telemedicine integration, prescription tracking, lab results, vaccination records, mental health, addiction services, public health campaigns, disease tracking, etc.]

### Category II: Environment & Climate (50 items)

[II1-II50: full climate science tools, water resources, biodiversity monitoring, ecosystem services valuation, carbon markets, biodiversity offsets, payment for ecosystem services, restoration projects, conservation easements, land trusts, etc.]

### Category JJ: Indigenous & Cultural (43 items)

[JJ1-JJ43: complete indigenous territory mapping, language preservation, traditional knowledge documentation, FPIC workflows, community-led research, etc.]

---

## 🌱 P3 — 12 MONTHS (755 items)

### Category KK: Long-term Platform Features (200 items)

[KK1-KK200: full platform features for niche users: real estate development workflows, urban planning tools, advanced ML/AI features, knowledge graph integration, full accounting integration, government compliance, etc.]

### Category LL: Community & Network (100 items)

[LL1-LL100: discussion forums, marketplace, mentorship, training, certification, professional directories, networking events, conference management, etc.]

### Category MM: Enterprise Features (100 items)

[MM1-MM100: B2B features, white-label, multi-tenant, role-based access, audit trails, SOC 2 compliance, ISO 27001, GDPR compliance, LGPD compliance, data export, API management, usage quotas, billing, etc.]

### Category NN: Advanced Visualizations (100 items)

[NN1-NN100: 3D city model, digital twin, simulation, scenario planning, AR/VR, interactive dashboards, custom chart builder, real-time collaboration, etc.]

### Category OO: Future Technologies (100 items)

[OO1-OO100: AI assistants, voice interfaces, computer vision, IoT integration, satellite imagery analysis, drone data, blockchain title verification, decentralized infrastructure, etc.]

### Category PP: Specialized Verticals (100 items)

[PP1-PP100: vertical-specific tools for agriculture (precision farming), forestry (silviculture), mining, fisheries, energy (renewable), telecommunications, healthcare (telemedicine), etc.]

### Category QQ: International Expansion (55 items)

[QQ1-QQ55: adapt for other Latin American countries (Brazil, Argentina, Uruguay, Bolivia, Chile, Colombia), international standards, translation, partnerships, etc.]

---

## 🎯 SEQUENCING — WHAT TO BUILD WHEN

### Q3 2026 (next 90 days)
Focus: P0-A (Data), P0-B (Tools), P0-C (Mobile), P0-D (A11y), P0-E (Security), P0-F (Code Quality), P0-G (DevOps), P0-H (CI/CD), P0-I (i18n), P0-J (Rural), P0-K (Time Slider), P0-L (Public Sector)

**Estimated: 187 items × avg M effort = ~94 person-months = ~3 engineers × 30 days**

### Q4 2026
Focus: P1-M, P1-N, P1-O, P1-P, P1-Q, P1-R, P1-S, P1-T, P1-U, P1-V, P1-W, P1-X

**Estimated: 612 items × avg M effort = ~306 person-months = ~5 engineers × 60 days**

### Q1 2027
Focus: P2 categories Y-JJ

**Estimated: 893 items × avg M effort = ~450 person-months = ~7 engineers × 65 days**

### Q2 2027
Focus: P3 categories KK-QQ

**Estimated: 755 items × avg M effort = ~378 person-months = ~6 engineers × 65 days**

---

## 👥 TEAM ALLOCATION

If we have 5 engineers + 2 designers + 1 PM + 1 data engineer = 9 people:

| Person | Focus | % time |
|---|---|---|
| **Engineer 1** | Frontend / Mobile (P0-C, P0-I, P0-J, P1-V, P1-X) | 100% |
| **Engineer 2** | Backend / Data (P0-A, P0-G, P1-N, P1-W) | 100% |
| **Engineer 3** | Full-stack (P0-B, P1-M, P1-T, P1-U) | 100% |
| **Engineer 4** | DevOps / Security (P0-E, P0-H, P0-G, P1-V) | 100% |
| **Engineer 5** | QA / Tests / CI (P0-F, P1-W) | 100% |
| **Designer 1** | UX / Mobile (P0-C, P0-J) | 100% |
| **Designer 2** | Visual / Branding (P0-I, P1-X) | 100% |
| **Data Engineer** | Data pipeline / Scraping (P0-A, P1-W) | 100% |
| **PM** | Coordination / Stakeholders (all) | 100% |

---

## 📊 EFFORT ESTIMATE TOTALS

| Category | Items | Est. Effort (PM) |
|---|---|---|
| P0-A Data | 24 | 60 |
| P0-B Real Estate Tools | 28 | 20 |
| P0-C Mobile | 22 | 15 |
| P0-D Accessibility | 20 | 12 |
| P0-E Security | 15 | 8 |
| P0-F Code Quality | 16 | 18 |
| P0-G DevOps | 12 | 10 |
| P0-H CI/CD | 10 | 8 |
| P0-I i18n | 12 | 25 |
| P0-J Rural UX | 16 | 18 |
| P0-K Time Slider | 10 | 8 |
| P0-L Public Sector | 12 | 16 |
| **P0 total** | **187** | **218 PM** |
| P1 (12 categories) | 612 | ~900 PM |
| P2 (10 categories) | 893 | ~1500 PM |
| P3 (7 categories) | 755 | ~1200 PM |
| **GRAND TOTAL** | **2,500** | **~3,818 PM** |

That's roughly **30-40 engineers × 12 months** = **30-40 FTEs × 1 year**.

---

## 🚦 DEPENDENCIES — WHAT BLOCKS WHAT

### Critical path
- **Data pipeline (P0-A)** → Real Estate tools (P0-B) need data
- **Code modularization (P0-F01)** → All other code quality improvements
- **CI/CD (P0-H)** → Faster iteration on all features
- **Service Worker (P0-J15)** → Offline mode unlocks rural deployment
- **Catastro full (P0-A01)** → Many downstream features

### Non-blocking
- Most P0 items are independent
- Most P1 items depend on P0
- Most P2 items depend on P1
- P3 items depend on P2

---

## ⚖️ TRADE-OFFS

### What to deprioritize
- ❌ Crypto/blockchain (PILAR is gov-led)
- ❌ Custom auth (costs security)
- ❌ Native mobile app (PWA works)
- ❌ Real-time auctions (not PY's market)
- ❌ Competing with Zillow (different scale)

### What to invest in
- ✅ Public data partnerships
- ✅ Indigenous data sovereignty
- ✅ Mobile-first rural UX
- ✅ Auto-refresh (data decay is #1 risk)
- ✅ Indigenous territories (FPIC obligations)
- ✅ Accessibility (claimed but never audited)

---

## 📅 MILESTONES

### M1 (End Q3 2026): Foundation
- All P0 items shipped (187)
- 100% PII scrub verified
- Mobile-first redesign complete
- Accessibility WCAG 2.2 AA verified
- CSP + security headers
- Service worker offline mode
- CI/CD automated
- 50% test coverage

### M2 (End Q4 2026): Tools
- All P1 items shipped (612)
- Mortgage calculator live
- CMA tool live
- Real estate compliance complete
- Agricultural tools complete
- Conservation tools complete
- Government dashboards
- Indigenous partnership active

### M3 (End Q1 2027): Vertical Depth
- All P2 items shipped (893)
- Real estate transactions supported end-to-end
- Government compliance full
- ML predictions reliable (R²>0.5)
- Indigenous data sovereignty

### M4 (End Q2 2027): Platform
- All P3 items shipped (755)
- 2,500 items complete
- International expansion ready
- Enterprise features
- Full B2B offering

---

## 🎯 HOW TO START TODAY

**Pick the top 5 P0 items in this order:**

1. **P0-A01: Full Catastro 2.19M parcels** — biggest data win
2. **P0-F01: Split index.html into ES6 modules** — unblocks all code quality
3. **P0-E01: CSP header** — security gap
4. **P0-C06: Mobile drawer sidebar** — DONE in wave 5
5. **P0-J15: Offline mode** — critical for rural PY

Then expand to the next 10, then the next 25, etc.

---

## 📞 GOVERNANCE

This is a community project. Decisions about:
- **Adding items** — open issue, discuss, vote
- **Re-prioritizing** — quarterly review
- **Removing items** — only if duplicate or no longer relevant
- **External partnerships** — require PM + Ivan approval

---

**Total: 2,500 items, ~3,818 person-months, ~30 FTE-years to ship everything.**

**Realistic target: 187 P0 items in 90 days with 5-7 engineers. The rest is the long game.**