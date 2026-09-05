import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

from tests.script_module_support import load_script_module


class ScriptModuleSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.script_path = Path(self.temporary_directory.name) / "fixture_script.py"
        self.module_name = "script_module_support_test_fixture"
        self.had_previous_module = self.module_name in sys.modules
        self.previous_module = sys.modules.pop(self.module_name, None)
        self.addCleanup(self._restore_previous_module)

    def _restore_previous_module(self) -> None:
        if self.had_previous_module:
            sys.modules[self.module_name] = self.previous_module
        else:
            sys.modules.pop(self.module_name, None)

    def test_failed_load_removes_new_module_and_restores_sys_path(self) -> None:
        self.script_path.write_text("raise SystemExit(3)\n")
        original_sys_path = sys.path.copy()

        with self.assertRaisesRegex(SystemExit, "3"):
            load_script_module(self.module_name, self.script_path)

        self.assertNotIn(self.module_name, sys.modules)
        self.assertEqual(sys.path, original_sys_path)

    def test_failed_load_restores_previous_module(self) -> None:
        previous_module = ModuleType(self.module_name)
        sys.modules[self.module_name] = previous_module
        self.script_path.write_text("raise RuntimeError('failure')\n")

        with self.assertRaisesRegex(RuntimeError, "failure"):
            load_script_module(self.module_name, self.script_path)

        self.assertIs(sys.modules[self.module_name], previous_module)

    def test_failed_load_restores_previous_none_sentinel(self) -> None:
        sys.modules[self.module_name] = None
        self.script_path.write_text("raise RuntimeError('failure')\n")

        with self.assertRaisesRegex(RuntimeError, "failure"):
            load_script_module(self.module_name, self.script_path)

        self.assertIsNone(sys.modules[self.module_name])

    def test_successful_load_retains_replacement_module(self) -> None:
        previous_module = ModuleType(self.module_name)
        sys.modules[self.module_name] = previous_module
        self.script_path.write_text("loaded = True\n")

        module = load_script_module(self.module_name, self.script_path)

        self.assertIs(sys.modules[self.module_name], module)
        self.assertIsNot(module, previous_module)
        self.assertTrue(module.loaded)


if __name__ == "__main__":
    unittest.main()
