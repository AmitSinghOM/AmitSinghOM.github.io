#!/usr/bin/env python3
"""Fail when a number on the site disagrees with facts.json.

Local checks (always):
  * every project in facts.json appears in each site file (or only in the files
    its optional "pages" list names) as an element carrying
    data-project="<key>", and that element's visible text contains
    "<tests> tests", the version string (if any), every must_mention phrase,
    and none of the must_not_mention phrases;
  * the hero element tagged data-fact="tests-total" equals the sum of tests.

Remote checks (--remote, needs network; GITHUB_TOKEN optional):
  * the GitHub repository description contains "<tests> tests";
  * the version tag exists on the repository.

Standard library only; exit code 1 on any drift so CI can gate on it.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"


def visible_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def element_text(page: str, key: str, path: str) -> str | None:
    """Return the visible text of the element tagged data-project=key."""
    match = re.search(rf'<(article|div)\b[^>]*\bdata-project="{re.escape(key)}"[^>]*>', page)
    if not match:
        return None
    tag = match.group(1)
    start = match.end()
    depth = 1
    pos = start
    token = re.compile(rf"<(/?){tag}\b[^>]*>")
    while depth:
        nxt = token.search(page, pos)
        if not nxt:
            raise SystemExit(f"{path}: unbalanced <{tag}> for data-project={key}")
        depth += -1 if nxt.group(1) else 1
        pos = nxt.end()
    return visible_text(page[start:pos])


def fmt(n: int) -> str:
    return f"{n:,}"


def check_local(facts: dict) -> list[str]:
    problems: list[str] = []
    projects = facts["projects"]
    for rel in facts["site"]["files"]:
        path = ROOT / rel
        page = path.read_text(encoding="utf-8")
        for key, spec in projects.items():
            if rel not in spec.get("pages", facts["site"]["files"]):
                if element_text(page, key, rel) is not None:
                    problems.append(f"{rel} [{key}]: present but facts.json scopes it to {spec['pages']}")
                continue
            text = element_text(page, key, rel)
            if text is None:
                problems.append(f"{rel}: no element with data-project=\"{key}\"")
                continue
            tests = spec["tests"]
            if not re.search(rf"\b{re.escape(fmt(tests))} tests\b", text):
                found = re.findall(r"\b[\d,]+ tests\b", text)
                problems.append(f"{rel} [{key}]: expected '{fmt(tests)} tests', found {found or 'none'}")
            version = spec.get("version")
            if version and version not in text:
                found = re.findall(r"\bv\d+\.\d+\.\d+\b", text)
                problems.append(f"{rel} [{key}]: expected version '{version}', found {found or 'none'}")
            for phrase in spec.get("must_mention", []):
                if phrase not in text:
                    problems.append(f"{rel} [{key}]: missing required phrase '{phrase}'")
            for phrase in spec.get("must_not_mention", []):
                if phrase in text:
                    problems.append(f"{rel} [{key}]: forbidden phrase present '{phrase}'")
        fact = facts["site"].get("tests_total_fact")
        if fact and rel == "index.html":
            total = sum(spec["tests"] for spec in projects.values())
            match = re.search(rf'data-fact="{re.escape(fact)}"[^>]*>([^<]*)<', page)
            if not match:
                problems.append(f"{rel}: no element with data-fact=\"{fact}\"")
            elif match.group(1).strip() != fmt(total):
                problems.append(f"{rel}: tests-total shows '{match.group(1).strip()}', facts sum to '{fmt(total)}'")
    return problems


def github(path: str) -> object:
    req = urllib.request.Request(f"{API}{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "portfolio-facts-check"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed https host
        return json.load(resp)


def check_remote(facts: dict) -> list[str]:
    problems: list[str] = []
    for key, spec in facts["projects"].items():
        repo = spec["repo"]
        try:
            meta = github(f"/repos/{repo}")
            tags = {t["name"] for t in github(f"/repos/{repo}/tags?per_page=100")}
        except urllib.error.URLError as exc:
            problems.append(f"remote [{key}]: could not reach GitHub for {repo}: {exc}")
            continue
        description = meta.get("description") or ""
        tests = spec["tests"]
        if not re.search(rf"\b{re.escape(fmt(tests))} tests\b", description):
            found = re.findall(r"\b[\d,]+ tests\b", description)
            problems.append(f"remote [{key}]: description says {found or 'no test count'}, facts say '{fmt(tests)} tests'")
        tag = spec.get("version_tag") or spec.get("version")
        if tag and tag not in tags:
            problems.append(f"remote [{key}]: tag '{tag}' not found on {repo} (have {sorted(tags)[-3:]})")
        if meta.get("private"):
            problems.append(f"remote [{key}]: {repo} is private but linked from the portfolio")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--remote", action="store_true", help="also compare against GitHub descriptions and tags")
    args = parser.parse_args()
    facts = json.loads((ROOT / "facts.json").read_text(encoding="utf-8"))
    problems = check_local(facts)
    if args.remote:
        problems += check_remote(facts)
    for line in problems:
        print(f"DRIFT: {line}")
    if problems:
        print(f"{len(problems)} problem(s). Update facts.json from a fresh measurement, then the site, then the descriptions.")
        return 1
    scope = "local + remote" if args.remote else "local"
    print(f"facts.json agrees with the site ({scope}); {len(facts['projects'])} projects checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
