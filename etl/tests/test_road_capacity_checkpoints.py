import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(os.environ.get("ROAD_CAPACITY_SOURCE_ROOT", ROOT))
sys.path[:0] = [str(ROOT / "etl"), str(MAIN / "etl"), str(MAIN / "backend/src")]

from road_capacity.checkpoints import fingerprint, verify_checkpoints, write_state


class CheckpointTests(unittest.TestCase):
    def test_same_inputs_and_implementation_reuse_checkpoint(self):
        expected = fingerprint(
            "weights", {"normalization_base": 100}, {"source_revision": "a"}
        )
        self.assertEqual(
            expected,
            fingerprint(
                "weights", {"normalization_base": 100}, {"source_revision": "a"}
            ),
        )
        self.assertNotEqual(
            expected,
            fingerprint(
                "weights", {"normalization_base": 101}, {"source_revision": "a"}
            ),
        )
        state = {"stages": {"weights": 2}, "stage_fingerprints": {"weights": expected}}
        verify_checkpoints(state, {"normalization_base": 100}, {"source_revision": "a"})
        self.assertEqual(state["stages"], {"weights": 2})

    def test_changed_code_requires_explicit_restart(self):
        state = {
            "stages": {"weights": 2},
            "stage_fingerprints": {"weights": "previous"},
        }
        with (
            patch("road_capacity.checkpoints.fingerprint", return_value="changed"),
            self.assertRaisesRegex(ValueError, "--restart-from weights"),
        ):
            verify_checkpoints(state, {}, {})

    def test_restart_invalidates_dependent_stages_only(self):
        state = {
            "stages": {"weights": 2, "matrices": 3, "indices": 4, "atlas": 5},
            "stage_fingerprints": {
                name: name for name in ["weights", "matrices", "indices", "atlas"]
            },
        }
        with patch(
            "road_capacity.checkpoints.fingerprint",
            side_effect=lambda stage, reference, source: stage,
        ):
            verify_checkpoints(state, {}, {}, restart="matrices")
        self.assertEqual(state["stages"], {"weights": 2})
        self.assertEqual(state["stage_fingerprints"], {"weights": "weights"})

    def test_unsigned_earlier_checkpoint_is_explicitly_marked_adopted(self):
        state = {"stages": {"weights": 2}}
        with patch("road_capacity.checkpoints.fingerprint", return_value="current"):
            verify_checkpoints(state, {}, {})
        self.assertEqual(state["adopted_unversioned_checkpoints"], ["weights"])
        self.assertEqual(state["stage_fingerprints"], {"weights": "current"})

    def test_invalid_state_does_not_overwrite_prior_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            write_state(path, {"stages": {}})
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                write_state(path, {"invalid": float("nan")})
            self.assertEqual(path.read_bytes(), original)
