import tempfile
import unittest
from pathlib import Path

from dockerfile_gen.arm64_pipeline import atomic_write
from dockerfile_gen.tasks import write_generated


class ArchitectureLayoutTests(unittest.TestCase):
    def test_atomic_refresh_keeps_alias_and_replaces_arm_target(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory)
            (task / "arm").mkdir()
            target = task / "arm/Dockerfile"
            target.write_text("old")
            alias = task / "Dockerfile"
            alias.symlink_to("arm/Dockerfile")
            atomic_write(alias, "new")
            self.assertTrue(alias.is_symlink())
            self.assertEqual(target.read_text(), "new")
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_upstream_generation_cannot_overwrite_arm_variant(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory)
            for arch in ("arm", "x86"):
                (task / arch).mkdir()
                (task / arch / "Dockerfile").write_text(arch)
            (task / "Dockerfile").symlink_to("arm/Dockerfile")
            write_generated(task, "new x86", "evaluation")
            self.assertEqual((task / "arm/Dockerfile").read_text(), "arm")
            self.assertEqual((task / "x86/Dockerfile").read_text(), "new x86")
            self.assertTrue((task / "Dockerfile").is_symlink())


if __name__ == "__main__":
    unittest.main()
