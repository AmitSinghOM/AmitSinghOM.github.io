# Amit Singh — Engineering Portfolio

A fast, dependency-free portfolio focused on senior backend, distributed-systems, AWS platform, and applied-AI engineering.

**Live at:** <https://amitsinghom.github.io/> — deployed by GitHub Pages from the `main` branch of `AmitSinghOM/AmitSinghOM.github.io`.

Every number on the site comes from one file, [`facts.json`](./facts.json), measured against the public repository it cites (`pytest --collect-only` at the commit named there). `scripts/check_facts.py` fails CI when `index.html`, `resume.html`, or a GitHub repository description disagrees with that file, so a stale count cannot survive a merge:

```bash
python3 scripts/check_facts.py            # site vs facts.json
python3 scripts/check_facts.py --remote   # plus GitHub descriptions and tags
```

To change a number: re-measure, edit `facts.json`, then the site, then the repository description. See [ROADMAP.md](./ROADMAP.md) for what has shipped and what is next.

## Site structure

- `index.html` — responsive portfolio and structured profile data
- `facts.json` and `scripts/check_facts.py` — source of truth for every quoted number, and the CI check that enforces it
- `styles.css` — visual system, responsive behavior, and accessibility states
- `resume.html` — print-ready résumé (`noindex` to prevent search competition)
- `robots.txt` and `sitemap.xml` — crawler discovery
- `site.webmanifest` and `favicon.svg` — browser metadata
- `assets/social-card.png` — LinkedIn and social-sharing preview

## Preview locally

No installation or build step is required:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## SEO setup

The site includes canonical metadata, Open Graph/Twitter cards, `ProfilePage` and `Person` JSON-LD, index directives, a sitemap, semantic HTML, and descriptive content. Google Search Console ownership is verified via the meta tag in `index.html`; `sitemap.xml` is referenced from `robots.txt`. Update `lastmod` in the sitemap whenever indexed content changes.

## Deploy

Changes land on `main` through pull requests gated by the `facts` workflow; GitHub Pages redeploys the repository root automatically. No build step is required.

The site uses no JavaScript, third-party fonts, analytics, trackers, or runtime dependencies.
