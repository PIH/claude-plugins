# Which modules are "core"

## The rule

A module is **core** if it is **in the PIH distro *and* in either OpenMRS Reference Application distro (O3 or O2)**. openmrs-core itself is always core.

Work this out live from the files below. Don't rely on memory or an old list: the distros change.

| List | Repo | Branch | File | What to read |
|---|---|---|---|---|
| PIH distro | `PIH/pihemr` | `master` | `distro/openmrs-distro.properties` | `omod.<name>=` lines |
| O3 refapp, backend | `openmrs/openmrs-distro-referenceapplication` | `main` | `distro/distro.properties` | `omod.<name>=` lines |
| O3 refapp, frontend | `openmrs/openmrs-distro-referenceapplication` | `main` | `frontend/spa-assemble-config.json` | keys of `frontendModules` |
| O2 refapp | `openmrs/openmrs-distro-referenceapplication` | `2.x` | `package/src/main/resources/openmrs-distro.properties` | `omod.<name>=` lines |

Module names can contain dots (`omod.webservices.rest=`, `omod.serialization.xstream=`). Ignore only the attribute lines that end in a known suffix, such as `omod.appointments.groupId=` or `omod.serialization.xstream.type=`.

Fetching a file:

```bash
gh api 'repos/openmrs/openmrs-distro-referenceapplication/contents/distro/distro.properties?ref=main' --jq .content | base64 -d
```

Listing module names from a properties file:

```bash
... | grep -E '^omod\.' | grep -vE '\.(groupId|type|artifactId|version)=' | sed -E 's/^omod\.([^=]+)=.*/\1/' | sort -u
```

Sanity check: the result should include `webservices.rest`. If it doesn't, the filter is wrong.

A local checkout works too, if it has been fetched recently. Read from `origin/<branch>`, not from whatever happens to be checked out.

**Frontend:** PIH's frontend (`PIH/openmrs-frontend-pihemr`, `spa-build-config.json`) pulls every `@openmrs/esm-*` app at `next`. So any `@openmrs/esm-*` app in the O3 refapp's frontend list counts as core. `@pih/esm-*` apps are PIH's own.

## Modules in the PIH distro but in neither refapp

The explicit lists (treated as core / free to change / unclassified) are in [SKILL.md](../SKILL.md), so they live in one place.

A module that isn't in the PIH distro at all isn't one PIH runs. If the user still wants to change it, it is someone else's module. Follow its owners' process and treat it at least as carefully as core.
