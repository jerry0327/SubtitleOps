import unittest
from pathlib import Path

from subtitleops.rules import LINT_RULE_CODES, RULES, iter_rules


class RuleRegistryTests(unittest.TestCase):
    def test_codes_are_unique_uppercase_identifiers(self):
        rules = iter_rules()
        self.assertEqual(len(rules), len(RULES))
        self.assertEqual(len({rule.code for rule in rules}), len(rules))
        for rule in rules:
            self.assertEqual(rule.code, rule.code.upper())
            self.assertTrue(rule.code.replace("_", "").isalnum())

    def test_lint_code_set_excludes_operational_diagnostics(self):
        self.assertIn("OVERLAP", LINT_RULE_CODES)
        self.assertNotIn("PARSE_ERROR", LINT_RULE_CODES)
        self.assertEqual(
            LINT_RULE_CODES,
            frozenset(rule.code for rule in iter_rules() if rule.category != "operational"),
        )

    def test_every_help_uri_has_a_documented_anchor(self):
        documentation = (Path(__file__).parents[1] / "docs" / "rules.md").read_text(encoding="utf-8")
        for rule in iter_rules():
            anchor = rule.code.lower().replace("_", "-")
            self.assertIn(f'<a id="{anchor}"></a>', documentation)
            self.assertTrue(rule.help_uri.endswith(f"#{anchor}"))


if __name__ == "__main__":
    unittest.main()
