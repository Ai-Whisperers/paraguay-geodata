# Polki Squad — Demo static site

> Static HTML/CSS/JS demo of what the rebuilt polkisquad.com would look like.
> Built for visual reference only. NOT the production site.

---

## What's in here

```
demo/
├── index.html         Homepage
├── css/styles.css     Design system (colors, typography, components, animations)
├── js/main.js         Counter animation, newsletter form, fade-in
├── README.md          This file
└── (more pages TBD)
```

## How to view

```bash
# Option 1: Open in browser
open demo/index.html

# Option 2: Local server
cd demo && python3 -m http.server 8000
# Then open http://localhost:8000
```

## What's done

- [x] Homepage (`/`)
- [x] Design system in CSS (colors, typography, spacing, components)
- [x] Counter animation on stats
- [x] Newsletter form (demo only)
- [x] Fade-in on scroll
- [x] Responsive (mobile + tablet)
- [x] Accessibility basics (alt text, semantic HTML, focus states)

## What's TODO (placeholders, to fill with real content)

- [ ] Real photos of:
  - Hero animal (replaced with emoji placeholder)
  - Refugio (replaced with emoji placeholder)
  - 3+ featured animals (replaced with emoji)
- [ ] Real stats:
  - +3,000 rescates → confirm exact number
  - 2,800 adopciones → confirm
  - 120 padrinos activos → confirm
  - 15 vet partners → confirm
- [ ] Real animal names + descriptions:
  - Toby, Luna, Rocky (placeholders)
  - Need 12-24 real animalitos
- [ ] Real links to other pages (adopta.html, padrinos.html, etc.)
- [ ] Real newsletter integration (Brevo or similar)
- [ ] Real WhatsApp link (+595 971 771371 → confirm)
- [ ] Real email (hola@polkisquad.com → confirm)
- [ ] Real Instagram link (@polkisquad → confirm)
- [ ] Real Facebook link (polki-squad → confirm)
- [ ] Real TikTok link (@polkisquad → confirm)
- [ ] Real footer credit (Ai-Whisperers → confirm)

## What the design system documents

- See `offering/04-visual/01-visual-system.md` for the full spec
- This demo implements P0 of that spec:
  - Color palette
  - Typography (Fraunces + Inter)
  - Component library (buttons, cards, forms, navigation)
  - Animations (fade-in, counter, smooth scroll)
  - Spacing scale
  - Radii
  - Shadows
  - Responsive breakpoints

## Notes

- This is **NOT** a real production site. It's a visual prototype.
- The real site would use:
  - Next.js 16 + Tailwind v4
  - Cloudflare Pages
  - Airtable as CMS
  - Plausible for analytics
  - Brevo for newsletter
  - Real photos, real data
- The CSS here is hand-written. The real site would use Tailwind for consistency + speed.
- The JS here is vanilla. The real site would use React.
- All copy in Spanish. Paraguayan voice ("tíos y tías", "che", etc.)

## When to use

- To show Polki Squad what their new site could look like
- To test the design system before building the full site
- As a reference for the dev who builds the real site
- As a portfolio piece for Ai-Whisperers

## When NOT to use

- As a production site (use the real one when built)
- As a substitute for the real one (placeholders everywhere)
- For SEO (no real content, no real links)
- For ads (no real conversion tracking)
