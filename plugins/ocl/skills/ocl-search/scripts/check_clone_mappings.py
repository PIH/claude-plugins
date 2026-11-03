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

Usage:
  check_clone_mappings.py --concept 21768 21760 ...   # live, from the OCL API
  check_clone_mappings.py --export export.json        # a whole released export
  add --json for machine-readable output.

For "external" findings it looks up the CIEL source concept and suggests the correct code.
The token is read from ~/.config/ocl/token. Run with `python3 -I`.
"""
import argparse
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
    p.add_argument('--json', action='store_true')
    a = p.parse_args()

    live = bool(a.concept)
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

    if a.json:
        json.dump(findings, sys.stdout, indent=1)
        print()
        return

    counts = {}
    for f in findings:
        counts[f['kind']] = counts.get(f['kind'], 0) + 1
    print('Summary:', ', '.join(f'{k}={v}' for k, v in sorted(counts.items())) or 'no problems found')
    order = {'external': 0, 'self': 1, 'no-self-mapping': 2, 'internal': 3}
    for f in sorted(findings, key=lambda f: (order[f['kind']], int(f['concept']) if f['concept'].isdigit() else 0)):
        if f['kind'] == 'external':
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


if __name__ == '__main__':
    main()
