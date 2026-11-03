#!/usr/bin/env python3
"""Advisory reviewer for OpenMRS diffs.

Reads unified diff text and prints one line per suspected historical pitfall:

    path:line  <ID>  <confidence>  <message>

Never blocks and never posts: the exit code is always 0. Python 3 standard
library only (subprocess is used solely for --repo).
"""
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Callable, List, Literal, Optional

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Line:
    kind: Literal["+", "-", " "]
    text: str
    new_lineno: Optional[int]
    old_lineno: Optional[int]


@dataclass
class Hunk:
    lines: List[Line] = field(default_factory=list)


@dataclass
class FileDiff:
    path: str
    hunks: List[Hunk] = field(default_factory=list)
    deleted: bool = False


@dataclass
class Finding:
    path: str
    line: int
    cat: str
    confidence: str
    message: str


@dataclass
class Check:
    cat: str
    confidence: str
    applies: Callable[[str], bool]
    run: Callable[[FileDiff], List[Finding]]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _strip_prefix(p: str) -> str:
    p = p.split("\t")[0].strip()
    if p.startswith(("a/", "b/")):
        p = p[2:]
    return p


def parse_diff(text: str) -> List[FileDiff]:
    """Parse unified diff text. Tolerates binary, rename-only and deleted files."""
    files: List[FileDiff] = []
    cur: Optional[FileDiff] = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        m = HUNK_RE.match(raw)
        if m and cur is not None:
            old_no = int(m.group(1))
            old_left = int(m.group(2)) if m.group(2) is not None else 1
            new_no = int(m.group(3))
            new_left = int(m.group(4)) if m.group(4) is not None else 1
            hunk = Hunk()
            i += 1
            while i < len(lines) and (old_left > 0 or new_left > 0):
                body = lines[i]
                if body.startswith("\\"):  # "\ No newline at end of file"
                    i += 1
                    continue
                kind = body[:1] if body else " "
                if kind not in ("+", "-", " "):
                    break
                t = body[1:]
                if kind == "+":
                    hunk.lines.append(Line("+", t, new_no, None))
                    new_no += 1
                    new_left -= 1
                elif kind == "-":
                    hunk.lines.append(Line("-", t, None, old_no))
                    old_no += 1
                    old_left -= 1
                else:
                    hunk.lines.append(Line(" ", t, new_no, old_no))
                    new_no += 1
                    old_no += 1
                    new_left -= 1
                    old_left -= 1
                i += 1
            cur.hunks.append(hunk)
            continue
        if raw.startswith("diff --git "):
            mm = re.match(r"diff --git a/(.*) b/(.*)$", raw)
            path = mm.group(2) if mm else raw[len("diff --git "):]
            cur = FileDiff(path=path)
            files.append(cur)
        elif raw.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old_p = _strip_prefix(raw[4:])
            new_p = _strip_prefix(lines[i + 1][4:])
            if cur is None or cur.hunks:
                cur = FileDiff(path=new_p if new_p != "/dev/null" else old_p)
                files.append(cur)
            if new_p == "/dev/null":
                cur.deleted = True
                cur.path = old_p
            else:
                cur.path = new_p
            i += 1
        elif raw.startswith("rename to ") and cur is not None:
            cur.path = raw[len("rename to "):].strip()
        elif raw.startswith("deleted file mode") and cur is not None:
            cur.deleted = True
        i += 1
    return files


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

CHECKS: List[Check] = []

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _lineno(ln: Line) -> int:
    return ln.new_lineno if ln.new_lineno is not None else (ln.old_lineno or 0)


def _added(fd: FileDiff):
    for h in fd.hunks:
        for ln in h.lines:
            if ln.kind == "+":
                yield ln


def _new_side(h: Hunk) -> List[Line]:
    """Context and added lines, i.e. the file as it will be after the change."""
    return [ln for ln in h.lines if ln.kind != "-"]


def _finding(fd: FileDiff, ln: Line, cat: str, conf: str, msg: str) -> Finding:
    return Finding(fd.path, _lineno(ln), cat, conf, msg)


def _register(cat: str, confidence: str, applies, run) -> None:
    CHECKS.append(Check(cat, confidence, applies, run))


# ---------------------------------------------------------------------------
# Liquibase checks (A1, A2, A3, A5)
# ---------------------------------------------------------------------------

RESERVED_WORDS = frozenset("""
rank condition order value group key rows window user to from select table
column index range interval read write system row groups lead lag over
partition unique primary references check default limit offset desc asc all
and or not like analyze both case cast current_date current_time
current_timestamp current_user end exists false true for grant having in into
is join leading natural null on only returning some then trailing union using
when where with dense_rank first_value last_value ntile percent_rank
row_number function lateral generated
""".split())

CHANGESET_OPEN = re.compile(r"<changeSet\b")
CHANGESET_CLOSE = re.compile(r"</changeSet>")
DDL_TAG = re.compile(
    r"<(?:ext:)?(?:createTable|addColumn|dropColumn|dropTable|createIndex|dropIndex|"
    r"renameColumn|renameTable|modifyDataType|modifyColumn|addForeignKeyConstraint|"
    r"dropForeignKeyConstraint|addNotNullConstraint|dropNotNullConstraint|"
    r"addUniqueConstraint|dropUniqueConstraint|addPrimaryKey|dropPrimaryKey|"
    r"addDefaultValue|dropDefaultValue|createView|dropView|addAutoIncrement)\b")


def _is_liquibase_xml(path: str) -> bool:
    low = path.lower()
    return low.endswith(".xml") and ("liquibase" in low or "changelog" in low)


def _new_changesets(h: Hunk) -> List[List[Line]]:
    """Blocks of lines for changeSets whose opening line is an added line."""
    blocks: List[List[Line]] = []
    cur: Optional[List[Line]] = None
    for ln in h.lines:
        if ln.kind == "+" and CHANGESET_OPEN.search(ln.text):
            cur = [ln]
            blocks.append(cur)
            if CHANGESET_CLOSE.search(ln.text):
                cur = None
            continue
        if cur is not None:
            if ln.kind == "-":
                continue
            cur.append(ln)
            if CHANGESET_CLOSE.search(ln.text):
                cur = None
    return blocks


def _a1(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        state = "unknown"  # unknown | none | existing | new
        reported = False
        seen_xml_ctx = False
        for ln in h.lines:
            opens = bool(CHANGESET_OPEN.search(ln.text))
            closes = bool(CHANGESET_CLOSE.search(ln.text))
            if opens:
                state = "new" if ln.kind == "+" else "existing"
                reported = False
            flag = False
            if state == "existing" and ln.kind in "+-":
                flag = True
            elif state == "unknown":
                if ln.kind == "-" and not closes:
                    flag = True
                elif ln.kind == "+" and seen_xml_ctx and not closes:
                    flag = True
            if flag and not reported:
                out.append(_finding(
                    fd, ln, "A1", "high",
                    "edit inside an existing changeSet; released changeSets must not "
                    "change, add a new changeSet instead"))
                reported = True
            if state == "unknown" and ln.kind == " " and ln.text.strip().startswith("<"):
                seen_xml_ctx = True
            if closes:
                state = "none"
                reported = False
    return out


def _a2(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        for block in _new_changesets(h):
            text = "\n".join(ln.text for ln in block)
            if DDL_TAG.search(text) and "<preConditions" not in text:
                out.append(_finding(
                    fd, block[0], "A2", "medium",
                    "changeSet with DDL has no <preConditions onFail=\"MARK_RAN\">"))
    return out


A3_CONSTRAINT = re.compile(r"<(?:addNotNullConstraint|addForeignKeyConstraint|addUniqueConstraint)\b")
A3_BACKFILL = re.compile(r"<(?:ext:)?update\b|<sql\b|sqlCheck")


def _a3(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        for block in _new_changesets(h):
            text = "\n".join(ln.text for ln in block)
            if A3_BACKFILL.search(text):
                continue
            hit = None
            for ln in block:
                if A3_CONSTRAINT.search(ln.text):
                    hit = ln
                    break
            if (hit is None and "<addColumn" in text and "<createTable" not in text
                    and "defaultValue" not in text):
                for ln in block:
                    if re.search(r'nullable\s*=\s*"false"', ln.text):
                        hit = ln
                        break
            if hit is not None:
                out.append(_finding(
                    fd, hit, "A3", "medium",
                    "constraint added with no backfill (<update>/<sql>/sqlCheck) in "
                    "the same changeSet; existing rows may violate it"))
    return out


A5_NAME_ATTRS = re.compile(
    r'<(?:column\s[^>]*?\bname|createTable\s[^>]*?\btableName|renameTable\s[^>]*?\bnewTableName|'
    r'renameColumn\s[^>]*?\bnewColumnName)\s*=\s*"(\w+)"')
A5_DBMS = re.compile(r'\bdbms\s*=\s*"([^"]*)"')


def _a5(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for ln in _added(fd):
        t = ln.text
        for m in A5_DBMS.finditer(t):
            engines = {e.strip().lower() for e in m.group(1).split(",")}
            if "mysql" in engines and not engines & {"mariadb", "postgresql"}:
                out.append(_finding(
                    fd, ln, "A5", "medium",
                    'dbms="mysql" only; changes must also run on PostgreSQL '
                    "(add postgresql/mariadb or use portable change types)"))
        if re.search(r"tinyint", t, re.I):
            out.append(_finding(
                fd, ln, "A5", "medium",
                "tinyint is MySQL-specific; use type=\"boolean\" or a portable type"))
        for m in A5_NAME_ATTRS.finditer(t):
            name = m.group(1)
            if name.lower() in RESERVED_WORDS:
                out.append(_finding(
                    fd, ln, "A5", "medium",
                    f"'{name}' is a reserved word on MySQL 8 / PostgreSQL; pick another name"))
    return out


for _cat, _conf, _fn in (("A1", "high", _a1), ("A2", "medium", _a2),
                         ("A3", "medium", _a3), ("A5", "medium", _a5)):
    _register(_cat, _conf, _is_liquibase_xml, _fn)


# ---------------------------------------------------------------------------
# Java checks (B1, B2, B5, C2, C3, D1, G1, G6, G7, G8, G9, H1, I1)
# ---------------------------------------------------------------------------


def _is_java(path: str) -> bool:
    return path.endswith(".java")


def _comment_or_blank(text: str) -> bool:
    t = text.strip()
    return not t or t.startswith(("//", "/*", "*"))


def _b1(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        view = _new_side(h)
        for i, ln in enumerate(view):
            if ln.kind != "+":
                continue
            if re.search(r"@(?:ManyToOne|OneToOne)\b", ln.text):
                window = " ".join(x.text for x in view[max(i - 1, 0):i + 3])
                if "FetchType.LAZY" not in window and "LAZY" not in window:
                    out.append(_finding(
                        fd, ln, "B1", "high",
                        "@ManyToOne/@OneToOne is EAGER by default in JPA; add fetch = FetchType.LAZY"))
            if re.search(r"orphanRemoval\s*=\s*true", ln.text):
                out.append(_finding(
                    fd, ln, "B1", "medium",
                    "orphanRemoval = true added; confirm it matches the old hbm cascade semantics exactly"))
    return out


COLLECTION_ASSIGN = re.compile(
    r"\bthis\.\w+\s*=\s*new\s+(?:Hash|Tree|Linked|Array)?(?:Set|List)\b")
SETTER_DECL = re.compile(r"\bvoid\s+set[A-Z]\w*\s*\(")


def _b2(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        view = _new_side(h)
        for i, ln in enumerate(view):
            if ln.kind != "+" or not COLLECTION_ASSIGN.search(ln.text):
                continue
            for prev in reversed(view[max(i - 8, 0):i]):
                if SETTER_DECL.search(prev.text):
                    out.append(_finding(
                        fd, ln, "B2", "medium",
                        "setter replaces a managed collection; clear() and addAll() instead"))
                    break
                if re.match(r"\s*(?:public|protected|private)\b.*\)\s*(?:throws [\w, .]+)?\s*\{", prev.text):
                    break
    return out


DISCARDED_CALL = re.compile(r"^\s*[\w.()]*\.(?:saveOrUpdate|merge)\(.*\)\s*;\s*$")


def _b5(fd: FileDiff) -> List[Finding]:
    return [
        _finding(fd, ln, "B5", "low",
                 "result of merge()/saveOrUpdate() is discarded; use the returned instance")
        for ln in _added(fd)
        if DISCARDED_CALL.match(ln.text) and "=" not in ln.text.split("(")[0]
        and not ln.text.strip().startswith("return")
    ]


C2_RE = re.compile(r"getAll\w*\(.*\)\.stream\(\)\.filter")


def _c2(fd: FileDiff) -> List[Finding]:
    return [_finding(fd, ln, "C2", "medium",
                     "filtering getAll...() results in Java; push the predicate into the query")
            for ln in _added(fd) if C2_RE.search(ln.text)]


C3_RE = re.compile(r"[\"'][^\"']*\b(?:lower|upper)\s*\(", re.I)


def _c3(fd: FileDiff) -> List[Finding]:
    return [_finding(fd, ln, "C3", "medium",
                     "lower()/upper() in a query defeats the index; rely on collation or a normalized column")
            for ln in _added(fd) if C3_RE.search(ln.text)]


def _d1(fd: FileDiff) -> List[Finding]:
    body = "\n".join(ln.text for h in fd.hunks for ln in _new_side(h))
    if re.search(r"\buuid\b|getUuid|getId\b", body, re.I):
        return []
    return [_finding(fd, ln, "D1", "low",
                     "compareTo() with no uuid/id tiebreak; equal sort keys collapse in a TreeSet")
            for ln in _added(fd) if re.search(r"\bint\s+compareTo\s*\(", ln.text)]


def _g1_applies(path: str) -> bool:
    return path.endswith("Service.java")


def _g1(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    in_api = "/api/" in "/" + fd.path and "/impl/" not in fd.path
    for h in fd.hunks:
        view = _new_side(h)
        is_interface = in_api or any(re.search(r"\binterface\b", x.text) for x in view)
        if not is_interface:
            continue
        for i, ln in enumerate(view):
            t = ln.text
            if ln.kind != "+" or _comment_or_blank(t) or t.strip().startswith(("@", "import", "package")):
                continue
            if re.search(r"\b(?:class|interface|enum)\b", t) or not re.match(
                    r"\s*(?:public\s+)?(?:default\s+)?[\w<>\[\],.? ]+?\s+\w+\s*\(", t):
                continue
            authorized = False
            for prev in reversed(view[max(i - 15, 0):i]):
                pt = prev.text.strip()
                if "@Authorized" in pt:
                    authorized = True
                    break
                if pt.endswith((";", "{", "}")):
                    break
            if not authorized:
                out.append(_finding(
                    fd, ln, "G1", "high",
                    "service method has no @Authorized; it fails open for any caller"))
    return out


G6_RES = [
    re.compile(r"get(?:Canonical|Absolute)?Path\(\)\s*\.startsWith\("),
    re.compile(r"toString\(\)\s*\.startsWith\("),
    re.compile(r"contains\(\s*\"\.\.\"\s*\)"),
]
G6_VAR = re.compile(r"\b\w*(?:[pP]ath|[dD]ir|[eE]ntryName|[fF]ilename)\w*\.startsWith\(")


def _g6(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for ln in _added(fd):
        t = ln.text
        hit = any(r.search(t) for r in G6_RES) or (
            G6_VAR.search(t) and not re.search(r"normalize\(|toPath\(|Paths\.get|Path\.of", t))
        if hit:
            out.append(_finding(
                fd, ln, "G6", "medium",
                "string/prefix path containment is bypassable; use Path.resolve().normalize() "
                "and Path.startsWith"))
    return out


G7_RE = re.compile(
    r"\b[vV]elocity\w*\.evaluate\(|SpelExpressionParser|StandardEvaluationContext")


def _g7(fd: FileDiff) -> List[Finding]:
    return [_finding(fd, ln, "G7", "high",
                     "template/expression evaluation of stored text; never evaluate untrusted input")
            for ln in _added(fd) if G7_RE.search(ln.text)]


def _g8(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        text = "\n".join(x.text for x in _new_side(h))
        for ln in h.lines:
            if ln.kind != "+":
                continue
            if "new XStream(" in ln.text:
                out.append(_finding(fd, ln, "G8", "medium",
                                    "new XStream() without a type allowlist; restrict permitted types"))
            elif "DocumentBuilderFactory.newInstance(" in ln.text and "setFeature" not in text:
                out.append(_finding(fd, ln, "G8", "medium",
                                    "DocumentBuilderFactory without setFeature; disable DTDs (XXE)"))
    return out


G9_RE = re.compile(
    r"(?:createQuery|createNativeQuery|createSQLQuery|executeSQL)\s*\(.*(?:\"\s*\+|\+\s*\")")


def _g9(fd: FileDiff) -> List[Finding]:
    return [_finding(fd, ln, "G9", "high",
                     "query built by string concatenation; bind parameters instead")
            for ln in _added(fd) if G9_RE.search(ln.text)]


def _h1(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        text = "\n".join(x.text for x in _new_side(h))
        if "setLenient(false)" in text:
            continue
        out.extend(_finding(fd, ln, "H1", "medium",
                            "SimpleDateFormat is lenient by default; call setLenient(false) or use java.time")
                   for ln in h.lines if ln.kind == "+" and "new SimpleDateFormat(" in ln.text)
    return out


def _i1_java(fd: FileDiff) -> List[Finding]:
    return [_finding(fd, ln, "I1", "high",
                     "test disabled with @Ignore/@Disabled; fix the test instead of weakening it")
            for ln in _added(fd) if re.match(r"\s*@(?:Ignore|Disabled)\b", ln.text)]


for _cat, _conf, _app, _fn in (
        ("B1", "high", _is_java, _b1), ("B2", "medium", _is_java, _b2),
        ("B5", "low", _is_java, _b5), ("C2", "medium", _is_java, _c2),
        ("C3", "medium", _is_java, _c3), ("D1", "low", _is_java, _d1),
        ("G1", "high", _g1_applies, _g1), ("G6", "medium", _is_java, _g6),
        ("G7", "high", _is_java, _g7), ("G8", "medium", _is_java, _g8),
        ("G9", "high", _is_java, _g9), ("H1", "medium", _is_java, _h1),
        ("I1", "high", _is_java, _i1_java)):
    _register(_cat, _conf, _app, _fn)


# ---------------------------------------------------------------------------
# Frontend checks (P4, P6, I1-js)
# ---------------------------------------------------------------------------


def _is_frontend(path: str) -> bool:
    return path.endswith((".ts", ".tsx", ".js", ".jsx"))


P6_RES = (re.compile(r"[=!]==?\s*t\("), re.compile(r"\bt\([^)]*\)\s*[=!]==?"))


def _p6(fd: FileDiff) -> List[Finding]:
    return [_finding(fd, ln, "P6", "medium",
                     "logic on translated text; compare stable codes/uuids, not t('...') output")
            for ln in _added(fd) if any(r.search(ln.text) for r in P6_RES)]


P4_RE = re.compile(r"\b\w+\[(?:index|idx|rowIndex|i)\]")


def _p4(fd: FileDiff) -> List[Finding]:
    out: List[Finding] = []
    for h in fd.hunks:
        text = "\n".join(x.text for x in _new_side(h))
        if "DataTable" not in text and not re.search(r"\brows?\b", text):
            continue
        out.extend(_finding(fd, ln, "P4", "low",
                            "row-index lookup into a data array; sorting/filtering reorders rows, look up by row id")
                   for ln in h.lines if ln.kind == "+" and P4_RE.search(ln.text))
    return out


I1_JS_RE = re.compile(r"\bxit\(|\bxdescribe\(|\b(?:it|describe|test)\.skip\(")


def _i1_js(fd: FileDiff) -> List[Finding]:
    return [_finding(fd, ln, "I1", "high",
                     "test skipped; fix the test instead of weakening it")
            for ln in _added(fd) if I1_JS_RE.search(ln.text)]


for _cat, _conf, _fn in (("P6", "medium", _p6), ("P4", "low", _p4), ("I1", "high", _i1_js)):
    _register(_cat, _conf, _is_frontend, _fn)


def run_checks(files: List[FileDiff]) -> List[Finding]:
    out: List[Finding] = []
    for fd in files:
        if fd.deleted:
            continue
        for check in CHECKS:
            if check.applies(fd.path):
                out.extend(check.run(fd))
    out.sort(key=lambda f: (f.path, f.line, f.cat))
    return out


# ---------------------------------------------------------------------------
# Output and CLI
# ---------------------------------------------------------------------------


def format_finding(f: Finding) -> str:
    return f"{f.path}:{f.line}  {f.cat}  {f.confidence}  {f.message}"


def summarize(found: List[Finding]) -> dict:
    counts: dict = {}
    for f in found:
        counts[f.cat] = counts.get(f.cat, 0) + 1
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Advisory OpenMRS pitfall review of a diff.")
    ap.add_argument("diff_file", nargs="?", help="diff file (default: stdin)")
    ap.add_argument("--repo", help="repository to diff")
    ap.add_argument("--base", help="base ref for --repo (runs git diff BASE...HEAD)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 0
    try:
        if args.repo:
            res = subprocess.run(
                ["git", "-C", args.repo, "diff", f"{args.base or 'HEAD~1'}...HEAD"],
                capture_output=True, text=True, errors="replace", check=True)
            text = res.stdout
        elif args.diff_file:
            with open(args.diff_file, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        else:
            text = sys.stdin.read()
        found = run_checks(parse_diff(text))
    except Exception as exc:  # advisory tool: never fail the caller
        print(f"review_diff: {exc}", file=sys.stderr)
        return 0
    counts = summarize(found)
    if args.json:
        print(json.dumps({
            "findings": [f.__dict__ for f in found],
            "summary": counts,
        }, indent=2))
    else:
        for f in found:
            print(format_finding(f))
        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none"
        print(f"review_diff: {len(found)} finding(s): {summary}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
