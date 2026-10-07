"""Regression tests for evidence drift. Uses isolated copies, never edits the site."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_facts


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path.home() / ".aki/tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.facts = json.loads((check_facts.ROOT / 'facts.json').read_text())
        for name in self.facts['site']['files'] + ['styles.css', 'favicon.svg', 'site.webmanifest']:
            shutil.copy(check_facts.ROOT / name, self.root / name)
        shutil.copytree(check_facts.ROOT / 'assets', self.root / 'assets')

    def mutate(self, name, old, new):
        path = self.root / name
        content = path.read_text()
        self.assertIn(old, content)
        path.write_text(content.replace(old, new, 1))

    def assert_drift(self, fragment):
        self.assertTrue(any(fragment in p for p in check_facts.check_local(self.facts, self.root)))

    def test_current_site(self):
        self.assertEqual([], check_facts.check_local(self.facts, self.root))

    def test_symlinked_root(self):
        alias = self.root / 'site-alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertEqual([], check_facts.check_local(self.facts, alias))

    def test_wrong_count(self):
        self.mutate('evidence.html', '518 passed', '999 passed')
        self.assert_drift('disagrees')

    def test_missing_boundary(self):
        self.mutate('evidence.html', self.facts['projects']['cloudscale']['boundary'], 'Guaranteed availability.')
        self.assert_drift('boundary missing')

    def test_unpinned_source(self):
        self.mutate('evidence.html', '/tree/26a7047de94266d97e9acc520e575b127030f1b2', '/tree/main')
        self.assert_drift('pinned source')

    def test_missing_evidence_link(self):
        self.mutate('evidence.html', self.facts['projects']['cloudscale']['observations'][0]['source_url'], 'https://example.org/')
        self.assert_drift('source missing')

    def test_missing_pdf(self):
        (self.root / 'assets/Amit_Singh_Backend_Resume.pdf').unlink()
        self.assert_drift('missing or out-of-root link')

    def test_broken_fragment(self):
        self.mutate('index.html', 'evidence.html#cloudscale', 'evidence.html#does-not-exist')
        self.assert_drift('broken fragment')

    def test_forbidden_absolute(self):
        self.mutate('index.html', 'Backend systems.', 'Never double-executes')
        self.assert_drift('forbidden phrase')

    def test_missing_project(self):
        self.mutate('index.html', 'data-project="cloudscale"', 'data-project="unknown"')
        self.assert_drift('expected 1 project block')

    def test_duplicate_fact(self):
        self.mutate('evidence.html', '</main>', '<span data-fact="cloudscale-1">518 passed, 5 skipped</span></main>')
        self.assert_drift('exactly once')

    def test_counts_stay_off_homepage(self):
        self.mutate('index.html', 'Backend systems.', '518 tests')
        self.assert_drift('move volatile test counts')

    def test_remote_rejects_wrong_commit(self):
        facts = {'projects': {'cloudscale': self.facts['projects']['cloudscale']}}
        def github(path):
            if '/commits/' in path:
                return {'sha': '0' * 40}
            if '/actions/runs/' in path:
                return {'head_sha': '0' * 40, 'conclusion': 'success', 'created_at': '2026-09-20'}
            if '/actions/jobs/' in path:
                o = next(o for o in facts['projects']['cloudscale']['observations'] if str(o['job_id']) in path)
                return {'run_id': o['run_id'], 'name': o['job_name'], 'conclusion': 'success', 'html_url': o['source_url']}
            return {'private': False}
        with patch.object(check_facts, 'github', github):
            self.assertTrue(any('commit mismatch' in p for p in check_facts.check_remote(facts)))


if __name__ == '__main__':
    unittest.main()
