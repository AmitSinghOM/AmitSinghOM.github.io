#!/usr/bin/env python3
"""Check scoped evidence, source links and local navigation. No third-party packages.

--remote additionally checks that cited commits are public and CI jobs match
those commits and succeeded. It does not re-derive numbers from CI logs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


class Page(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.nodes: list[dict] = []
        self.stack: list[dict] = []
        self.errors: list[str] = []
        self.feed(source)
        self.close()
        if self.stack:
            self.errors.append('unclosed elements')

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'text': '', 'links': []}
        self.nodes.append(node)
        href = node['attrs'].get('href')
        if href:
            for parent in self.stack:
                parent['links'].append(href)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1]['tag'] != tag:
            self.errors.append(f'unbalanced closing tag: {tag}')
            return
        self.stack.pop()

    def handle_data(self, data):
        for node in self.stack:
            node['text'] += data

    def find(self, attribute, value):
        return [n for n in self.nodes if n['attrs'].get(attribute) == value]


def normalized(text):
    return ' '.join(text.split())


def check_local(facts: dict, root: Path = ROOT) -> list[str]:
    root = root.resolve()
    problems = []
    pages = {}
    if facts.get('schema_version') != 2:
        return ['unsupported facts schema']
    for rel in facts['site']['files']:
        path = root / rel
        if not path.is_file():
            problems.append(f'{rel}: file missing')
            continue
        source = path.read_text(encoding='utf-8')
        page = pages[rel] = Page(source)
        problems += [f'{rel}: {e}' for e in page.errors]
        ids = [n['attrs']['id'] for n in page.nodes if 'id' in n['attrs']]
        if len(ids) != len(set(ids)):
            problems.append(f'{rel}: duplicate element ID')
        for phrase in facts['site']['forbidden_phrases']:
            if phrase.casefold() in source.casefold():
                problems.append(f'{rel}: forbidden phrase {phrase!r}')
        for key, spec in facts['projects'].items():
            matches = page.find('data-project', key)
            expected = int(rel in spec['pages'])
            if len(matches) != expected:
                problems.append(f'{rel}: expected {expected} project block for {key}')
        unknown = [n for n in page.nodes if 'data-project' in n['attrs'] and n['attrs']['data-project'] not in facts['projects']]
        if unknown:
            problems.append(f'{rel}: unknown project block')
        if rel != 'evidence.html' and re.search(r'\b[\d,]+\s+(?:tests|passed|skipped)\b', source):
            problems.append(f'{rel}: move volatile test counts to evidence.html')

    evidence = pages.get('evidence.html')
    expected_ids = []
    for key, spec in facts['projects'].items():
        if not re.fullmatch(r'[a-f0-9]{40}', spec['commit']):
            problems.append(f'{key}: commit must be a full SHA')
        blocks = evidence.find('data-project', key) if evidence else []
        if len(blocks) != 1:
            continue
        block = blocks[0]
        source = f'https://github.com/{spec["repo"]}/tree/{spec["commit"]}'
        if source not in block['links']:
            problems.append(f'{key}: pinned source link missing')
        if spec['boundary'] not in normalized(block['text']):
            problems.append(f'{key}: evidence boundary missing')
        for observation in spec['observations']:
            identifier = observation['id']
            expected_ids.append(identifier)
            nodes = evidence.find('data-fact', identifier)
            if len(nodes) != 1 or normalized(nodes[0]['text']) != observation['value']:
                problems.append(f'{key}: observation {identifier} disagrees with facts.json')
            if observation['value'] not in normalized(block['text']):
                problems.append(f'{key}: observation {identifier} outside its project')
            if observation['source_url'] not in block['links']:
                problems.append(f'{key}: observation {identifier} source missing')
    actual_ids = [n['attrs']['data-fact'] for p in pages.values() for n in p.nodes if 'data-fact' in n['attrs']]
    if sorted(actual_ids) != sorted(expected_ids) or len(expected_ids) != len(set(expected_ids)):
        problems.append('evidence IDs must appear exactly once, with no unknown facts')

    for rel, page in pages.items():
        for node in page.nodes:
            for attr in ('href', 'src'):
                href = node['attrs'].get(attr)
                if not href:
                    continue
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    continue
                target = ((root / rel).parent / unquote(url.path)).resolve() if url.path else (root / rel).resolve()
                if not target.is_relative_to(root.resolve()) or not target.is_file():
                    problems.append(f'{rel}: missing or out-of-root link {href}')
                elif url.fragment and target.suffix == '.html':
                    target_page = pages.get(str(target.relative_to(root))) or Page(target.read_text(encoding='utf-8'))
                    if not target_page.find('id', unquote(url.fragment)):
                        problems.append(f'{rel}: broken fragment {href}')
    return problems


def github(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'portfolio-evidence-check'}
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = f'Bearer {os.environ["GITHUB_TOKEN"]}'
    request = urllib.request.Request('https://api.github.com' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def check_remote(facts):
    problems = []
    for key, spec in facts['projects'].items():
        repo = spec['repo']
        try:
            if github(f'/repos/{repo}').get('private'):
                problems.append(f'{key}: source repository is private')
            commit = github(f'/repos/{repo}/commits/{spec["commit"]}')
            if commit['sha'] != spec['commit']:
                problems.append(f'{key}: source commit mismatch')
            runs = {}
            for observation in spec['observations']:
                if 'run_id' not in observation:
                    continue
                run_id = observation['run_id']
                if run_id not in runs:
                    runs[run_id] = github(f'/repos/{repo}/actions/runs/{run_id}')
                run = runs[run_id]
                job = github(f'/repos/{repo}/actions/jobs/{observation["job_id"]}')
                if run['head_sha'] != spec['commit'] or run['conclusion'] != 'success':
                    problems.append(f'{key}: CI run does not establish the pinned successful snapshot')
                if job['run_id'] != run_id or job['name'] != observation['job_name'] or job['conclusion'] != 'success' or job['html_url'] != observation['source_url']:
                    problems.append(f'{key}: job identity, source URL or result mismatch')
                if run['created_at'][:10] != observation['run_date']:
                    problems.append(f'{key}: run date mismatch')
        except (urllib.error.URLError, KeyError, ValueError) as error:
            problems.append(f'{key}: could not verify public evidence: {error}')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    args = parser.parse_args()
    facts = json.loads((ROOT / 'facts.json').read_text(encoding='utf-8'))
    problems = check_local(facts)
    if args.remote:
        problems += check_remote(facts)
    for problem in problems:
        print('DRIFT:', problem)
    if problems:
        return 1
    print(f'PASS: {len(facts["projects"])} projects; scoped facts, boundaries and local links verified.')
    if args.remote:
        print('PASS: public commits and successful CI job identities verified. Numeric results require log review.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
