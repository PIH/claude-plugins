"""Tests for ocl_release_check.py. No network. Run: python3 -I -m unittest discover -s <scripts dir> -p 'test_*.py'"""
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocl_release_check as rc  # noqa: E402

PIH, CIEL = rc.PIH, rc.CIEL


def concept(cid, uuid, names, version='1', retired=False):
    return {'id': cid, 'external_id': uuid, 'version': version, 'retired': retired, 'concept_class': 'Misc',
            'names': [{'name': n, 'locale': 'en', 'locale_preferred': i == 0, 'external_id': u}
                      for i, (n, u) in enumerate(names)]}


def mapping(mid, frm, map_type, to_code, to_source_url, to_concept_url=None, version='1', retired=False):
    return {'id': mid, 'from_concept_code': frm, 'map_type': map_type, 'to_concept_code': to_code,
            'to_source_url': to_source_url, 'to_concept_url': to_concept_url, 'version': version, 'retired': retired}


def self_map(mid, cid):
    return mapping(mid, cid, 'SAME-AS', cid, PIH, f'{PIH}concepts/{cid}/')


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = {}  # fake DB snapshot: name uuid -> (concept uuid, name, locale, voided)
        self._orig_db, self._orig_tok = rc.load_db_snapshot, rc.token
        rc.load_db_snapshot = lambda refresh=False: self.db
        rc.token = lambda: None  # no network: suggest() skips CIEL lookups

    def tearDown(self):
        rc.load_db_snapshot, rc.token = self._orig_db, self._orig_tok
        self.tmp.cleanup()

    def export(self, name, version, concepts, mappings, as_zip=False):
        d = {'id': version, 'concepts': concepts, 'mappings': mappings}
        path = os.path.join(self.tmp.name, name)
        if as_zip:
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('export.json', json.dumps(d))
        else:
            with open(path, 'w') as f:
                json.dump(d, f)
        return path

    def run_check(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = rc.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class NameUuids(Base):
    def test_clash_with_db_snapshot_is_an_error(self):
        self.db['NAME-U-1'] = ('OTHER-CONCEPT', 'Old name', 'en', True)
        e = self.export('e.json', '1.0', [concept('20001', 'C1', [('New', 'NAME-U-1')])], [self_map('m1', '20001')])
        code, out, _ = self.run_check('--export', e, '--checks', 'name-uuids', '--fail-on', 'error')
        self.assertEqual(code, 1)
        self.assertIn('name-clash', out)
        self.assertIn('(voided)', out)

    def test_same_concept_in_db_is_fine(self):
        self.db['NAME-U-1'] = ('C1', 'New', 'en', False)
        e = self.export('e.json', '1.0', [concept('20001', 'C1', [('New', 'NAME-U-1')])], [])
        code, out, _ = self.run_check('--export', e, '--checks', 'name-uuids', '--fail-on', 'error')
        self.assertEqual(code, 0)

    def test_handled_clash_is_only_a_warning(self):
        u = next(iter(rc.HANDLED_NAME_CLASHES))
        self.db[u] = ('OTHER', 'Old', 'en', True)
        e = self.export('e.json', '1.0', [concept('20001', 'C1', [('New', u)])], [])
        code, out, _ = self.run_check('--export', e, '--checks', 'name-uuids', '--fail-on', 'error')
        self.assertEqual(code, 0)
        self.assertIn('name-clash-handled', out)

    def test_same_name_uuid_on_two_concepts(self):
        e = self.export('e.json', '1.0', [concept('20001', 'C1', [('A', 'DUP')]), concept('20002', 'C2', [('B', 'DUP')])], [])
        code, out, _ = self.run_check('--export', e, '--checks', 'name-uuids', '--fail-on', 'error')
        self.assertEqual(code, 1)
        self.assertIn('dup-name-uuid', out)


class CloneMappings(Base):
    def test_external_code_swapped_for_pih_concept_is_an_error(self):
        icd = '/orgs/WHO/sources/ICD-10-WHO/'
        concepts = [concept('20001', 'C1', [('Lichen', 'N1')]), concept('10034', 'C2', [('LSC', 'N2')])]
        maps = [self_map('m0', '20001'), mapping('m1', '20001', 'BROADER-THAN', '10034', icd, f'{PIH}concepts/10034/'),
                mapping('m2', '10034', 'SAME-AS', 'L28.0', icd, f'{icd}concepts/L28.0/')]
        e = self.export('e.json', '1.0', concepts, maps)
        code, out, _ = self.run_check('--export', e, '--checks', 'clone-mappings', '--fail-on', 'error')
        self.assertEqual(code, 1)
        self.assertIn('clone-mappings/external', out)
        self.assertIn('L28.0', out)  # the lost code is reported

    def test_self_and_missing_self_mapping_are_warnings(self):
        e = self.export('e.json', '1.0', [concept('20001', 'C1', [('X', 'N1')])],
                        [mapping('m1', '20001', 'SAME-AS', '20001', CIEL, f'{PIH}concepts/20001/')])
        code, out, _ = self.run_check('--export', e, '--checks', 'clone-mappings', '--fail-on', 'error')
        self.assertEqual(code, 0)
        self.assertIn('clone-mappings/self', out)
        self.assertIn('clone-mappings/no-self-mapping', out)
        code, _, _ = self.run_check('--export', e, '--checks', 'clone-mappings', '--fail-on', 'warning')
        self.assertEqual(code, 1)


class BaselineAndOutput(Base):
    def test_baseline_limits_scope_to_changed_concepts(self):
        self.db['OLD-CLASH'] = ('OTHER', 'Old', 'en', True)
        unchanged = concept('20001', 'C1', [('Known problem', 'OLD-CLASH')])
        old = self.export('old.json', '1.0', [unchanged], [])
        new = self.export('new.zip', '1.1', [unchanged, concept('20002', 'C2', [('New one', 'N2')])],
                          [self_map('m2', '20002')], as_zip=True)
        md = os.path.join(self.tmp.name, 'summary.md')
        code, out, _ = self.run_check('--export', new, '--baseline', old, '--fail-on', 'error', '--summary-md', md)
        self.assertEqual(code, 0, out)  # 20001's clash is old, so not checked
        self.assertIn('Checked 1 concept(s)', out)
        with open(md) as f:
            self.assertIn('no errors', f.read())

    def test_changed_mapping_brings_its_concept_into_scope(self):
        c = concept('20001', 'C1', [('X', 'N1')])
        old = self.export('old.json', '1.0', [c], [self_map('m1', '20001')])
        new = self.export('new.json', '1.1', [c], [self_map('m1', '20001'), self_map('m2', '20001')])
        _, out, _ = self.run_check('--export', new, '--baseline', old)
        self.assertIn('Checked 1 concept(s)', out)

    def test_errors_and_usage(self):
        code, _, err = self.run_check('--export', os.path.join(self.tmp.name, 'missing.json'))
        self.assertEqual(code, 2)
        self.assertIn('could not run', err)
        with self.assertRaises(SystemExit):
            self.run_check('--export', 'x.json', '--checks', 'no-such-check')
        code, out, _ = self.run_check('--list-checks')
        self.assertEqual(code, 0)
        for name in rc.CHECKS:
            self.assertIn(name, out)


if __name__ == '__main__':
    unittest.main()
