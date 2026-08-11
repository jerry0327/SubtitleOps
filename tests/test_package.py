import ast
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 CI
    import tomli as tomllib

import subtitleops

ROOT = Path(__file__).resolve().parents[1]


class PackageContractTests(unittest.TestCase):
    def test_package_and_project_versions_match(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(subtitleops.__version__, project["project"]["version"])

    def test_version_assignment_remains_literal_for_release_validation(self):
        module = ast.parse((ROOT / "src/subtitleops/__init__.py").read_text(encoding="utf-8"))
        version = next(
            ast.literal_eval(node.value)
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
        )
        self.assertEqual(version, subtitleops.__version__)

    def test_typed_package_marker_is_present(self):
        self.assertTrue((ROOT / "src/subtitleops/py.typed").is_file())


if __name__ == "__main__":
    unittest.main()
