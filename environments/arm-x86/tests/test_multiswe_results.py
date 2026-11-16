import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "results", Path(__file__).resolve().parents[1] / "scripts/summarize_multiswe.py"
)
results = importlib.util.module_from_spec(spec)
spec.loader.exec_module(results)


class ResultParserTests(unittest.TestCase):
    def test_build_error_has_no_observed_test_passes(self):
        for language in ("java", "go", "rust"):
            self.assertEqual(
                results.parse("error: dependency download failed", language), {}
            )

    def test_duplicate_success_does_not_hide_failure(self):
        self.assertEqual(
            results.parse("test one ... FAILED\ntest one ... ok\n", "rust"),
            {"one": "FAIL"},
        )

    def test_go_subtest_names_are_preserved(self):
        self.assertEqual(
            results.parse("    --- PASS: Test_refreshRun/no_hostname (0.00s)", "go"),
            {"Test_refreshRun/no_hostname": "PASS"},
        )

    def test_java_aggregates_errors_as_failures(self):
        line = "[ERROR] Tests run: 2, Failures: 0, Errors: 1, Skipped: 0, Time elapsed: 0.1 s -- in pkg.SomeTest"
        self.assertEqual(results.parse(line, "java"), {"pkg.SomeTest": "FAIL"})
