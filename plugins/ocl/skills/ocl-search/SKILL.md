---
name: ocl-search
description: Search and edit Open Concept Lab (OCL) terminology via the OCL REST API behind app.v3.openconceptlab.org — especially the PIH source in the PIH org, where the usual work is pulling (cloning) concepts from CIEL into PIH, creating new PIH concepts, modifying existing PIH concepts, adding mappings, and releasing new source versions. Use this whenever the user mentions OCL, Open Concept Lab, CIEL, the PIH dictionary or PIH concepts, looking up/adding/editing a concept, mapping, concept set, source or collection, or pastes an app.v3.openconceptlab.org or api.openconceptlab.org link, even if they don't say "API".
---

# OCL search and maintenance

The OCL web app (`https://app.v3.openconceptlab.org/`) is a front end for the REST API at `https://api.openconceptlab.org`. Query the API with `curl` (or a small Python script for loops) rather than driving the web UI; it's faster, scriptable, and returns JSON.

Many users of this plugin aren't developers. Explain results in plain language, and keep raw JSON out of answers unless they ask for it.

## Check for a plugin update (once per session)

The first time this skill is used in a session, run:
```bash
python3 -I <this skill's base directory>/scripts/check_update.py
```
It compares this plugin's version with the latest on GitHub (read-only, no token, cached for a day) and always exits 0.
- **`UPDATE AVAILABLE`:** tell the user in one or two plain sentences, before the answer to their request. Say that newer versions include checks that help avoid bad releases, and how to update: type `/plugin marketplace update pih`, then `/plugin` → **Installed** → `ocl` → **Update now**, then start a new session. Mention that `/plugin` → **Marketplaces** → `pih` → **Enable auto-update** keeps it current automatically. Then carry on with their request using the current version. Don't update anything yourself.
- **Before a release** (see "Check before releasing" below), if the check said `UPDATE AVAILABLE`, recommend updating first, because the release checks may have improved.
- **Anything else** (`up to date`, `ahead` (a local development copy), or `skipped`): say nothing about it.

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
| Cloned from CIEL via `$clone` | ≥ 20000 | usually a new random UUID (some keep the CIEL UUID); names keep CIEL name UUIDs (`…BBBB`) | `SAME-AS CIEL:<ciel id>` (equivalency), copies of CIEL's mappings, and a broken "CIEL:<PIH id>" self-mapping (see the clone bug in workflow 1) |

The `SAME-AS` mapping to `/orgs/PIH/sources/PIH/` with the concept's own id is a PIH convention, carried over from OpenMRS reference terms.

**Is a CIEL concept already in PIH?** Search PIH mappings for the CIEL code, not just names:
```bash
curl -s -H "Authorization: Token $(cat ~/.config/ocl/token)" \
  'https://api.openconceptlab.org/orgs/PIH/sources/PIH/mappings/?toConcept=<CIEL_ID>&toConceptSource=CIEL'
```
No hits means PIH doesn't have it yet, unless someone created it by hand without a CIEL mapping, so also do a quick name search.

- **The source filter is `toConceptSource`** (it matches the mapping's `to_source_name`). `toSource` is silently ignored: it returns every mapping that matches the other filters, e.g. `toConcept=5089` alone also returns `PIH:5089` and set memberships.
- **`toConcept` matches a code or a name.**

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

**Known `$clone` bugs** (confirmed Nov 2026, Jira UHM-9636). They're reported to OCL as [ocl_issues#3012](https://github.com/OpenConceptLab/ocl_issues/issues/3012) and [ocl_issues#3013](https://github.com/OpenConceptLab/ocl_issues/issues/3013); check both for a fix before assuming they still happen (`gh issue view <n> -R OpenConceptLab/ocl_issues`). Both are in oclapi2 `core/sources/models.py` (`clone_resources`, `clone_mappings`) and `Mapping.clone()`.

1. **The source URLs are never updated (#3012).** Every copied mapping keeps the original mapping's `from_source_url`, which is CIEL, even though it now starts from a PIH concept. This is cosmetic: the OpenMRS importer never reads `from_source_url`.
2. **The target is swapped (#3013).** For each copied mapping, `$clone` checks whether PIH already has a `SAME-AS` to the mapping's target. If so, it points the copy at that PIH concept instead. It updates `to_concept_url`, `to_concept_code` and `to_source_name`, but leaves `to_source_url` on the original source. What this does to each kind of mapping:

| CIEL mapping | After the clone | Effect in OpenMRS |
|---|---|---|
| `SAME-AS CIEL:<ciel id>` (CIEL's self-mapping) | "CIEL:<PIH id>", pointing at the new concept itself | OpenMRS uses `to_source_name` + code, so it gets `SAME-AS PIH:<id>`, the normal self-mapping. Only OCL looks wrong. |
| `Q-AND-A` / `CONCEPT-SET` / other concept-to-concept | points at the right PIH concept, but `to_source_url` still says CIEL | None. The importer follows `to_concept_url`. |
| ICD-10, LOINC, or any external code that exists as a concept in OCL, *when some PIH concept is SAME-AS that code* | points at that PIH concept; **the external code is lost** | Wrong: e.g. `BROADER-THAN PIH:10034` instead of `BROADER-THAN ICD-10-WHO:L28.0`. |

SNOMED, IMO and other codes that aren't concepts in OCL (`to_concept_url` is null) aren't affected. The clone doesn't add a separate, proper `SAME-AS PIH:<id>` self-mapping. The `SELF` mapping in the first row stands in for it.

**After every clone, check it** with the release check (see workflow 5):
```bash
python3 -I <this skill's base directory>/scripts/ocl_release_check.py --concept <new PIH ids…>
```
It's read-only and reads the token from the file. It runs every check: `name-uuids` compares the new concepts' name UUIDs against a PIH database (see "Other clone behavior" below; the first run downloads a snapshot of about 33 MB to `~/.cache/ocl/`), and `clone-mappings` looks for the mapping bugs above. Each finding is an `ERROR` (fix before releasing) or a `WARNING` (report only):
- **`name-uuids/name-clash` / `name-uuids/dup-name-uuid` (errors):** must be fixed before the next release, because the OpenMRS import will fail. Propose giving that name a new UUID (workflow 3). A `name-clash-handled` warning means the clash is already fixed on servers (e.g. by a distro Liquibase changeset); it's listed in `HANDLED_NAME_CLASHES` in the script.
- **`clone-mappings/external` (error):** must be fixed. Tell the user, and propose retiring the bad mapping and adding the correct one with the same map type (workflow 4). The script shows two codes:
  - **"Lost code":** the code that was lost in the clone.
  - **"CIEL … today":** CIEL's mapping *today*.

  Right after a clone these match. For older clones, CIEL may have changed its mapping since, so if they differ, show the user both and let them choose. Also check whether someone already re-added the correct mapping by hand; if so, only retire the bad one.
- **`clone-mappings/self` / `no-self-mapping` / `internal` (warnings):** leave them alone, and just mention them. OpenMRS already reads a `SELF` mapping as the usual `SAME-AS PIH:<id>`, and `INTERNAL` mappings point at the right concept. Cleaning these up is on hold until OCL fixes #3012/#3013. Retiring and re-adding them gives each mapping a new ID, which makes every server delete and recreate it on the next import, only to fix fields OpenMRS doesn't use.

Don't try to fix a mapping in place with `PUT`. It hasn't been tested on these inconsistent records.

**Watch for OCL fixing these bugs.** When run on live concepts (`--concept`, `--unreleased`), the release check ends with an **"OCL fix watch"** section, but only if there's something to report. It shows:
- **Issue state:** whether ocl_issues#3012 and #3013 are open or closed, from GitHub.
- **Fresh clones:** for clones made after the issues were filed, whether the bugs still show up. If not, the copied mappings have a PIH `from_source_url`, there are no `SELF` or `EXTERNAL` findings, and the clones get fresh name UUIDs.

If it prints **"POSSIBLE OCL FIX"**, tell the user. Then *suggest*, without doing it unprompted, reviewing whether the skill still needs the related guidance, and whether the `clone-mappings` check can be retired:
- **#3012:** the from-source note.
- **#3013:** the `SELF`/`INTERNAL`/`EXTERNAL` handling, and the on-hold cleanup (UHM-9636 step 3), which OCL's fix might also cover.
- **Name UUIDs:** the name-UUID caveat. Keep the `name-uuids` check anyway, as any manual name edit can still clash.

One clean clone is weak evidence, since that concept may simply not have triggered the bug. So before recommending a change, confirm with a clone that *would* have triggered it, e.g. preview a CIEL concept with an ICD-10 mapping that PIH already has, or check OCL's release notes. Any change to the skill goes through a PR, like other plugin changes.

To audit the whole source, download a released export (workflow 6, steps 1–2) and run the release check with `--export <export.json or zip>`. On 1.8.46 it found 29 external, 932 self and 282 internal problems. It doesn't report the wrong `from_source_url` (#3012), which affects about 3,850 mappings, nearly every mapping a clone has copied.

**Other clone behavior (expected; not a bug, confirmed with the dictionary maintainers):**
- Names keep their CIEL name UUIDs (`…BBBB`). PIH's auto-UUID for names isn't applied.
  - **But this can break the OpenMRS import.** A PIH server may already hold that UUID on another concept's name, often one voided years ago that OCL no longer shows. The import then fails with `Duplicate entry '…BBBB' for key 'concept_name_uuid_index'`. The failed concept's mappings fail too, Initializer aborts the OCL load, and pihcore won't start.
  - **It has happened.** Releases 1.8.47–1.8.50 broke this way (Jira UHM-9656): PIH 21797, cloned from CIEL 81457, reused CIEL name UUIDs that PIH servers had on 13277.
  - **OCL can't detect it.** The release check's `name-uuids` check compares against a 2023 snapshot of a PIH database (the pihcore test DB), which catches most cases.
  - **Possible prevention:** give cloned names fresh UUIDs right after cloning. Nothing at PIH is known to rely on names keeping CIEL's UUIDs, but that's a convention for the dictionary maintainers to decide, so only offer it.
- All CIEL locales come along (nl, vi, ru, pt_BR, …), not only en/es/fr/ht.

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
- **Check before releasing:** run the release check on everything changed since the last release:
  ```bash
  python3 -I <this skill's base directory>/scripts/ocl_release_check.py --unreleased
  ```
  It finds every PIH concept changed since the latest release (directly or through one of its mappings) and runs every check on them (`--list-checks` lists them).
  - **Any `ERROR`:** the release would break the OpenMRS import, or lose a code. Fix these first. `WARNING`s are report-only.
  - **Testing:** `--since <older version>` checks against an older release instead, e.g. `--since 1.8.46` reproduces the 1.8.47 failure.

  This catches the problems we know about, not every possible import error. Once the release is out, loading its export on a test server is still the real test.
- **The same check runs in GitHub.** PIH/pihemr's "Update OCL export" Action downloads `ocl_release_check.py` from this repo's `main` branch and runs it on the new export with `--export <new zip> --baseline <zip in the distro> --fail-on error`, so only concepts that changed are checked. If there's an error, it doesn't open the PR. So a release with errors never reaches the distro, even if nobody ran the check before releasing.
- **Adding or retiring a check:** write a function that returns findings and register it in `CHECKS` in `ocl_release_check.py`, with a test in `test_ocl_release_check.py` (run `python3 -I -m unittest discover -s <scripts dir> -p 'test_*.py'`). Remove a check from `CHECKS` once it's no longer needed (e.g. when OCL fixes the bug behind it). The pihemr Action picks up changes automatically. Keep the command-line options and exit statuses it uses working (`--export`, `--baseline`, `--fail-on`, `--summary-md`; exit 0 OK, 1 errors, 2 couldn't run), or change that workflow in the same release.
- **Check the latest:** `GET /orgs/PIH/sources/PIH/versions/?limit=5&verbose=true` lists recent versions. They're numbered sequentially (`1.8.x`), each with a short description of what changed.
- **Create the next one:** `POST /orgs/PIH/sources/PIH/versions/` with `{"id": "<next>", "description": "<what changed>", "released": true}`.
- **Verify it:** `GET …/PIH/latest/` should return it, and `GET …/PIH/<version>/concepts/<id>/` reads that version's snapshot.
- **Get the export:** the zip export is built separately, which took about 4 minutes for 1.8.44. Until it's ready, `GET …/PIH/<version>/export/` returns 204 (not started) or 208 (being built), and once it's ready it returns 302. Wait for the 302 in a background loop rather than retrying by hand. Workflow 6 covers downloading it into a distro.
- **Coordinate first:** releasing a version includes everyone's unreleased edits, not just yours. Check with the dictionary maintainers before releasing.

### 6. Put a released version's export into a PIH distro

OpenMRS servers load the PIH dictionary from an export zip committed to the distro, so a release only reaches them once its zip is swapped in.

- **No checkout needed:** `PIH/pihemr` has an *Update OCL export* GitHub Action (Actions tab → Run workflow) that does all of this and opens a PR. It runs the release check and the load test (step 3) first, unless *Skip the release check* or *Skip the load test* is ticked. Point non-developers to it. The steps below are for doing it locally.

1. **Get the download URL.** `GET …/PIH/<version>/export/` with the token returns `302` once the export is built (204 or 208 mean it isn't ready yet; see workflow 5), redirecting to a signed S3 URL such as `https://ocl-production-s3.s3.amazonaws.com/orgs/PIH/PIH_PIH_v1.8.43.2026-10-29_212531.zip?…`. Read the `Location` header (`curl -s -D - -o /dev/null …`), then download that URL in a separate curl *without* the token header. It's already signed, and this keeps the token from going to S3.
2. **Check the zip** before using it. It holds a single `export.json`. Confirm its `id` is the version you wanted, and note how many `concepts` and `mappings` it has, so you can tell the user.
3. **Load-test it on a real OpenMRS database** before creating any branch. The release check only catches the problems we know about; this runs the actual import. Ask the user first whether to run it, since it takes about 5–10 minutes. If they skip it, say so in the PR description.
   - It uses pihemr's `scripts/ocl-load-test.sh`, the same script the GitHub Action runs. If `origin/master` doesn't have it yet, say the load test isn't available and carry on.
   - Don't touch the user's pihemr checkout. Make a throwaway worktree from master: `git -C <pihemr> fetch`, then `git -C <pihemr> worktree add --detach <scratch>/pihemr-load-test origin/master`. In it, replace the zip in `content/configuration/backend_configuration/ocl/` with the new one, named as in step 6.
   - Run `scripts/ocl-load-test.sh --summary-md <scratch>/load-test.md --openmrs-log <scratch>/openmrs.log` there, in the background (Java 8, Maven and Docker are needed). It builds pihemr and the ZL EMR distribution with the new export, restores the nightly ZL seed database (`partnersinhealth/zl-emr-seed-haiti`, which already has master's export loaded) into a new `openmrs-docker` instance, starts it, and checks that the OCL import finished with no errors. It clones zl-emr and distro-tools itself; pass `--distro-tools-dir` to use the user's checkout.
   - Exit 0: it loaded cleanly; carry on. Exit 1: it didn't; show the user the summary (it lists the items that failed, with the database error for each) and stop. The full log is in `openmrs.log` if they need more. Don't create a branch for an export that doesn't load. Exit 2: the test couldn't run; tell the user why and ask whether to go on without it.
   - Afterwards, remove the worktree (`git -C <pihemr> worktree remove --force <scratch>/pihemr-load-test`). The script stops the instance but keeps it so it can be inspected; tell the user it's there and that `openmrs-docker <instance> destroy` removes it (it asks them to confirm, so leave it to them). Also tell them the test installed a pihemr snapshot with this export into `~/.m2`, which their other local builds will use until they rebuild pihemr or Maven pulls a newer snapshot.
4. **Find the distro folder.** In the pihemr distro (`PIH/pihemr`), it's `content/configuration/backend_configuration/ocl/`. The folder holds exactly one zip, which is the current export. Other PIH config repos (e.g. `config-pihemr/configuration/ocl/`) carry their own, often older, export. Update only the ones the user asks for.
5. **Check master first.** Others commit export bumps often, sometimes several a week. `git fetch`, then compare the branch's zip with `origin/master`'s. If master already has a newer version than the branch, rebase before swapping, so you don't hit a conflict on the binary file.
6. **Swap the zip.** Delete the old one and add the new one, named to match master. Since Oct 2026 that's `orgs_PIH_sources_PIH_<version>_<YYYY-MM-DD_HHMMSS>.zip`, using the timestamp from the S3 filename. Older commits used the raw S3 name (`PIH_PIH_v<version>.<timestamp>.zip`). Then `git grep` for the old filename. No references have been found so far.
