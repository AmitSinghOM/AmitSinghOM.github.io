# amit-singh.github.io — Roadmap

Live at <https://amitsinghom.github.io/>. Built in small, visible increments; every
change lands through a pull request and deploys via GitHub Pages from `main`.

> Rule: every claim on the site must be traceable to a public repository or a
> verifiable artifact. Test counts and performance numbers are re-verified by
> running the suites before they are published.

## Phase 0 — Single-page site  ·  ✅ done (2026-08)
Hero, selected-work cards, leadership and experience sections, print-ready résumé
page, canonical/Open Graph metadata, `ProfilePage` + `Person` JSON-LD, sitemap,
robots, manifest, social card. No JavaScript, fonts, analytics, or trackers.

## Phase 1 — Evidence links  ·  ✅ done (2026-09)
Project cards link directly to the evidence they cite: the webhook platform's
public benchmarks page and SKIP LOCKED deep-dive, and the CloudScale source
repository once it was made public.

## Phase 2 — Polish  ·  ✅ done (2026-08 → 2026-09)
Responsive layout, focus-visible and reduced-motion handling, skip link,
sub-35 KB total page weight, `rel="noreferrer"` on all external links.

## Phase 2b — Cut and verify  ·  ✅ done (2026-09-19)
Three featured projects and four in brief, each card on one template: the
problem, two design decisions, one measured result, one stated limit, evidence
links. Absolute claims bounded (AgentOS: duplicate *committed* completions are
prevented; external side effects still rely on downstream idempotency). Every
quoted number moved into `facts.json`, enforced against the site and the GitHub
repository descriptions by `scripts/check_facts.py` in CI.

## Phase 3 — Writeups index  ·  ⏳ not started
A short index page listing architecture writeups as they are published in the
project repositories (benchmarks, delivery semantics, resilience notes).

## Definition of done (every change)
1. Every number on the site re-verified against the public repo it cites and recorded in `facts.json`; `python3 scripts/check_facts.py --remote` passes.
2. HTML parses clean; all outbound links return 200.
3. `sitemap.xml` `lastmod` updated when indexed content changes.
4. Landed via pull request, verified live after Pages deploys.
