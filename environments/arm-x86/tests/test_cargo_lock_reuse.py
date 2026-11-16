import json
import shutil
import tempfile
import unittest
from pathlib import Path

from dockerfile_gen import _get_dockerfile
from dockerfile_gen.arm64 import generate
from dockerfile_gen.cargo_lock import pin_x86_dockerfile, repository_lock
from dockerfile_gen.tasks import TASKS_DIR, load_task, write_generated

ELIGIBLE = (
    "burntsushi__ripgrep-2209", "burntsushi__ripgrep-2576",
    "sharkdp__bat-2393", "sharkdp__bat-2650",
)
TOKIO = ("tokio-rs__tokio-4867", "tokio-rs__tokio-6603",
         "tokio-rs__tokio-6724", "tokio-rs__tokio-6838")


class CargoLockReuseTests(unittest.TestCase):
    def render(self, task, snapshot=None):
        lock = json.loads((task / "arm64-lock.json").read_text())
        return generate(task, base_image=lock["base_image"],
                        cargo_lock=snapshot if snapshot is not None else
                        (task / "Cargo.lock.arm64").read_text())

    def test_both_architectures_reuse_the_audited_lock_and_fail_fast(self):
        for name in ELIGIBLE:
            with self.subTest(task=name):
                task = TASKS_DIR / name
                digest = repository_lock(task, load_task(task))
                arm = self.render(task)
                x86 = pin_x86_dockerfile(_get_dockerfile(load_task(task)), digest)
                for arch, text in (("arm", arm), ("x86", x86)):
                    self.assertEqual(text, (task / arch / "Dockerfile").read_text())
                    self.assertNotIn(" > Cargo.lock", text)
                    self.assertNotIn("[[package]]", text)
                    self.assertIn("cargo test --locked", text)
                    self.assertEqual(text.count(digest), 2)
                    self.assertLess(text.index(digest), text.index("cargo test --locked"))
                    self.assertGreater(text.rindex(digest), text.index("cargo test --locked"))

    def test_missing_upstream_locks_keep_the_exact_tokio_snapshots(self):
        for name in TOKIO:
            with self.subTest(task=name):
                task = TASKS_DIR / name
                snapshot = (task / "Cargo.lock.arm64").read_text()
                self.assertIsNone(repository_lock(task, load_task(task), snapshot))
                text = self.render(task)
                self.assertIn(snapshot.rstrip(), text)
                self.assertEqual(text.count(" > Cargo.lock"), 1)
                self.assertEqual(text, (task / "arm/Dockerfile").read_text())

    def test_changed_snapshot_cannot_silently_reuse_the_repository_lock(self):
        task = TASKS_DIR / ELIGIBLE[0]
        altered = (task / "Cargo.lock.arm64").read_text() + "# changed\n"
        with self.assertRaisesRegex(ValueError, "snapshot differs"):
            self.render(task, altered)

    def test_evidence_for_another_commit_is_rejected(self):
        task = TASKS_DIR / ELIGIBLE[0]
        instance = load_task(task)
        instance["base_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "task checkout"):
            repository_lock(task, instance)

    def test_without_equivalence_evidence_the_snapshot_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / ELIGIBLE[0]
            shutil.copytree(TASKS_DIR / task.name, task, symlinks=True)
            (task / "evidence/cargo-lock-source.json").unlink()
            snapshot = (task / "Cargo.lock.arm64").read_text()
            text = self.render(task)
            self.assertIn(snapshot.rstrip(), text)
            self.assertIn("cargo test --locked", text)

    def test_x86_regeneration_preserves_arm_and_original_upstream_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / ELIGIBLE[0]
            shutil.copytree(TASKS_DIR / task.name, task, symlinks=True)
            arm = (task / "arm/Dockerfile").read_bytes()
            original = (task / "Dockerfile.amd").read_bytes()
            expected_x86 = (task / "x86/Dockerfile").read_bytes()
            evaluation = (task / "eval.sh").read_bytes()
            write_generated(task, _get_dockerfile(load_task(task)), evaluation.decode())
            self.assertEqual((task / "x86/Dockerfile").read_bytes(), expected_x86)
            self.assertEqual((task / "arm/Dockerfile").read_bytes(), arm)
            self.assertEqual((task / "Dockerfile.amd").read_bytes(), original)
            self.assertEqual((task / "eval.sh").read_bytes(), evaluation)
            self.assertTrue((task / "Dockerfile.amd").is_symlink())

    def test_repeated_x86_enforcement_does_not_duplicate_checks(self):
        task = TASKS_DIR / ELIGIBLE[0]
        text = (task / "x86/Dockerfile").read_text()
        self.assertEqual(pin_x86_dockerfile(text, repository_lock(task, load_task(task))), text)


if __name__ == "__main__":
    unittest.main()
