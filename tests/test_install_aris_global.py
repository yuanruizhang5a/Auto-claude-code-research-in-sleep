#!/usr/bin/env python3
"""Tests for tools/install_aris_global.sh."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "install_aris_global.sh"


class InstallArisGlobalTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="aris-global-test-"))
        self.repo = self.tmpdir / "repo"
        self.claude_home = self.tmpdir / "claude-home"
        self.skills_dir = self.repo / "skills"
        self.skills_dir.mkdir(parents=True)
        self.claude_home.mkdir(parents=True)
        self._make_skill("alpha")
        self._make_skill("beta")
        (self.skills_dir / "shared-references").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_skill(self, name: str) -> None:
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")

    def _run(self, *args, check=True):
        cmd = [
            "bash",
            str(SCRIPT),
            "--quiet",
            "--aris-repo",
            str(self.repo),
            "--claude-home",
            str(self.claude_home),
            *args,
        ]
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            check=check,
        )

    def test_fresh_install_creates_symlinks_and_manifest(self):
        self._run()

        alpha_link = self.claude_home / "skills" / "alpha"
        beta_link = self.claude_home / "skills" / "beta"
        manifest = self.claude_home / "aris-global" / "installed-skills.txt"

        self.assertTrue(alpha_link.is_symlink())
        self.assertTrue(beta_link.is_symlink())
        self.assertEqual(alpha_link.resolve(), (self.skills_dir / "alpha").resolve())
        self.assertTrue(manifest.exists())
        manifest_text = manifest.read_text(encoding="utf-8")
        self.assertIn("alpha", manifest_text)
        self.assertIn("beta", manifest_text)
        self.assertIn("shared-references", manifest_text)

    def test_rerun_reconciles_removed_upstream_skill(self):
        self._run()
        shutil.rmtree(self.skills_dir / "beta")

        self._run()

        self.assertFalse((self.claude_home / "skills" / "beta").exists())
        manifest_text = (self.claude_home / "aris-global" / "installed-skills.txt").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("\tbeta\t", manifest_text)

    def test_uninstall_removes_only_managed_entries(self):
        self._run()
        foreign = self.claude_home / "skills" / "foreign-pack"
        foreign_target = self.tmpdir / "foreign-pack"
        foreign_target.mkdir()
        foreign.symlink_to(foreign_target)

        self._run("--uninstall")

        self.assertFalse((self.claude_home / "skills" / "alpha").exists())
        self.assertTrue(foreign.is_symlink())
        self.assertFalse((self.claude_home / "aris-global" / "installed-skills.txt").exists())
        self.assertTrue((self.claude_home / "aris-global" / "installed-skills.txt.prev").exists())

    def test_conflict_real_directory_is_not_overwritten(self):
        conflict_dir = self.claude_home / "skills" / "alpha"
        conflict_dir.mkdir(parents=True)

        result = self._run(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(conflict_dir.is_dir())
        self.assertFalse((self.claude_home / "aris-global" / "installed-skills.txt").exists())

    def test_replace_link_updates_managed_symlink(self):
        self._run()
        new_repo = self.tmpdir / "repo-v2"
        new_skills = new_repo / "skills"
        new_skills.mkdir(parents=True)
        for name in ("alpha", "beta"):
            skill_dir = new_skills / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name} v2\n", encoding="utf-8")
        (new_skills / "shared-references").mkdir()

        result = subprocess.run(
            [
                "bash",
                str(SCRIPT),
                "--quiet",
                "--aris-repo",
                str(new_repo),
                "--claude-home",
                str(self.claude_home),
                "--replace-link",
                "alpha",
                "--replace-link",
                "beta",
                "--replace-link",
                "shared-references",
            ],
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual((self.claude_home / "skills" / "alpha").resolve(), (new_skills / "alpha").resolve())

    def test_dry_run_does_not_mutate_filesystem(self):
        result = self._run("--dry-run")

        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.claude_home / "skills").exists())
        self.assertFalse((self.claude_home / "aris-global").exists())

    def test_symlinked_parent_is_refused(self):
        real_root = self.tmpdir / "real-claude"
        real_root.mkdir()
        linked_home = self.tmpdir / "linked-claude"
        linked_home.symlink_to(real_root)

        result = subprocess.run(
            [
                "bash",
                str(SCRIPT),
                "--quiet",
                "--aris-repo",
                str(self.repo),
                "--claude-home",
                str(linked_home),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is a symlink", result.stderr)


if __name__ == "__main__":
    unittest.main()
