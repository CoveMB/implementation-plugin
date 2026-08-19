import importlib.util
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills" / "implementing-staged-plans" / "scripts"
SCRIPT_PATH = SCRIPT_ROOT / "task_prompt.py"


class TaskPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("task_prompt", SCRIPT_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load task prompt from {SCRIPT_PATH}")
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        sys.path.insert(0, str(SCRIPT_ROOT))
        try:
            spec.loader.exec_module(cls.module)
        finally:
            sys.path.remove(str(SCRIPT_ROOT))

    def test_render_and_parse_are_byte_exact(self) -> None:
        command = {
            "schema_version": "example-command/v1",
            "program_id": "ARCHIVE-PROGRAM",
            "nested": {"zeta": 2, "alpha": 1},
        }

        prompt = self.module.render_exact_prompt(command)

        self.assertTrue(prompt.startswith("$implementing-staged-plans\n\n```json\n"))
        self.assertTrue(prompt.endswith("```\n"))
        self.assertEqual(
            self.module.parse_exact_prompt(prompt, "example-command/v1"), command
        )
        self.assertEqual(self.module.render_exact_prompt(command), prompt)

    def test_noncanonical_or_appended_transport_is_rejected(self) -> None:
        command = {"schema_version": "example-command/v1", "value": 1}
        prompt = self.module.render_exact_prompt(command)
        cases = (
            prompt.replace('  "value": 1', '    "value": 1'),
            "Quoted context\n\n" + prompt,
            prompt + "Additional scope\n",
            prompt.replace("```json", "```JSON"),
        )
        for candidate in cases:
            with self.subTest(candidate=candidate[:30]):
                with self.assertRaisesRegex(ValueError, "exact prompt"):
                    self.module.parse_exact_prompt(candidate, "example-command/v1")

    def test_schema_mismatch_and_prompt_self_digest_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "schema"):
            self.module.parse_exact_prompt(
                self.module.render_exact_prompt({"schema_version": "other/v1"}),
                "example-command/v1",
            )
        for field in ("submitted_prompt_sha256", "prompt_sha256"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "self-digest"):
                    self.module.render_exact_prompt(
                        {"schema_version": "example-command/v1", field: "0" * 64}
                    )

    def test_self_digest_nested_in_a_tuple_is_rejected_before_rendering(self) -> None:
        command = {
            "schema_version": "example-command/v1",
            "items": ({"prompt_sha256": "0" * 64},),
        }

        with self.assertRaisesRegex(ValueError, "self-digest"):
            self.module.render_exact_prompt(command)


if __name__ == "__main__":
    unittest.main()
