---
name: ocl-search
description: Search and edit Open Concept Lab (OCL) terminology via the OCL REST API behind app.v3.openconceptlab.org — especially the PIH source in the PIH org, where the usual work is pulling (cloning) concepts from CIEL into PIH, creating new PIH concepts, modifying existing PIH concepts, adding mappings, and releasing new source versions. Use this whenever the user mentions OCL, Open Concept Lab, CIEL, the PIH dictionary or PIH concepts, looking up/adding/editing a concept, mapping, concept set, source or collection, or pastes an app.v3.openconceptlab.org or api.openconceptlab.org link, even if they don't say "API".
---

# OCL search and maintenance

The OCL web app (`https://app.v3.openconceptlab.org/`) is a front end for the REST API at `https://api.openconceptlab.org`. Query the API with `curl` (or a small Python script for loops) rather than driving the web UI; it's faster, scriptable, and returns JSON.

Many users of this plugin aren't developers. Explain results in plain language, and keep raw JSON out of answers unless they ask for it.

## Authentication

Anonymous API access is disabled, even for public content like CIEL (a 403 with `"Authentication required. Anonymous API access is disabled."`).

- Use the user's **API token** (OCL web app → profile → API Token), never their password.
- The token lives in `~/.config/ocl/token`, outside any repo. If it's missing or doesn't work, run the `/ocl:setup` command, which walks the user through creating it.
- Never ask the user to paste the token into the chat, and never `export` it via `!`. Each Bash call starts a fresh shell, so an exported variable doesn't carry over, and `!` commands land in the transcript.
- Read the token inline in each call, so its value never gets echoed:
  ```bash
  curl -s -H "Authorization: Token $(cat ~/.config/ocl/token)" 'https://api.openconceptlab.org/...'
  ```

## URL patterns

Resources are nested by owner (org or user), then repo (source or collection):

| What | Path |
|---|---|
| Global concept search | `/concepts/?q=<term>` |
| Concepts in a source | `/orgs/<ORG>/sources/<SOURCE>/concepts/?q=<term>` |
| One concept | `/orgs/<ORG>/sources/<SOURCE>/concepts/<ID>/` |
| Mappings in a source | `/orgs/<ORG>/sources/<SOURCE>/mappings/` |
| A source version | `/orgs/<ORG>/sources/<SOURCE>/<VERSION>/` (`latest` = latest released) |
| Collections | `/orgs/<ORG>/collections/<COLL>/` |

- **Query params:** `limit`, `page`, `verbose=true`, `includeMappings=true`, `includeInverseMappings=true`.
- **Pagination:** the counts are in the response headers (`num_found`, `num_returned`, `next`). Use `curl -D -` when counts matter.
- **Sorting:** `sortDesc=last_update` gives the most recently changed items first. `sortDesc=id` sorts ids as strings, so don't use it to find the newest concept.

**Links for the user:** the web app URL is the API path on the app host. For example, API `/orgs/PIH/sources/PIH/concepts/9483/` ↔ `https://app.v3.openconceptlab.org/orgs/PIH/sources/PIH/concepts/9483/`. Include these links whenever you list concepts, so the user can open them.

**Which sets is a concept in?** Set membership is stored as a `CONCEPT-SET` mapping from the set to the member.
1. Look at the member's *inverse* mappings: `GET …/concepts/<ID>/?includeInverseMappings=true`.
2. Keep the `CONCEPT-SET` mappings whose `to_concept_code` is this concept. The `from_concept_code` of each is a parent set.
3. GET each parent set to read its name and class.

For many concepts, loop in a small Python script (`python3 -I`, token read from the file) instead of running many separate curls.

## The PIH source (`/orgs/PIH/sources/PIH/`)

This is the main working source.

- **Validation:** `custom_validation_schema: OpenMRS`. OCL enforces OpenMRS rules, e.g. exactly one fully-specified name per locale and unique preferred names.
- **Auto-IDs:** the concept id (mnemonic) is assigned sequentially from 20000, and the `external_id` is a random UUID. Don't supply either when creating.
- **Locales:** default `en`; supported `en`, `es`, `fr`, `ht`.
- **Access:** publicly viewable; only members of the PIH org can edit.

The concept id is a PIH number, never the CIEL number. Concepts fall into three groups:

| Kind | id | external_id | Typical mappings |
|---|---|---|---|
| Legacy, imported from OpenMRS | < 20000 | the OpenMRS UUID; CIEL-derived ones keep the CIEL UUID (`145851AAAA…`) | `SAME-AS PIH:<id>`, `SAME-AS CIEL:<ciel id>`, plus SNOMED, ICD-10, etc. |
| New PIH-only concepts | ≥ 20000 | random UUID | `SAME-AS PIH:<id>` (self-reference) |
| Cloned from CIEL via `$clone` | ≥ 20000 | new random UUID, not the CIEL UUID | `SAME-AS CIEL:<ciel id>` (equivalency), plus copies of CIEL's mappings |

The `SAME-AS` mapping to `/orgs/PIH/sources/PIH/` with the concept's own id is a PIH convention, carried over from OpenMRS reference terms.

**Is a CIEL concept already in PIH?** Search PIH mappings for the CIEL code, not just names:
```bash
curl -s -H "Authorization: Token $(cat ~/.config/ocl/token)" \
  'https://api.openconceptlab.org/orgs/PIH/sources/PIH/mappings/?toConcept=<CIEL_ID>&toSource=CIEL'
```
No hits means PIH doesn't have it yet, unless someone created it by hand without a CIEL mapping, so also do a quick name search.

## Writing to PIH

Writes change a shared, production terminology that feeds OpenMRS deployments, and colleagues see the changes immediately.

- **Before every write**, show the user what will be sent and to which URL, in plain words as well as the request. Wait for their go-ahead. Approval for one write doesn't cover the next one.
- **After every write**, GET the result and confirm what changed.

**Auto mode:** Claude Code's auto mode blocks OCL write requests as "modifying shared resources", even after the user says yes. Don't try to work around it. Instead:
1. Write the exact requests into a script in the scratchpad: token read from the file, `set -euo pipefail`, and stop on the first non-2xx response.
2. Tell the user they can review it and run it with `! bash <path>`, or switch permission modes and let you run it.
3. Verify the results with GETs.

### 1. Pull (clone) concepts from CIEL into PIH

This uses the same endpoint as the web app's "Clone to source" dialog:

```bash
curl -s -X POST -H "Authorization: Token $(cat ~/.config/ocl/token)" -H 'Content-Type: application/json' \
  'https://api.openconceptlab.org/orgs/PIH/sources/PIH/concepts/$clone/' \
  -d '{"expressions": ["/orgs/CIEL/sources/CIEL/concepts/<CIEL_ID>/"],
       "parameters": {"mapTypes": "Q-AND-A,CONCEPT-SET", "excludeMapTypes": "", "returnMapTypes": "*",
                      "cascadeLevels": "1", "equivalencyMapType": "SAME-AS",
                      "omitIfExistsIn": "/orgs/PIH/sources/PIH/"}}'
```

These parameters are the web app's defaults. Here's what they do:
- Pull in the concept's answers and set members (`Q-AND-A`, `CONCEPT-SET`), one level deep.
- Skip any concept PIH already has an equivalent for, so the clone links to the existing PIH concept instead of creating a duplicate.
- Copy the concept's mappings.
- Give each new concept a new PIH id and UUID, and add `SAME-AS` → the CIEL concept.

The response is keyed by expression, each with a `status` and a `bundle` listing what was created. There's a per-user quota (`clone_resources_per_call_limit_reached`).

**Preview first:** `GET /orgs/CIEL/sources/CIEL/concepts/<ID>/$cascade/?mapTypes=Q-AND-A,CONCEPT-SET&cascadeLevels=1` returns a Bundle whose `entry` items are the concepts and mappings that would come along. Escape the `$` in a double-quoted shell string. Check each answer concept against PIH using the mapping search above, and show the user what would be created.

**Possible clone quirks** (seen on existing clones; not confirmed, so check with the dictionary maintainers before acting on them):
- No `SAME-AS PIH:<id>` self-mapping is created. Ask the user whether to add one, to match convention.
- CIEL's own `SAME-AS CIEL:<id>` mapping may get copied with its code rewritten to the new PIH id, leaving a bogus "CIEL:<PIH id>" mapping. Check for this after a clone.
- CIEL names keep their CIEL name UUIDs (`…BBBB`), and extra CIEL locales come along too.

### 2. Create a new concept in PIH

`POST /orgs/PIH/sources/PIH/concepts/` with JSON. Omit `id` and `external_id`. Minimum shape:
```json
{"concept_class": "Question", "datatype": "Coded",
 "names": [{"name": "…", "locale": "en", "locale_preferred": true, "name_type": "FULLY_SPECIFIED"}],
 "descriptions": [{"description": "…", "locale": "en"}]}
```
- Numeric concepts carry their ranges in `extras`, e.g. `{"hi_absolute": 20, "low_absolute": 0}`.
- Then add the self-mapping: `POST /orgs/PIH/sources/PIH/mappings/` with `map_type` `SAME-AS`, `from_concept_url` = the new concept's URL, `to_source_url` `/orgs/PIH/sources/PIH/`, and `to_concept_code` = the new id.
- For coded questions, add `Q-AND-A` mappings to each answer. For sets, add `CONCEPT-SET` mappings to each member.

Before creating, search PIH and CIEL for an existing equivalent. If CIEL has one, clone it (workflow 1) instead.

### 3. Modify a PIH concept

`PUT /orgs/PIH/sources/PIH/concepts/<ID>/` with the changed fields; each edit creates a new concept version.
- **Names and descriptions are replaced as a whole list.** GET the concept first (`?verbose=true`), edit that JSON, and send the full `names`/`descriptions` back. Otherwise you'll silently drop translations.
- **Mappings** are edited separately, at `/orgs/PIH/sources/PIH/mappings/<MAPPING_ID>/`.
- **Retire rather than delete.** `DELETE` on a concept retires it in OCL, and it accepts an `update_comment`.

### 4. Add a mapping to an external code system

`POST /orgs/PIH/sources/PIH/mappings/`:
```json
{"map_type": "<type>", "from_concept_url": "/orgs/PIH/sources/PIH/concepts/<ID>/",
 "to_source_url": "/orgs/<OWNER>/sources/<SOURCE>/", "to_concept_code": "<CODE>"}
```
- **The target source must exist in OCL,** but the code doesn't need to be a concept in it. External sources (e.g. `/orgs/PIH/sources/DCM/`, DICOM) can be empty and just be referenced by code.
- **Pick a map type that's true.** Use `SAME-AS` only for real equivalence. For an attribute, such as an imaging orderable's DICOM modality, use a non-equivalence type that already exists in PIH and OpenMRS, e.g. `Associated with`. Check the types in use with `GET /orgs/PIH/sources/PIH/mappings/?facetsOnly=true` (`facets.fields.mapType`).

**For the mapping to show up in OpenMRS / FHIR:**
- **Source name:** the OpenMRS OCL module matches a mapping's target source by name (exact, then case-insensitive, then fuzzy). If nothing matches, it creates the source itself. So the OpenMRS concept source name should match the OCL source's `short_code`.
- **FHIR coding:** FHIR2 only emits a mapping as a coding if the OpenMRS concept source has a FHIR concept source URL. If the concept has more than one map type to the same system, FHIR2 emits only the SAME-AS one, or nothing at all if none of them is SAME-AS. So keep one mapping per system for non-SAME-AS codes.
- **Where the config lives:** in PIH distros, both are Initializer CSVs under `content/configuration/backend_configuration/{conceptsources,fhirconceptsources}/`.

### 5. Release a new PIH source version

Changes reach OpenMRS servers through released source versions, not the live source.
- **Check the latest:** `GET /orgs/PIH/sources/PIH/versions/?limit=5&verbose=true` lists recent versions. They're numbered sequentially (`1.8.x`), each with a short description of what changed.
- **Create the next one:** `POST /orgs/PIH/sources/PIH/versions/` with `{"id": "<next>", "description": "<what changed>", "released": true}`.
- **Verify it:** `GET …/PIH/latest/` should return it, and `GET …/PIH/<version>/concepts/<id>/` reads that version's snapshot.
- **Get the export:** the zip export is built separately. Right after creation, `GET …/PIH/<version>/export/` may return 204 (not ready). Workflow 6 covers downloading it into a distro.
- **Coordinate first:** releasing a version includes everyone's unreleased edits, not just yours. Check with the dictionary maintainers before releasing.

### 6. Put a released version's export into a PIH distro

OpenMRS servers load the PIH dictionary from an export zip committed to the distro, so a release only reaches them once its zip is swapped in.

- **No checkout needed:** `PIH/pihemr` may have an *Update OCL export* GitHub Action (Actions tab → Run workflow) that does all of this and opens a PR. If it exists, point non-developers to it. The steps below are for doing it locally.

1. **Get the download URL.** `GET …/PIH/<version>/export/` with the token returns `302`, redirecting to a signed S3 URL such as `https://ocl-production-s3.s3.amazonaws.com/orgs/PIH/PIH_PIH_v1.8.43.2026-10-29_212531.zip?…`. Read the `Location` header (`curl -s -D - -o /dev/null …`), then download that URL in a separate curl *without* the token header. It's already signed, and this keeps the token from going to S3.
2. **Check the zip** before using it. It holds a single `export.json`. Confirm its `id` is the version you wanted, and note how many `concepts` and `mappings` it has, so you can tell the user.
3. **Find the distro folder.** In the pihemr distro (`PIH/pihemr`), it's `content/configuration/backend_configuration/ocl/`. The folder holds exactly one zip, which is the current export. Other PIH config repos (e.g. `config-pihemr/configuration/ocl/`) carry their own, often older, export. Update only the ones the user asks for.
4. **Check master first.** Others commit export bumps often, sometimes several a week. `git fetch`, then compare the branch's zip with `origin/master`'s. If master already has a newer version than the branch, rebase before swapping, so you don't hit a conflict on the binary file.
5. **Swap the zip.** Delete the old one and add the new one, named to match master. Since Oct 2026 that's `orgs_PIH_sources_PIH_<version>_<YYYY-MM-DD_HHMMSS>.zip`, using the timestamp from the S3 filename. Older commits used the raw S3 name (`PIH_PIH_v<version>.<timestamp>.zip`). Then `git grep` for the old filename. No references have been found so far.
