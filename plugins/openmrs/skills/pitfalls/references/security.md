# Security and privileges (G1-G11)

Starred categories (★) recur across many years or many reviews. Read them first.

## G1 ★ Service method without `@Authorized` (fails open)
A public service method has no privilege annotation, so any caller, including unauthenticated ones, can use it. By-uuid getters, `getAll`, counts and `purge` are the usual misses.
- **While writing:** Annotate every public service method with `@Authorized`, including by-uuid, `getAll`, purge and count variants. Write a test that an unprivileged user is denied.
- **When reviewing:** A public method added to a `*Service` interface with no `@Authorized` in the preceding annotation lines; new REST or controller endpoints with no privilege check.
- **Seen in:** TRUNK-698, TRUNK-6253 to TRUNK-6259, TRUNK-6776, d8fe1365f (about 15 public fixes, 2007-2026)
- **Module twist:** Retrofitting auth into a module that shipped open breaks existing roles, so ship a role-grant migration in the same release. In the 2.x UI, `requiredPrivilege` on an app or extension only hides the link: the page controller and every public method on a `FragmentController` stay reachable by URL, so check the privilege server-side (RA-239, UIFR-134). REST resources: see J1.

## G6 ★ Incomplete path containment (zip slip, traversal)
A path check misses a branch, uses String `startsWith` on a non-normalized path, or checks only the entry name, so `..` or an absolute path escapes the intended directory.
- **While writing:** Resolve, normalize, then check containment with `Path.startsWith` on every branch (zip entries, servlet resources, resource providers, dev-dir variants).
- **When reviewing:** `String.startsWith(` or `getCanonicalPath().startsWith` for containment; `contains("..")`; `base + relativePath` with no check; a fix that covers one code path of several.
- **Seen in:** CVE-2022-23612 / GHSA-8rgr-ww69-jv65, TRUNK-6226, CVE-2026-40076, CVE-2026-40075 (fixed 4+ times)
- **Module twist:** ResourceProviders in the UI framework could load arbitrary files through traversal or absolute paths; the first fix was reverted and re-landed (UIFR-215).

## G10 ★ Escaping in the wrong layer
Output is encoded for the wrong context (HTML encoder inside a JS string or JSON) or escaped on input, so XSS persists or legitimate data is corrupted. Fixes arrive in waves and get reverted.
- **While writing:** Store raw data. Escape at output with the encoder for the sink: JavaScript, HTML attribute, HTML body, JSON serializer. Test with `O'Brien "}];alert(1);//`.
- **When reviewing:** `${...}` inside `<script>` or `onclick=` without a JS encoder; `encodeHtml` applied to JSON; quote-style "fixes"; `ng-bind-html` with no sanitize; `.html(` or `.append(` with server strings; uploads served back with a renderable content type.
- **Seen in:** TRUNK-3931 to TRUNK-3940, GHSA-vpxm-cr3r-pjp9, fc20f2130, webservices.rest@6f5471d1 (stored XSS in a clobdata endpoint)
- **Module twist:** In the 2.x UI (GSP/JSP) there were 40+ commits across 6+ repos: `ui.encodeJavaScript` inside JS strings, never `encodeHtml` on JSON; a changed `escapeJs` broke names with apostrophes (UIFR-203, RA-1424, coreapps@3353af1 reverted same day). Core's input-side XSSFilter also mangles module expression strings such as `require` and templates (AF-73, LUI-197).

## G2 Sibling methods disagree on the privilege
Two methods on the same entity require different privileges, or one checks a privilege that no longer exists, so the weaker one becomes the real policy.
- **While writing:** Same entity, same privilege across get, save, void and purge, plus per-object checks. Look up names in the target core's `PrivilegeConstants`.
- **When reviewing:** A new method whose `@Authorized` differs from its siblings; string privilege literals; privilege names deprecated in core.
- **Seen in:** TRUNK-4938, ef6bc1225, TRUNK-5444
- **Module twist:** A session endpoint checked VIEW_PROVIDERS, removed in core 2.0 (RESTWS-946); the reset-password endpoint required privileges the anonymous flow cannot have (RESTWS-885).

## G3 Authorization checks only the root, not cascaded children or stored state
The privilege check covers the object passed in, but cascades, void paths or nested data touch children the user may not modify, or the check reads request input instead of the persisted value.
- **While writing:** Enforce child privileges, including on void and cascade paths. Check the persisted value, not the submitted one.
- **When reviewing:** Cascaded saves or voids with one check at the top; privilege decisions made on a request field.
- **Seen in:** d5be4eb7d, b2f0b1305, 0a2dc9819
- **Module twist:** In REST, the "children" are representation-graph edges (nested and `custom:` reps, derived `display` strings): see J1.

## G4 Proxy privileges scoped too wide
`Context.addProxyPrivilege` stays active across more code than the single call that needed it, so caller-supplied logic runs with extra rights.
- **While writing:** Put add and remove of the proxy privilege in try/finally around the single call. Never wrap caller evaluation, callbacks or loops.
- **When reviewing:** `addProxyPrivilege` without a `finally` removal, or with a large block between add and remove.
- **Seen in:** 08668a329, TRUNK-6263, TRUNK-4496

## G5 Fail-open on error; pre-auth endpoints
An error in the authorization path allows the request, or setup, update or session endpoints stay reachable without login.
- **While writing:** "Can't determine" means deny. Setup and update wizards close permanently once complete. Pre-auth endpoints get explicit narrow proxy privileges.
- **When reviewing:** `catch` blocks that continue after a failed privilege lookup; new unauthenticated URL patterns.
- **Seen in:** acd187d81, TRUNK-6203, TRUNK-6258
- **Module twist:** Hardening in core can break pre-login pages in modules (REST session endpoint needed proxy privileges, webservices.rest@e81036bf). A multi-step login (2FA, forced password change, redirects) keeps state on the HTTP session; test sequences such as failed-then-successful attempts (AUT-34, AUT-31).

## G7 Evaluating stored text as Velocity or SpEL templates
Stored or user-supplied text is run through a template engine, which gives code execution to whoever can edit that text.
- **While writing:** Do not evaluate stored text. Use an allowlisted grammar or a sandbox, and fix every sink of the engine, not just one.
- **When reviewing:** `Velocity.evaluate`, `SpelExpressionParser`, `StandardEvaluationContext`, script engines fed from the database or from requests.
- **Seen in:** CVE-2026-41258 / GHSA-xj4f-8jjg-vx4q, TRUNK-4819
- **Module twist:** In htmlformentry, Velocity in form XML is intended, so "manage forms" amounts to code execution. Look for new Velocity entry points that take user- or patient-supplied text.

## G8 Unsafe XStream, XXE and reflection-by-name defaults
XML and object deserializers allow DTDs or arbitrary types, or code instantiates classes by a name taken from data.
- **While writing:** Disable DTDs and external entities. Allowlist XStream types. Check `isAssignableFrom` before instantiating by name.
- **When reviewing:** `new XStream(` without an allowlist; `DocumentBuilderFactory.newInstance(` with no `setFeature`; `Class.forName` on stored values.
- **Seen in:** TRUNK-3942, TRUNK-6188, TRUNK-6547
- **Module twist:** Reporting added XStream whitelisting in `ReportingSerializer`, reverted it 4 days later, re-added it for core 2.7+ and then deferred it (reporting@3083d1d3, 2024-25). When tightening an allowlist, check that stored definitions still deserialize (see N2).

## G9 String-built SQL, shell, properties and log lines
Values are concatenated into SQL, shell commands, property files or log lines instead of being bound or escaped.
- **While writing:** Bind parameters everywhere, including Liquibase custom changes, filters and `set @x=` statements.
- **When reviewing:** `createQuery(`, `createNativeQuery(`, `createSQLQuery(` or `executeSQL(` with `+` on the same line; user values in `Runtime.exec` or log format strings.
- **Seen in:** TRUNK-5244, 427441549, TRUNK-6549
- **Module twist:** Reporting splices context parameters (a user's name) into SQL (REPORT-881); its read-only check for stored SQL is a keyword denylist (see N6).

## G11 Weak session, token and credential lifecycle; secrets in logs
Tokens use weak randomness or can be reused, sessions are not rotated at login, credentials appear in GET requests or logs.
- **While writing:** Use `SecureRandom`. Make tokens single-use with an expiry. Rotate the session at login. Mask secrets in logs and scripts.
- **When reviewing:** `Math.random` or `Random` for tokens; credentials in URLs; password change that does not require the old password; error messages that reveal whether a user exists.
- **Seen in:** TRUNK-3938, TRUNK-6838, 720cc5317
- **Module twist:** REST session endpoints returned the sessionId and created sessions on DELETE (RESTWS-903, RESTWS-905); the forgot-password form leaked valid usernames (LUI-45).
