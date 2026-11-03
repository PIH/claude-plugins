import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import review_diff as rd  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def load(name):
    with open(os.path.join(FIXTURES, name + ".diff"), encoding="utf-8") as f:
        return f.read()


def findings(name):
    return rd.run_checks(rd.parse_diff(load(name)))


def hits(name, cat):
    return [f for f in findings(name) if f.cat == cat]


class ParserTests(unittest.TestCase):
    def test_parse_simple_hunk(self):
        text = (
            "diff --git a/Foo.java b/Foo.java\n"
            "index 1..2 100644\n"
            "--- a/Foo.java\n"
            "+++ b/Foo.java\n"
            "@@ -10,4 +10,5 @@ class Foo {\n"
            " keep1\n"
            "-old\n"
            "+new1\n"
            "+new2\n"
            " keep2\n"
        )
        files = rd.parse_diff(text)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].path, "Foo.java")
        lines = files[0].hunks[0].lines
        self.assertEqual([l.kind for l in lines], [" ", "-", "+", "+", " "])
        self.assertEqual([l.new_lineno for l in lines], [10, None, 11, 12, 13])
        self.assertEqual([l.old_lineno for l in lines], [10, 11, None, None, 12])
        self.assertEqual(lines[2].text, "new1")

    def test_parser_handles_binary_rename_delete(self):
        files = rd.parse_diff(load("binary_rename_delete"))
        self.assertEqual(len(files), 3)
        self.assertEqual(rd.run_checks(files), [])


class LiquibaseTests(unittest.TestCase):
    def test_a1_edit_inside_existing_changeset(self):
        h = hits("a1_edit_existing", "A1")
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0].confidence, "high")

    def test_a1_edit_when_hunk_starts_mid_changeset(self):
        h = hits("a1_edit_mid_changeset", "A1")
        self.assertEqual([f.confidence for f in h], ["high"])

    def test_a1_added_include_not_flagged(self):
        self.assertEqual(hits("a1_include_added", "A1"), [])

    def test_a1_new_changeset_not_flagged(self):
        self.assertEqual(hits("a1_new_changeset", "A1"), [])

    def test_a2_ddl_without_precondition(self):
        h = hits("a2_ddl_no_precondition", "A2")
        self.assertEqual([f.confidence for f in h], ["medium"])
        self.assertEqual(hits("a2_ddl_with_precondition", "A2"), [])

    def test_a3_not_null_without_backfill(self):
        h = hits("a3_not_null_no_backfill", "A3")
        self.assertEqual([f.confidence for f in h], ["medium"])
        self.assertEqual(hits("a3_not_null_with_backfill", "A3"), [])

    def test_a5_dbms_mysql_only(self):
        h = hits("a5_dbms_mysql_only", "A5")
        self.assertEqual([f.confidence for f in h], ["medium"])
        self.assertEqual(hits("a5_dbms_all_engines", "A5"), [])

    def test_a5_reserved_word_column(self):
        h = hits("a5_reserved_word_column", "A5")
        self.assertEqual(len(h), 3)
        msgs = " ".join(f.message for f in h)
        for word in ("rank", "condition", "order"):
            self.assertIn(word, msgs)
        self.assertEqual(hits("a5_portable_ok", "A5"), [])

    def test_a5_insert_existing_column_not_flagged(self):
        self.assertEqual(hits("a5_insert_existing_column_ok", "A5"), [])

    def test_a5_tinyint(self):
        h = hits("a5_tinyint", "A5")
        self.assertEqual(len(h), 1)
        self.assertIn("tinyint", h[0].message)

    def test_reserved_words_bundled(self):
        for w in ("rank", "condition", "order", "value", "group", "key", "rows",
                  "window", "user", "to", "from", "select", "table", "column",
                  "index", "range", "interval", "read", "write", "system"):
            self.assertIn(w, rd.RESERVED_WORDS)

    def test_liquibase_checks_only_apply_to_liquibase_xml(self):
        text = load("a1_edit_existing").replace("liquibase-update-to-latest.xml", "pom.xml")
        self.assertEqual(rd.run_checks(rd.parse_diff(text)), [])


def confs(name, cat):
    return [f.confidence for f in hits(name, cat)]


class JavaTests(unittest.TestCase):
    def test_b1_manytoone_without_lazy(self):
        self.assertEqual(confs("b1_manytoone_no_lazy", "B1"), ["high"])

    def test_b1_lazy_present_ok(self):
        self.assertEqual(hits("b1_lazy_present", "B1"), [])
        self.assertEqual(hits("b1_lazy_next_line", "B1"), [])

    def test_b1_orphan_removal_added(self):
        self.assertEqual(confs("b1_orphan_removal", "B1"), ["medium"])

    def test_b2_setter_replaces_collection(self):
        self.assertEqual(confs("b2_setter_replaces_collection", "B2"), ["medium"])
        self.assertEqual(hits("b2_clear_and_add_ok", "B2"), [])

    def test_b5_discarded_merge(self):
        self.assertEqual(confs("b5_discarded_merge", "B5"), ["low"])
        self.assertEqual(hits("b5_merge_result_used", "B5"), [])

    def test_b5_saveorupdate_not_flagged(self):
        self.assertEqual(hits("b5_saveorupdate_ok", "B5"), [])

    def test_c2_getall_stream_filter(self):
        self.assertEqual(confs("c2_getall_stream_filter", "C2"), ["medium"])
        self.assertEqual(hits("c2_sql_filter_ok", "C2"), [])

    def test_c3_lower_in_hql(self):
        self.assertEqual(confs("c3_lower_in_hql", "C3"), ["medium"])
        self.assertEqual(hits("c3_tolowercase_ok", "C3"), [])

    def test_d1_compareto_without_tiebreak(self):
        self.assertEqual(confs("d1_compareto_no_tiebreak", "D1"), ["low"])
        self.assertEqual(hits("d1_compareto_uuid_tiebreak", "D1"), [])

    def test_g1_service_method_without_authorized(self):
        h = hits("g1_no_authorized", "G1")
        self.assertEqual([f.confidence for f in h], ["high"])
        self.assertEqual(h[0].line, 35)
        self.assertEqual(hits("g1_authorized_ok", "G1"), [])

    def test_g1_annotation_above_javadoc_ok(self):
        self.assertEqual(hits("g1_annotation_above_javadoc_ok", "G1"), [])

    def test_g1_javadoc_with_link_and_long_javadoc_ok(self):
        self.assertEqual(hits("g1_link_javadoc_ok", "G1"), [])
        self.assertEqual(hits("g1_long_javadoc_ok", "G1"), [])

    def test_g1_javadoc_does_not_hide_previous_member(self):
        self.assertEqual(confs("g1_javadoc_after_previous_member", "G1"), ["high"])

    def test_g1_concrete_class_ignored(self):
        self.assertEqual(hits("g1_concrete_class_ok", "G1"), [])
        self.assertEqual(hits("g1_body_lines_no_class_ctx_ok", "G1"), [])

    def test_g1_multiline_signature(self):
        self.assertEqual(confs("g1_multiline_signature", "G1"), ["high"])

    def test_g1_non_service_file_ignored(self):
        self.assertEqual(hits("g1_non_service_file", "G1"), [])

    def test_g6_string_startswith_path(self):
        self.assertEqual(confs("g6_startswith_path", "G6"), ["medium"])
        self.assertEqual(hits("g6_path_normalize_ok", "G6"), [])

    def test_g7_velocity_evaluate(self):
        self.assertEqual(confs("g7_velocity_evaluate", "G7"), ["high"])
        self.assertEqual(hits("g7_velocity_clean", "G7"), [])

    def test_g8_new_xstream(self):
        self.assertEqual(confs("g8_new_xstream", "G8"), ["medium"])

    def test_g8_documentbuilder_needs_setfeature(self):
        self.assertEqual(confs("g8_dbf_no_setfeature", "G8"), ["medium"])
        self.assertEqual(hits("g8_dbf_with_setfeature_ok", "G8"), [])

    def test_g9_concatenated_query(self):
        self.assertEqual(confs("g9_concatenated_query", "G9"), ["high"])
        self.assertEqual(hits("g9_bound_param_ok", "G9"), [])

    def test_h1_simpledateformat_lenient(self):
        self.assertEqual(confs("h1_simpledateformat_lenient", "H1"), ["medium"])
        self.assertEqual(hits("h1_simpledateformat_strict_ok", "H1"), [])

    def test_i1_ignore_added(self):
        self.assertEqual(confs("i1_ignore_added", "I1"), ["high"])
        self.assertEqual(confs("i1_disabled_added", "I1"), ["high"])
        self.assertEqual(hits("i1_no_ignore", "I1"), [])


class FrontendTests(unittest.TestCase):
    def test_p6_translated_comparison(self):
        self.assertEqual(confs("p6_translated_comparison", "P6"), ["medium"])
        self.assertEqual(hits("p6_translated_display_ok", "P6"), [])

    def test_p4_row_index_lookup(self):
        self.assertEqual(confs("p4_row_index_lookup", "P4"), ["low"])
        self.assertEqual(hits("p4_find_by_id_ok", "P4"), [])

    def test_i1_xit_skip(self):
        self.assertEqual(confs("i1_xit_skip", "I1"), ["high"])
        self.assertEqual(confs("i1_it_skip", "I1"), ["high"])
        self.assertEqual(hits("i1_js_clean", "I1"), [])

    def test_frontend_checks_ignore_java_paths(self):
        text = load("p6_translated_comparison").replace("visit-table.component.tsx", "Visit.java")
        self.assertEqual(rd.run_checks(rd.parse_diff(text)), [])


class CliTests(unittest.TestCase):
    def run_main(self, argv):
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = rd.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_output_line_format_and_exit_code(self):
        path = os.path.join(FIXTURES, "i1_ignore_added.diff")
        rc, out, _ = self.run_main([path])
        self.assertEqual(rc, 0)
        self.assertEqual(
            out.strip(),
            "api/src/test/java/org/openmrs/api/ThingServiceTest.java:51  I1  high  "
            "test disabled with @Ignore/@Disabled; fix the test instead of weakening it")

    def test_json_output(self):
        import json
        rc, out, _ = self.run_main(["--json", os.path.join(FIXTURES, "i1_ignore_added.diff")])
        data = json.loads(out)
        self.assertEqual(rc, 0)
        self.assertEqual(data["findings"][0]["cat"], "I1")
        self.assertEqual(data["summary"], {"I1": 1})

    def test_missing_file_still_exits_zero(self):
        rc, out, err = self.run_main(["/nonexistent/x.diff"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertIn("review_diff", err)


if __name__ == "__main__":
    unittest.main()
