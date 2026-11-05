#!/usr/bin/env python3
"""Find mappings in the PIH source that OCL's $clone rewrote incorrectly. Read-only.

$clone copies each CIEL mapping onto the new PIH concept. If the mapping's target is
something PIH already has a SAME-AS mapping to, $clone points the copy at that PIH
concept instead. It updates the code, the concept URL and the source name, but leaves
`to_source_url` (and `from_source_url`) pointing at the original source. That gives:

  self      CIEL's own "SAME-AS CIEL:<ciel id>" becomes "CIEL:<PIH id>" pointing at the
            concept itself. OpenMRS reads it as SAME-AS PIH:<id> (the usual self-mapping),
            so it's only wrong in OCL.
  internal  Q-AND-A / CONCEPT-SET / other concept-to-concept mappings now point at the
            right PIH concept, but `to_source_url` still says CIEL. Cosmetic.
  external  An ICD-10 / LOINC / ... mapping is rewritten to point at whichever PIH concept
            is SAME-AS that code. The real external code is LOST, and OpenMRS gets e.g.
            "BROADER-THAN PIH:10034" instead of "BROADER-THAN ICD-10-WHO:L28.0".

It also reports concepts >= 20000 that have no proper SAME-AS PIH:<id> self-mapping.

With --name-uuids it also checks concept NAME uuids. Clones keep CIEL's name uuids
(…BBBB). PIH servers can already hold one of those uuids, e.g. on a name voided years
ago, and then the OpenMRS import fails with "Duplicate entry … for key
'concept_name_uuid_index'" (UHM-9656). OCL can't see voided server names, so this compares
against a snapshot of a PIH database: the pihcore test DB (openmrs.sql, from 2023). It's
downloaded once and cached in ~/.cache/ocl/. It reports:
  name-clash     a name uuid that the snapshot has on a DIFFERENT concept (active or voided)
  dup-name-uuid  the same name uuid on two PIH concepts in what's being checked

Usage:
  check_clone_mappings.py --concept 21768 21760 ...   # live, from the OCL API
  check_clone_mappings.py --export export.json        # a whole released export
  add --name-uuids to also check name uuids, and --json for machine-readable output.

For "external" findings it looks up the CIEL source concept and suggests the correct code.
The token is read from ~/.config/ocl/token. Run with `python3 -I`.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API = 'https://api.openconceptlab.org'
PIH = '/orgs/PIH/sources/PIH/'
CIEL = '/orgs/CIEL/sources/CIEL/'
INTERNAL_TYPES = {'Q-AND-A', 'CONCEPT-SET'}
DB_SNAPSHOT_URL = ('https://raw.githubusercontent.com/PIH/openmrs-module-pihcore/master/'
                   'api/src/test/resources/event/openmrs.sql')
DB_SNAPSHOT_CACHE = os.path.expanduser('~/.cache/ocl/pihcore-openmrs.sql')
UUID_RE = re.compile(r'[0-9A-Za-z-]{36}')
_cache = {}


def get(path):
    if path not in _cache:
        with open(os.path.expanduser('~/.config/ocl/token')) as f:
            tok = f.read().strip()
        req = urllib.request.Request(API + path, headers={'Authorization': 'Token ' + tok})
        with urllib.request.urlopen(req) as r:
            _cache[path] = json.load(r)
    return _cache[path]


def source_of(url):
    m = re.match(r'(/orgs?/[^/]+/sources/[^/]+/)', url or '')
    return m.group(1) if m else None


def short(url):
    return (url or '').rstrip('/').split('/')[-1]


def concept_path(cid, extra=''):
    return f'{PIH}concepts/{urllib.parse.quote(cid)}/?includeMappings=true{extra}'


def load_live(ids):
    concepts, mappings = {}, []
    for cid in ids:
        c = get(concept_path(cid, '&verbose=true'))
        concepts[cid] = c
        mappings.extend(c.get('mappings') or [])
    return concepts, mappings


def changed_since(version):
    """PIH concept ids changed (themselves or via one of their mappings) after release `version`."""
    cutoff = get(f'{PIH}{urllib.parse.quote(version)}/')['created_on']
    ids = set()
    for kind, key in (('concepts', 'id'), ('mappings', 'from_concept_code')):
        page = 1
        while True:
            items = get(f'{PIH}{kind}/?sortDesc=last_update&limit=200&page={page}')
            fresh = [i for i in items if (i.get('version_updated_on') or '') > cutoff]
            ids.update(i[key] for i in fresh)
            if len(fresh) < len(items) or len(items) < 200:
                break
            page += 1
    return cutoff, sorted(ids, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x))


def load_db_snapshot(refresh=False):
    """{name_uuid: (db_concept_uuid, name, locale, voided)} from the pihcore test DB dump."""
    if refresh or not os.path.exists(DB_SNAPSHOT_CACHE):
        os.makedirs(os.path.dirname(DB_SNAPSHOT_CACHE), exist_ok=True)
        print(f'Downloading PIH DB snapshot to {DB_SNAPSHOT_CACHE} (about 33 MB)…', file=sys.stderr)
        urllib.request.urlretrieve(DB_SNAPSHOT_URL, DB_SNAPSHOT_CACHE)
    with open(DB_SNAPSHOT_CACHE, encoding='utf-8', errors='replace') as f:
        sql = f.read()

    def rows(table):
        for blk in re.findall(r'INSERT INTO `%s` VALUES (.*?);\n' % table, sql, re.S):
            cur, depth, quoted, esc = '', 0, False, False
            for ch in blk:
                if quoted:
                    cur += ch
                    if esc:
                        esc = False
                    elif ch == '\\':
                        esc = True
                    elif ch == "'":
                        quoted = False
                    continue
                if ch == "'":
                    quoted = True
                    cur += ch
                elif ch == '(' and depth == 0:
                    depth, cur = 1, ''
                elif ch == ')' and depth == 1:
                    depth = 0
                    yield next(csv.reader(io.StringIO(cur), quotechar="'", escapechar='\\'))
                elif depth:
                    cur += ch

    concept_uuid = {r[0]: r[-1] for r in rows('concept')}
    names = {}
    # concept_name columns: concept_name_id, concept_id, name, locale, locale_preferred, creator,
    # date_created, concept_name_type, voided, voided_by, date_voided, void_reason, uuid, ...
    for r in rows('concept_name'):
        uuid = next((x for x in r[12:] if UUID_RE.fullmatch(x or '')), None)
        if uuid:
            names[uuid] = (concept_uuid.get(r[1]), r[2], r[3], r[8] == '1')
    return names


def check_name_uuids(concepts, db_names):
    findings, seen = [], {}
    for cid, c in concepts.items():
        for n in c.get('names') or []:
            u = n.get('external_id')
            if not u:
                continue
            if u in seen and seen[u] != cid:
                findings.append({'kind': 'dup-name-uuid', 'concept': cid, 'other_concept': seen[u],
                                 'name': n['name'], 'name_uuid': u})
            seen.setdefault(u, cid)
            hit = db_names.get(u)
            if hit and hit[0] != c.get('external_id'):
                findings.append({'kind': 'name-clash', 'concept': cid, 'name': n['name'], 'locale': n.get('locale'),
                                 'name_uuid': u, 'db_concept_uuid': hit[0], 'db_name': hit[1],
                                 'db_voided': hit[3]})
    return findings


# OCL bugs these checks work around. Once OCL fixes them, the matching checks (and the skill's
# guidance about them) can probably go. The fix watch below spots signs of that.
OCL_ISSUES = {
    3012: 'copied mappings keep the original from_source_url',
    3013: 'mappings retargeted to an equivalent PIH concept (incl. CIEL self-mapping, external codes)',
}
FIX_WATCH_SINCE = '2026-11-05'   # only clones made after the issues were filed tell us about a fix
CLONE_WINDOW_SECONDS = 300       # a clone creates its concept and mappings within moments of each other


def _ts(s):
    from datetime import datetime
    return datetime.fromisoformat((s or '').replace('Z', '+00:00')) if s else None


def ocl_issue_states():
    """{issue number: (state, closed_at)} from GitHub's public API; {} if it can't be reached."""
    states = {}
    for n in OCL_ISSUES:
        try:
            req = urllib.request.Request(f'https://api.github.com/repos/OpenConceptLab/ocl_issues/issues/{n}',
                                         headers={'Accept': 'application/vnd.github+json'})
            with urllib.request.urlopen(req, timeout=10) as r:
                d = json.load(r)
            states[n] = (d.get('state'), (d.get('closed_at') or '')[:10])
        except Exception:  # offline, rate-limited… the watch is best-effort
            pass
    return states


def fix_watch(concepts, by_from, findings, since=FIX_WATCH_SINCE):
    """Look at clones made since `since` for signs that OCL has fixed the clone bugs."""
    self_bug = {f['concept'] for f in findings if f['kind'] == 'self'}
    ext_bug = {f['concept'] for f in findings if f['kind'] == 'external'}
    clones, ev = [], {'3012': set(), '3013': set(), 'name_uuids': set()}
    for cid, c in concepts.items():
        created = _ts(c.get('created_on'))
        if not created or c['created_on'][:10] < since:
            continue
        near = [m for m in by_from.get(cid, [])
                if m.get('created_on') and abs((_ts(m['created_on']) - created).total_seconds()) < CLONE_WINDOW_SECONDS]
        equiv = [m for m in near if m['map_type'] == 'SAME-AS' and source_of(m.get('to_concept_url')) == CIEL
                 and not m.get('to_source_url')]
        if not equiv:
            continue  # not a $clone
        clones.append(cid)
        copied = [m for m in near if m not in equiv]
        if copied:
            stale = any(m.get('from_source_url') not in (None, PIH) for m in copied)
            ev['3012'].add('still happening' if stale else 'looks fixed')
            ev['3013'].add('still happening' if (cid in self_bug or cid in ext_bug) else 'looks fixed')
        ciel_style = any((n.get('external_id') or '').endswith('BBBBBBBB') for n in c.get('names') or [])
        ev['name_uuids'].add('still CIEL name uuids' if ciel_style else 'fresh name uuids')
    return {'kind': 'ocl-fix-watch', 'clones_checked': clones, 'since': since,
            'evidence': {k: sorted(v) for k, v in ev.items()}, 'issues': ocl_issue_states()}


def print_fix_watch(w):
    issues = w['issues']
    closed = [n for n, (state, _) in issues.items() if state == 'closed']
    signs = [k for k, v in w['evidence'].items() if v == ['looks fixed'] or v == ['fresh name uuids']]
    if not (w['clones_checked'] or closed):
        return
    print()
    print('OCL fix watch:')
    for n, why in OCL_ISSUES.items():
        state = issues.get(n)
        print(f"  ocl_issues#{n} ({why}): " + (f"{state[0]}" + (f" on {state[1]}" if state[1] else '') if state
                                                else 'state unknown (GitHub not reachable)'))
    if w['clones_checked']:
        print(f"  Clones made since {w['since']} that were checked: {' '.join(w['clones_checked'])}")
        for k, v in w['evidence'].items():
            if v:
                print(f"    {k}: {', '.join(v)}")
    if closed or signs:
        said = {'3012': 'new clones suggest ocl_issues#3012 is fixed',
                '3013': 'new clones suggest ocl_issues#3013 is fixed',
                'name_uuids': 'new clones get fresh name uuids instead of keeping CIEL\'s'}
        print('  POSSIBLE OCL FIX: ' + '; '.join(
            [f'ocl_issues#{n} is closed' for n in closed] + [said[k] for k in signs]) + '.')
        print('  Suggest to the user (do not do it unprompted) reviewing whether the skill\'s clone-bug guidance '
              'and the matching checks are still needed.')


def load_export(path):
    with open(path) as f:
        d = json.load(f)
    return {c['id']: c for c in d['concepts']}, d['mappings']


def mappings_of(cid, by_from, live):
    if cid in by_from or not live:
        return by_from.get(cid, [])
    return get(concept_path(cid)).get('mappings') or []


def name_of(c):
    names = (c or {}).get('names') or []
    pref = [n['name'] for n in names if n.get('locale') == 'en' and n.get('locale_preferred')]
    return (pref or [n['name'] for n in names] or [''])[0]


def suggest(m, by_from, live):
    """Correct external code: what the CIEL source concept maps to, with the same map type and source."""
    tgt = m['to_source_url']
    ciel_ids = [x['to_concept_code'] for x in by_from.get(m['from_concept_code'], [])
                if x['map_type'] == 'SAME-AS' and source_of(x.get('to_concept_url')) == CIEL and not x.get('retired')]
    codes = []
    for ciel_id in ciel_ids:
        for x in get(f'{CIEL}concepts/{urllib.parse.quote(ciel_id)}/?includeMappings=true').get('mappings') or []:
            if x.get('to_source_url') == tgt and x['map_type'] == m['map_type'] and not x.get('retired'):
                codes.append(x['to_concept_code'])
    # Fallback: the code the wrongly targeted PIH concept is SAME-AS in that source.
    via = [x['to_concept_code'] for x in mappings_of(m['to_concept_code'], by_from, live)
           if x['map_type'] == 'SAME-AS' and x.get('to_source_url') == tgt and not x.get('retired')]
    return ciel_ids, sorted(set(codes)), sorted(set(via))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--concept', nargs='+', metavar='PIH_ID')
    g.add_argument('--export', metavar='EXPORT_JSON')
    g.add_argument('--unreleased', action='store_true',
                   help='check every PIH concept changed since the latest release (a pre-release check)')
    p.add_argument('--since', metavar='VERSION',
                   help='with --unreleased: compare against this release instead of the latest, e.g. 1.8.46')
    p.add_argument('--name-uuids', action='store_true',
                   help='also check name uuids against a PIH DB snapshot (implied by --unreleased)')
    p.add_argument('--refresh-snapshot', action='store_true', help='re-download the PIH DB snapshot')
    p.add_argument('--fix-watch-since', default=FIX_WATCH_SINCE, metavar='YYYY-MM-DD',
                   help=argparse.SUPPRESS)  # for testing the fix watch on older clones
    p.add_argument('--json', action='store_true')
    a = p.parse_args()

    if a.unreleased:
        version = a.since or get(f'{PIH}latest/')['id']
        cutoff, ids = changed_since(version)
        print(f'Checking {len(ids)} PIH concept(s) changed since {version} ({cutoff[:16]}Z): '
              f'{" ".join(ids) or "(none)"}', file=sys.stderr)
        a.concept, a.name_uuids = ids, True
    live = a.concept is not None
    concepts, mappings = load_live(a.concept) if live else load_export(a.export)
    by_from = {}
    for m in mappings:
        by_from.setdefault(m['from_concept_code'], []).append(m)

    findings = []
    for m in mappings:
        if m.get('retired'):
            continue
        tsu, tcu = m.get('to_source_url'), m.get('to_concept_url')
        if not (tsu and tcu) or source_of(tcu) != PIH or tsu == PIH:
            continue
        f = {'mapping': m['id'], 'concept': m['from_concept_code'], 'map_type': m['map_type'],
             'to_source_url': tsu, 'to_concept_code': m['to_concept_code']}
        if m['to_concept_code'] == m['from_concept_code']:
            f['kind'] = 'self'
        elif tsu == CIEL or m['map_type'] in INTERNAL_TYPES:
            f['kind'] = 'internal'
        else:
            f['kind'] = 'external'
            f['ciel_ids'], f['correct_from_ciel'], f['pih_target_sameas'] = suggest(m, by_from, live)
            f['pih_target_name'] = name_of(concepts.get(m['to_concept_code']))
        findings.append(f)

    bogus_self = {f['concept'] for f in findings if f['kind'] == 'self'}
    for cid, c in concepts.items():
        if not cid.isdigit() or int(cid) < 20000 or c.get('retired'):
            continue
        has_self = any(x['map_type'] == 'SAME-AS' and x.get('to_source_url') == PIH and x['to_concept_code'] == cid
                       and not x.get('retired') for x in by_from.get(cid, []))
        if not has_self:
            findings.append({'kind': 'no-self-mapping', 'concept': cid, 'name': name_of(c),
                             'has_bogus_self': cid in bogus_self})

    if a.name_uuids:
        findings.extend(check_name_uuids(concepts, load_db_snapshot(a.refresh_snapshot)))

    watch = fix_watch(concepts, by_from, findings, a.fix_watch_since) if live else None

    if a.json:
        json.dump(findings + ([watch] if watch else []), sys.stdout, indent=1)
        print()
        return

    counts = {}
    for f in findings:
        counts[f['kind']] = counts.get(f['kind'], 0) + 1
    print('Summary:', ', '.join(f'{k}={v}' for k, v in sorted(counts.items())) or 'no problems found')
    order = {'name-clash': 0, 'dup-name-uuid': 1, 'external': 2, 'self': 3, 'no-self-mapping': 4, 'internal': 5}
    for f in sorted(findings, key=lambda f: (order[f['kind']], int(f['concept']) if f['concept'].isdigit() else 0)):
        if f['kind'] == 'name-clash':
            print(f"NAME-CLASH PIH {f['concept']} name '{f['name']}' ({f['locale']}) uuid {f['name_uuid']} is already on "
                  f"another concept ({f['db_concept_uuid']}) in PIH databases, as '{f['db_name']}'"
                  f"{' (voided)' if f['db_voided'] else ''}. The OpenMRS import WILL FAIL.")
        elif f['kind'] == 'dup-name-uuid':
            print(f"DUP-NAME  PIH {f['concept']} name '{f['name']}' uuid {f['name_uuid']} is also used by PIH "
                  f"{f['other_concept']}. The OpenMRS import will fail.")
        elif f['kind'] == 'external':
            print(f"EXTERNAL  mapping {f['mapping']}: PIH {f['concept']} {f['map_type']} {short(f['to_source_url'])} "
                  f"rewritten to PIH {f['to_concept_code']} {f['pih_target_name']}; "
                  f"CIEL {'/'.join(f['ciel_ids']) or '?'} has {'/'.join(f['correct_from_ciel']) or '(none)'}; "
                  f"PIH {f['to_concept_code']} is SAME-AS {'/'.join(f['pih_target_sameas']) or '(none)'}")
        elif f['kind'] == 'self':
            print(f"SELF      mapping {f['mapping']}: PIH {f['concept']} SAME-AS "
                  f"{short(f['to_source_url'])}:{f['to_concept_code']} (target is the concept itself; source should be PIH)")
        elif f['kind'] == 'internal':
            print(f"INTERNAL  mapping {f['mapping']}: PIH {f['concept']} {f['map_type']} -> PIH {f['to_concept_code']} "
                  f"(to_source_url says {short(f['to_source_url'])})")
        else:
            print(f"NO-SELF   PIH {f['concept']} {f['name']}"
                  + (' (has the bogus CIEL self-mapping instead)' if f['has_bogus_self'] else ''))

    if watch:
        print_fix_watch(watch)


if __name__ == '__main__':
    main()
