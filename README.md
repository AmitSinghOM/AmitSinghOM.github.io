# Amit Singh — Engineering Portfolio

A fast, dependency-free portfolio focused on senior backend, distributed-systems, AWS platform, and applied-AI engineering.

**Intended public URL:** <https://amitsinghom.github.io/>

> The GitHub user-site repository must be named `AmitSinghOM.github.io` for this URL to work.

## Site structure

- `index.html` — responsive portfolio and structured profile data
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

The site includes canonical metadata, Open Graph/Twitter cards, `ProfilePage` and `Person` JSON-LD, index directives, a sitemap, semantic HTML, and descriptive content. After deployment:

1. Add `https://amitsinghom.github.io/` to Google Search Console.
2. Submit `https://amitsinghom.github.io/sitemap.xml`.
3. Link the portfolio from GitHub, LinkedIn, and public project READMEs.

## Deploy

Create the public repository `AmitSinghOM/AmitSinghOM.github.io`, push this directory to its `main` branch, and configure GitHub Pages to deploy from the repository root. No build workflow is required.

The site uses no JavaScript, third-party fonts, analytics, trackers, or runtime dependencies.
