# Amit Singh | Engineering Portfolio

A dependency-free portfolio focused on senior backend engineering: Python, AWS and production reliability. React and applied AI remain supporting capabilities.

Public site: <https://amitsinghom.github.io/>. This working copy is a **local preview**; changes are not published until separately approved and merged.

## Preview and check

```bash
python3 -m http.server 8000 --bind 127.0.0.1
python3 scripts/check_facts.py
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/check_facts.py --remote
```

Open <http://localhost:8000>. `--remote` uses public GitHub APIs; `GITHUB_TOKEN` is optional for a higher rate limit.

## Site structure

- `index.html`: production ownership, three featured public projects, supporting work and contact.
- `resume.html`: readable, print-ready résumé, with actual employment titles and employer/client attribution.
- `assets/Amit_Singh_Backend_Resume.pdf`: generated two-page résumé; regenerate after editing the HTML.
- `evidence.html`: dated observations, benchmark scope and explicit project limitations.
- `facts.json`: pinned public commits, scoped CI observations and evidence boundaries.
- `scripts/check_facts.py`: checks observation text, project scope, pinned links, boundary text, HTML nesting and local links/fragments.
- `scripts/test_check_facts.py`: negative tests for drift and broken links.
- `styles.css`: responsive layout, keyboard focus and reduced-motion support.
- `assets/social-card.svg`: editable social-card source; `social-card.png` is its 1200 × 630 render.

## Evidence policy

Do not aggregate test counts across overlapping suites or matrix jobs. Keep volatile numbers off the homepage and résumé; place public test observations on the evidence page with a pinned commit, job URL, suite scope and run date. Benchmark results are bounded observations, not production capacity or availability claims.

Remote checks validate that public commits exist and cited CI jobs belong to those commits and succeeded. They **do not parse numeric results from logs** or force current repository descriptions to match a historical snapshot. Read the source logs when updating observations. Employment achievements are owner-provided résumé history, not public-project CI evidence. Do not publish client source or private operational artifacts to substantiate them.

## PDF and social image

The PDF is printed from `resume.html` using Chromium, A4, CSS page size, background graphics enabled, with browser headers/footers disabled. Check both pages and extracted text after regeneration. The PNG is rendered from `assets/social-card.svg` at 1200 × 630.

## Publication

Review the local preview before approving a commit or push. The existing live branch has changes absent from this local starting point: compare and reconcile it before publishing rather than force-pushing or replacing remote history. CI changes here run only after publication.

The site has no client-side JavaScript execution, external fonts, analytics or runtime dependencies. The JSON-LD block is metadata. Canonical URLs and résumé PDF links intentionally use the eventual public site domain.
