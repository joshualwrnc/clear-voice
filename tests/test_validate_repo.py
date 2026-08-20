import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
VALIDATOR = TESTS_DIR / "validate_repo.py"


VALID_SKILL = """---
name: clear-voice
description: Use on 'Clear Voice' writing that needs a concise, evidence-led rewrite.
license: CC-BY-4.0
---
# Clear Voice

Use this skill to make writing direct and human.

See [the guide](references/guide.md), [examples](references/examples.md), and [notes](references/notes.md).
"""

VALID_README = """# Clear Voice

Choose This reply, This conversation, or Moving forward.

Current-client and profile persistence boundary: this repository does not persist current-client data or profile data.

## Related Writing Styles

- Plain language

External author, source repository, and license notes: adapted with attribution from the author and source repository under the stated license.

Caveman is untested, persistent, and auto-trigger behavior is not guaranteed.

Claude verification limitation: Claude cannot verify behavior in this environment.

The documentation states its boundaries plainly and does not make product claims.
"""

LICENSE = """Clear Voice

Copyright 2026 Clear Voice contributors

Attribution is required. This work is shared under the applicable license.
"""
NOTICE = """Clear Voice NOTICE

Copyright 2026 Clear Voice contributors
Attribution notice for the Clear Voice materials.
"""
LICENSE_CODE = """MIT License

Copyright (c) 2026 Clear Voice contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software...
"""


class ValidatorTests(unittest.TestCase):
    def make_repo(self):
        root = Path(tempfile.mkdtemp(prefix="clear-voice-")).resolve()
        (root / "references").mkdir()
        (root / "README.md").write_text(VALID_README, encoding="utf-8")
        (root / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
        (root / "LICENSE").write_text(LICENSE, encoding="utf-8")
        (root / "NOTICE.md").write_text(NOTICE, encoding="utf-8")
        (root / "LICENSE-CODE").write_text(LICENSE_CODE, encoding="utf-8")
        for name in ("guide.md", "examples.md", "notes.md"):
            (root / "references" / name).write_text("# Reference\n", encoding="utf-8")
        self.addCleanup(shutil.rmtree, root)
        return root

    def run_validator(self, root):
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR), str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(proc.stdout, proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def test_valid_fixture_passes_with_structured_json(self):
        code, result = self.run_validator(self.make_repo())
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual([], result["errors"])
        self.assertIn("checks", result)

    def test_real_duration_choices_are_required(self):
        root = self.make_repo()
        (root / "README.md").write_text(VALID_README.replace(
            "This reply, This conversation, or Moving forward",
            "15 minutes, 30 minutes, or 60 minutes",
        ), encoding="utf-8")
        code, result = self.run_validator(root)
        self.assertNotEqual(code, 0)
        self.assertTrue(any("three duration choices" in error for error in result["errors"]))

    def test_use_on_skill_description_is_accepted(self):
        root = self.make_repo()
        code, result = self.run_validator(root)
        self.assertEqual(code, 0, result["errors"])

    def test_required_negative_disclosures_are_not_positive_claims(self):
        root = self.make_repo()
        (root / "README.md").write_text(VALID_README +
            "\nClear Voice is not affiliated with or endorsed by any vendor.\n",
            encoding="utf-8")
        code, result = self.run_validator(root)
        self.assertEqual(code, 0, result["errors"])

    def test_positive_affiliation_claim_is_still_rejected(self):
        root = self.make_repo()
        (root / "README.md").write_text(VALID_README +
            "\nClear Voice is officially affiliated with a vendor.\n",
            encoding="utf-8")
        code, result = self.run_validator(root)
        self.assertNotEqual(code, 0)
        self.assertTrue(any("compatibility" in error for error in result["errors"]))

    def test_missing_required_file_fails(self):
        root = self.make_repo()
        (root / "NOTICE.md").unlink()
        code, result = self.run_validator(root)
        self.assertNotEqual(code, 0)
        self.assertFalse(result["ok"])
        self.assertTrue(any("NOTICE.md" in error for error in result["errors"]))

    def test_invalid_content_and_policy_failures_are_reported(self):
        root = self.make_repo()
        (root / "SKILL.md").write_text(
            "---\nname: wrong\ndescription: vague\nlicense: MIT\n---\n\n"
            "See [missing](references/missing.md) and /Users/example/private.txt.\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text("We are officially affiliated and compatible.", encoding="utf-8")
        (root / "LICENSE-CODE").write_text("Proprietary", encoding="utf-8")
        (root / "references" / "extra.md").write_text("extra", encoding="utf-8")
        code, result = self.run_validator(root)
        self.assertNotEqual(code, 0)
        self.assertGreaterEqual(len(result["errors"]), 5)
        joined = "\n".join(result["errors"])
        for expected in ("frontmatter", "reference", "absolute", "README", "MIT", "exactly"):
            self.assertIn(expected, joined)

    def test_forbidden_vendored_and_automation_paths_fail(self):
        root = self.make_repo()
        (root / "attention-span.md").write_text("vendor", encoding="utf-8")
        (root / ".github").mkdir()
        (root / ".github" / "workflow.yml").write_text("name: CI", encoding="utf-8")
        (root / "install.sh").write_text("#!/bin/sh", encoding="utf-8")
        code, result = self.run_validator(root)
        self.assertNotEqual(code, 0)
        joined = "\n".join(result["errors"])
        self.assertIn("vendored", joined)
        self.assertIn("automation", joined)
        self.assertIn("install", joined)

    def test_fresh_dist_package_passes(self):
        import zipfile
        root = self.make_repo()
        (root / "dist").mkdir()
        with zipfile.ZipFile(root / "dist" / "clear-voice.skill", "w") as zf:
            for name in ("SKILL.md", "NOTICE.md", "LICENSE", "README.md"):
                zf.writestr(f"clear-voice/{name}", (root / name).read_bytes())
            for ref in sorted((root / "references").iterdir()):
                zf.writestr(f"clear-voice/references/{ref.name}", ref.read_bytes())
        code, result = self.run_validator(root)
        self.assertEqual(code, 0, result["errors"])
        self.assertTrue(result["checks"]["dist_package_fresh"])

    def test_stale_dist_package_fails(self):
        import zipfile
        root = self.make_repo()
        (root / "dist").mkdir()
        with zipfile.ZipFile(root / "dist" / "clear-voice.skill", "w") as zf:
            zf.writestr("clear-voice/SKILL.md", "outdated content")
        code, result = self.run_validator(root)
        self.assertNotEqual(code, 0)
        self.assertTrue(any("stale" in error for error in result["errors"]))

    def test_default_root_is_parent_of_tests_directory(self):
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(proc.stdout)
        result = json.loads(proc.stdout)
        self.assertIn("ok", result)


if __name__ == "__main__":
    unittest.main()
