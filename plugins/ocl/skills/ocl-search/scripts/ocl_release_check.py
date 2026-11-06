#!/usr/bin/env python3
"""PIH OCL release check: find problems in the PIH source that would break, or quietly damage, OpenMRS. Read-only.

It runs a set of named checks, each written for a problem we've actually hit. To add a check, write a function
that returns findings and register it in CHECKS. To retire one (e.g. once OCL fixes the bug behind it), remove it
from CHECKS. Each finding has a severity:
  error    the OpenMRS import will fail, or data reaching servers will be wrong. Fix before releasing / merging.
  warning  wrong or odd in OCL, but harmless to servers. Report only.

Checks (see --list-checks):
  name-uuids      UHM-9656. Concept name uuids already used by another concept in PIH databases (incl. voided names,
                  which OCL can't see), or by two PIH concepts. Compared against a PIH database snapshot: the pihcore
                  test DB (openmrs.sql, from 2023), downloaded once and cached in ~/.cache/ocl/.
  clone-mappings  UHM-9636, OCL ocl_issues#3012/#3013. Mappings that OCL's $clone rewrote: external codes (ICD-10,
                  LOINC...) replaced by a PIH concept (error); CIEL self-mappings and answer/set mappings with stale
                  source urls, and concepts >= 20000 with no SAME-AS PIH self-mapping (warnings). On live runs it
                  also watches for OCL fixing these bugs ("OCL fix watch").

What to check (pick one):
  --unreleased [--since VERSION]   everything changed in the live PIH source since the latest (or given) release.
                                   This is the PRE-RELEASE check.
  --export NEW [--baseline OLD]    a released export (export.json or the OCL zip). With --baseline, only concepts
                                   that changed between OLD and NEW are checked. This is what CI runs on a new
                                   export before it goes into the distro.
  --concept ID [ID ...]            specific PIH concepts, live (e.g. right after cloning).

Output and exit status:
  --fail-on error|warning|never    exit 1 if there's a finding at or above this severity (default: never).
  --summary-md FILE                also write a Markdown summary (for a PR description or a GitHub job summary).
  --json                           machine-readable findings instead of text.
  Exit status: 0 = OK, 1 = findings at or above --fail-on, 2 = the check couldn't run.

The OCL token is read from $OCL_API_TOKEN, else ~/.config/ocl/token. Run with `python3 -I`.
This script is also run by the PIH/pihemr "Update OCL export" GitHub Action, which downloads it from this repo's
main branch. Keep these options and exit statuses working, or update that workflow at the same time.
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
import zipfile

API = 'https://api.openconceptlab.org'
PIH = '/orgs/PIH/sources/PIH/'
CIEL = '/orgs/CIEL/sources/CIEL/'
INTERNAL_TYPES = {'Q-AND-A', 'CONCEPT-SET'}
DB_SNAPSHOT_URL = ('https://raw.githubusercontent.com/PIH/openmrs-module-pihcore/master/'
                   'api/src/test/resources/event/openmrs.sql')
DB_SNAPSHOT_CACHE = os.path.expanduser('~/.cache/ocl/pihcore-openmrs.sql')
UUID_RE = re.compile(r'[0-9A-Za-z-]{36}')
SEVERITY = {'warning': 1, 'error': 2}
_cache = {}


# ---------------------------------------------------------------- OCL access

def token():
    tok = os.environ.get('OCL_API_TOKEN')
    if tok:
        return tok.strip()
    path = os.path.expanduser('~/.config/ocl/token')
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return None


def get(path):
    if path not in _cache:
        tok = token()
        if not tok:
            raise RuntimeError('No OCL token: set OCL_API_TOKEN or create ~/.config/ocl/token (/ocl:setup)')
        req = urllib.request.Request(API + path, headers={'Authorization': 'Token ' + tok})
        with urllib.request.urlopen(req, timeout=60) as r:
            _cache[path] = json.load(r)
    return _cache[path]


def source_of(url):
    m = re.match(r'(/orgs?/[^/]+/sources/[^/]+/)', url or '')
    return m.group(1) if m else None


def short(url):
    return (url or '').rstrip('/').split('/')[-1]


def name_of(c):
    names = (c or {}).get('names') or []
    pref = [n['name'] for n in names if n.get('locale') == 'en' and n.get('locale_preferred')]
    return (pref or [n['name'] for n in names] or [''])[0]


def sort_key(cid):
    return (not str(cid).isdigit(), int(cid) if str(cid).isdigit() else 0, str(cid))


# ---------------------------------------------------------------- loading what to check

class Context:
    """What's being checked. `concepts`/`mappings` hold everything loaded; `scope` is the concept ids to report on."""

    def __init__(self, concepts, mappings, scope, live, label, refresh_snapshot=False):
        self.concepts, self.mappings, self.scope, self.live, self.label = concepts, mappings, set(scope), live, label
        self.refresh_snapshot = refresh_snapshot
        self.by_from = {}
        for m in mappings:
            self.by_from.setdefault(m['from_concept_code'], []).append(m)
        self.extra_reports = []  # extra sections a check wants printed (e.g. the OCL fix watch)

    def mappings_of(self, cid):
        if cid in self.by_from or not self.live:
            return self.by_from.get(cid, [])
        return get(f'{PIH}concepts/{urllib.parse.quote(cid)}/?includeMappings=true').get('mappings') or []


def load_live(ids, label, refresh):
    concepts, mappings = {}, []
    for cid in ids:
        c = get(f'{PIH}concepts/{urllib.parse.quote(cid)}/?includeMappings=true&verbose=true')
        concepts[cid] = c
        mappings.extend(m for m in c.get('mappings') or [] if m['from_concept_code'] == cid)
    return Context(concepts, mappings, ids, True, label, refresh)


def changed_since(version):
    """PIH concept ids changed (themselves, or via one of their mappings) after release `version`."""
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
    return cutoff, sorted(ids, key=sort_key)


def read_export(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.endswith('.json'))
            return json.loads(z.read(name))
    with open(path) as f:
        return json.load(f)


def load_export(path, baseline, refresh):
    d = read_export(path)
    concepts = {c['id']: c for c in d['concepts']}
    scope = set(concepts)
    label = f"export {d.get('id', '?')}"
    if baseline:
        b = read_export(baseline)
        old_c = {c['id']: (c.get('version'), c.get('retired')) for c in b['concepts']}
        old_m = {m['id']: (m.get('version'), m.get('retired')) for m in b['mappings']}
        scope = {cid for cid, c in concepts.items() if old_c.get(cid) != (c.get('version'), c.get('retired'))}
        scope |= {m['from_concept_code'] for m in d['mappings'] if old_m.get(m['id']) != (m.get('version'), m.get('retired'))}
        label += f" (concepts changed since {b.get('id', '?')})"
    return Context(concepts, d['mappings'], scope, False, label, refresh), d.get('id')


# ---------------------------------------------------------------- check: name-uuids

def load_db_snapshot(refresh=False):
    """{name_uuid: (db_concept_uuid, name, locale, voided)} from the pihcore test DB dump."""
    if refresh or not os.path.exists(DB_SNAPSHOT_CACHE):
        os.makedirs(os.path.dirname(DB_SNAPSHOT_CACHE), exist_ok=True)
        print(f'Downloading PIH DB snapshot to {DB_SNAPSHOT_CACHE} (about 33 MB)...', file=sys.stderr)
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


# Clashes with the DB snapshot that servers no longer have, because a distro change frees the uuid first.
# These are reported as warnings, with the reason. Add an entry when you fix a clash that way.
HANDLED_NAME_CLASHES = {
    '7159BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB':
        'freed on servers by pihemr liquibase changeset 20261105-free-pas-name-uuid-for-ocl-import (UHM-9656)',
}


def check_name_uuids(ctx):
    db = load_db_snapshot(ctx.refresh_snapshot)
    owner = {}  # name uuid -> concept id, across everything loaded
    for cid, c in ctx.concepts.items():
        for n in c.get('names') or []:
            if n.get('external_id'):
                owner.setdefault(n['external_id'], set()).add(cid)
    findings = []
    for cid in sorted(ctx.scope, key=sort_key):
        c = ctx.concepts.get(cid)
        if not c:
            continue
        for n in c.get('names') or []:
            u = n.get('external_id')
            if not u:
                continue
            others = sorted(owner.get(u, set()) - {cid}, key=sort_key)
            if others:
                findings.append({'check': 'name-uuids', 'kind': 'dup-name-uuid', 'severity': 'error', 'concept': cid,
                                 'message': f"PIH {cid} name '{n['name']}' uuid {u} is also used by PIH {', '.join(others)}. "
                                            'The OpenMRS import will fail.'})
            hit = db.get(u)
            if hit and hit[0] != c.get('external_id'):
                where = (f"PIH {cid} name '{n['name']}' ({n.get('locale')}) uuid {u} is already on another concept "
                         f"({hit[0]}) in PIH databases, as '{hit[1]}'{' (voided)' if hit[3] else ''}.")
                if u in HANDLED_NAME_CLASHES:
                    findings.append({'check': 'name-uuids', 'kind': 'name-clash-handled', 'severity': 'warning',
                                     'concept': cid, 'message': f'{where} Handled: {HANDLED_NAME_CLASHES[u]}.'})
                else:
                    findings.append({'check': 'name-uuids', 'kind': 'name-clash', 'severity': 'error', 'concept': cid,
                                     'message': f'{where} The OpenMRS import WILL FAIL.'})
    return findings


# ---------------------------------------------------------------- check: clone-mappings

OCL_ISSUES = {
    3012: 'copied mappings keep the original from_source_url',
    3013: 'mappings retargeted to an equivalent PIH concept (incl. CIEL self-mapping, external codes)',
}
FIX_WATCH_SINCE = '2026-11-05'   # only clones made after the issues were filed tell us about a fix
CLONE_WINDOW_SECONDS = 300       # a clone creates its concept and mappings within moments of each other


def suggest(ctx, m):
    """For a corrupted external mapping: CIEL's current code, and the code the swapped-in PIH concept is SAME-AS."""
    tgt = m['to_source_url']
    ciel_ids = [x['to_concept_code'] for x in ctx.mappings_of(m['from_concept_code'])
                if x['map_type'] == 'SAME-AS' and source_of(x.get('to_concept_url')) == CIEL and not x.get('retired')]
    codes = []
    if token():
        for ciel_id in ciel_ids:
            try:
                for x in get(f'{CIEL}concepts/{urllib.parse.quote(ciel_id)}/?includeMappings=true').get('mappings') or []:
                    if x.get('to_source_url') == tgt and x['map_type'] == m['map_type'] and not x.get('retired'):
                        codes.append(x['to_concept_code'])
            except Exception:
                pass
    via = [x['to_concept_code'] for x in ctx.mappings_of(m['to_concept_code'])
           if x['map_type'] == 'SAME-AS' and x.get('to_source_url') == tgt and not x.get('retired')]
    return ciel_ids, sorted(set(codes)), sorted(set(via))


def check_clone_mappings(ctx):
    findings = []
    for m in ctx.mappings:
        if m.get('retired') or m['from_concept_code'] not in ctx.scope:
            continue
        tsu, tcu = m.get('to_source_url'), m.get('to_concept_url')
        if not (tsu and tcu) or source_of(tcu) != PIH or tsu == PIH:
            continue
        cid = m['from_concept_code']
        f = {'check': 'clone-mappings', 'concept': cid, 'mapping': m['id']}
        if m['to_concept_code'] == cid:
            f.update(kind='self', severity='warning',
                     message=f"mapping {m['id']}: PIH {cid} SAME-AS {short(tsu)}:{cid} (points at itself; source should be PIH)")
        elif tsu == CIEL or m['map_type'] in INTERNAL_TYPES:
            f.update(kind='internal', severity='warning',
                     message=f"mapping {m['id']}: PIH {cid} {m['map_type']} -> PIH {m['to_concept_code']} "
                             f"(to_source_url says {short(tsu)})")
        else:
            ciel_ids, now, lost = suggest(ctx, m)
            f.update(kind='external', severity='error',
                     message=f"mapping {m['id']}: PIH {cid} {m['map_type']} {short(tsu)} was rewritten to PIH "
                             f"{m['to_concept_code']} {name_of(ctx.concepts.get(m['to_concept_code']))}; the {short(tsu)} "
                             f"code is lost. Lost code: {'/'.join(lost) or '?'}; CIEL {'/'.join(ciel_ids) or '?'} today: "
                             f"{'/'.join(now) or '(none)'}")
        findings.append(f)
    bogus_self = {f['concept'] for f in findings if f['kind'] == 'self'}
    for cid in sorted(ctx.scope, key=sort_key):
        c = ctx.concepts.get(cid)
        if not c or not cid.isdigit() or int(cid) < 20000 or c.get('retired'):
            continue
        if not any(x['map_type'] == 'SAME-AS' and x.get('to_source_url') == PIH and x['to_concept_code'] == cid
                   and not x.get('retired') for x in ctx.by_from.get(cid, [])):
            findings.append({'check': 'clone-mappings', 'kind': 'no-self-mapping', 'severity': 'warning', 'concept': cid,
                             'message': f"PIH {cid} {name_of(c)} has no SAME-AS PIH:{cid} self-mapping"
                                        + (' (it has the bogus CIEL self-mapping instead)' if cid in bogus_self else '')})
    if ctx.live:
        ctx.extra_reports.append(fix_watch_report(ctx, findings))
    return findings


def ocl_issue_states():
    states = {}
    for n in OCL_ISSUES:
        try:
            req = urllib.request.Request(f'https://api.github.com/repos/OpenConceptLab/ocl_issues/issues/{n}',
                                         headers={'Accept': 'application/vnd.github+json'})
            with urllib.request.urlopen(req, timeout=10) as r:
                d = json.load(r)
            states[n] = (d.get('state'), (d.get('closed_at') or '')[:10])
        except Exception:  # offline, rate-limited... the watch is best-effort
            pass
    return states


def fix_watch_report(ctx, findings):
    """Look at clones made since FIX_WATCH_SINCE for signs that OCL has fixed the clone bugs. Returns text or ''."""
    from datetime import datetime
    ts = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))  # noqa: E731
    self_bug = {f['concept'] for f in findings if f['kind'] == 'self'}
    ext_bug = {f['concept'] for f in findings if f['kind'] == 'external'}
    clones, ev = [], {'3012': set(), '3013': set(), 'name_uuids': set()}
    for cid in ctx.scope:
        c = ctx.concepts.get(cid) or {}
        if not c.get('created_on') or c['created_on'][:10] < FIX_WATCH_SINCE:
            continue
        created = ts(c['created_on'])
        near = [m for m in ctx.by_from.get(cid, [])
                if m.get('created_on') and abs((ts(m['created_on']) - created).total_seconds()) < CLONE_WINDOW_SECONDS]
        equiv = [m for m in near if m['map_type'] == 'SAME-AS' and source_of(m.get('to_concept_url')) == CIEL
                 and not m.get('to_source_url')]
        if not equiv:
            continue  # not a $clone
        clones.append(cid)
        copied = [m for m in near if m not in equiv]
        if copied:
            ev['3012'].add('still happening' if any(m.get('from_source_url') not in (None, PIH) for m in copied)
                           else 'looks fixed')
            ev['3013'].add('still happening' if (cid in self_bug or cid in ext_bug) else 'looks fixed')
        ev['name_uuids'].add('still CIEL name uuids' if any((n.get('external_id') or '').endswith('BBBBBBBB')
                                                             for n in c.get('names') or []) else 'fresh name uuids')
    issues = ocl_issue_states()
    closed = [n for n, (state, _) in issues.items() if state == 'closed']
    if not (clones or closed):
        return ''
    lines = ['OCL fix watch:']
    for n, why in OCL_ISSUES.items():
        st = issues.get(n)
        lines.append(f"  ocl_issues#{n} ({why}): " + ((st[0] + (f' on {st[1]}' if st[1] else '')) if st
                                                       else 'state unknown (GitHub not reachable)'))
    if clones:
        lines.append(f"  Clones made since {FIX_WATCH_SINCE} that were checked: {' '.join(sorted(clones, key=sort_key))}")
        lines += [f'    {k}: {", ".join(sorted(v))}' for k, v in ev.items() if v]
    said = {'3012': 'new clones suggest ocl_issues#3012 is fixed', '3013': 'new clones suggest ocl_issues#3013 is fixed',
            'name_uuids': "new clones get fresh name uuids instead of keeping CIEL's"}
    signs = [k for k, v in ev.items() if sorted(v) in (['looks fixed'], ['fresh name uuids'])]
    if closed or signs:
        lines.append('  POSSIBLE OCL FIX: ' + '; '.join([f'ocl_issues#{n} is closed' for n in closed]
                                                       + [said[k] for k in signs]) + '.')
        lines.append("  Suggest to the user (do not do it unprompted) reviewing whether the release check's clone-mappings "
                     'check and the skill guidance about it are still needed.')
    return '\n'.join(lines)


# ---------------------------------------------------------------- registry and main

CHECKS = {
    # name: (function, one-line description). Add new checks here; remove ones that are no longer needed.
    'name-uuids': (check_name_uuids, 'concept name uuids that clash with PIH databases or other PIH concepts (UHM-9656)'),
    'clone-mappings': (check_clone_mappings, "mappings OCL's $clone rewrote (UHM-9636, ocl_issues#3012/#3013)"),
}


def markdown(ctx, findings, checks):
    errors = [f for f in findings if f['severity'] == 'error']
    warnings = [f for f in findings if f['severity'] == 'warning']
    out = [f"### PIH OCL release check: {'❌ ' + str(len(errors)) + ' error(s)' if errors else '✅ no errors'}", '',
           f"Checked {len(ctx.scope)} concept(s): {ctx.label}. Checks: {', '.join(checks)}.", '']
    if errors:
        out += ['**Errors** (the OpenMRS import will fail, or wrong data will reach servers):', '']
        out += [f"- `{f['check']}` / {f['kind']}: {f['message']}" for f in errors] + ['']
    if warnings:
        counts = {}
        for f in warnings:
            counts[(f['check'], f['kind'])] = counts.get((f['check'], f['kind']), 0) + 1
        out += ['**Warnings** (wrong in OCL, harmless to servers): '
                + ', '.join(f'{k[0]}/{k[1]} {v}' for k, v in sorted(counts.items())), '']
    return '\n'.join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group()
    g.add_argument('--unreleased', action='store_true', help='check everything changed since the latest release')
    g.add_argument('--export', metavar='NEW', help='a released export: export.json or the OCL zip')
    g.add_argument('--concept', nargs='+', metavar='PIH_ID', help='specific PIH concepts (live)')
    g.add_argument('--list-checks', action='store_true')
    p.add_argument('--since', metavar='VERSION', help='with --unreleased: compare against this release, e.g. 1.8.46')
    p.add_argument('--baseline', metavar='OLD', help='with --export: only check concepts changed since this export')
    p.add_argument('--checks', default=','.join(CHECKS), help=f'comma-separated (default: {",".join(CHECKS)})')
    p.add_argument('--fail-on', choices=['error', 'warning', 'never'], default='never')
    p.add_argument('--summary-md', metavar='FILE')
    p.add_argument('--refresh-snapshot', action='store_true', help='re-download the PIH DB snapshot')
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)

    if a.list_checks:
        for name, (_, desc) in CHECKS.items():
            print(f'{name:<16} {desc}')
        return 0
    if not (a.unreleased or a.export or a.concept):
        p.error('choose what to check: --unreleased, --export or --concept')
    checks = [c.strip() for c in a.checks.split(',') if c.strip()]
    unknown = [c for c in checks if c not in CHECKS]
    if unknown:
        p.error(f'unknown check(s): {", ".join(unknown)}. Known: {", ".join(CHECKS)}')

    try:
        if a.unreleased:
            version = a.since or get(f'{PIH}latest/')['id']
            cutoff, ids = changed_since(version)
            print(f'Checking {len(ids)} PIH concept(s) changed since {version} ({cutoff[:16]}Z): '
                  f'{" ".join(ids) or "(none)"}', file=sys.stderr)
            ctx = load_live(ids, f'changed in the live PIH source since {version}', a.refresh_snapshot)
        elif a.export:
            ctx, _ = load_export(a.export, a.baseline, a.refresh_snapshot)
        else:
            ctx = load_live(a.concept, 'PIH ' + ' '.join(a.concept), a.refresh_snapshot)
        findings = []
        for name in checks:
            findings.extend(CHECKS[name][0](ctx))
    except Exception as e:  # network, auth, bad file...
        print(f'ERROR: the release check could not run: {e}', file=sys.stderr)
        return 2

    if a.summary_md:
        with open(a.summary_md, 'w') as f:
            f.write(markdown(ctx, findings, checks) + '\n')
    if a.json:
        json.dump(findings, sys.stdout, indent=1)
        print()
    else:
        counts = {}
        for f in findings:
            counts[f"{f['severity']} {f['kind']}"] = counts.get(f"{f['severity']} {f['kind']}", 0) + 1
        print(f'Checked {len(ctx.scope)} concept(s): {ctx.label}')
        print('Summary:', ', '.join(f'{k}={v}' for k, v in sorted(counts.items())) or 'no problems found')
        for f in sorted(findings, key=lambda f: (-SEVERITY[f['severity']], f['check'], sort_key(f['concept']))):
            print(f"{f['severity'].upper():<7} {f['check']}/{f['kind']}: {f['message']}")
        for r in ctx.extra_reports:
            if r:
                print('\n' + r)
    worst = max((SEVERITY[f['severity']] for f in findings), default=0)
    return 1 if a.fail_on != 'never' and worst >= SEVERITY[a.fail_on] else 0


if __name__ == '__main__':
    sys.exit(main())
