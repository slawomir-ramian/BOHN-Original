from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bohn_original.foundation import (
    ReversibleRMIGLayer,
    compute_orbit_histogram,
    compute_z3_orbits,
    test_gradient_input as gradient_input_check,
    test_gradient_weights as gradient_weights_check,
    test_invariance_batch as invariance_batch_check,
    test_reversibility as reversibility_check,
    z3_permutation,
)


class FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orbits = compute_z3_orbits()

    def test_b001_orbits_and_burnside(self):
        self.assertEqual(len(self.orbits), 24)
        self.assertEqual(sum(len(orbit) == 1 for orbit in self.orbits), 4)
        self.assertEqual(sum(len(orbit) == 3 for orbit in self.orbits), 20)
        self.assertEqual([o[0] for o in self.orbits if len(o) == 1], [0, 21, 42, 63])
        self.assertTrue(all(z3_permutation(z3_permutation(z3_permutation(s))) == s for s in range(64)))

    def test_b002_histogram_dimension(self):
        phi = compute_orbit_histogram(np.zeros(64), self.orbits)
        self.assertEqual(phi.shape, (72,))

    def test_b003_exact_roundtrip(self):
        layer = ReversibleRMIGLayer(seed=42)
        X = np.random.RandomState(42).randn(8, 64)
        self.assertTrue(np.array_equal(layer.inverse(layer.forward(X)), X))

    def test_b004_gradients(self):
        np.random.seed(42)
        layer = ReversibleRMIGLayer(seed=42)
        self.assertEqual(reversibility_check(layer), 0.0)
        self.assertLess(gradient_input_check(layer)[0], 1e-6)
        self.assertLess(gradient_weights_check(layer)[0], 1e-6)

    def test_b009_invariance(self):
        max_error, _, _ = invariance_batch_check(self.orbits, n_samples=100)
        self.assertLess(max_error, 1e-13)

    def test_historical_sources_match_provenance_hashes(self):
        base = ROOT / "experiments" / "02_bohn_foundation"
        for number in range(1, 10):
            experiment = base / f"B-{number:03d}"
            provenance = json.loads((experiment / "provenance.json").read_text(encoding="utf-8"))
            raw = (experiment / "historical" / "source_from_monograph.py").read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            digest = hashlib.sha256(raw[:-1].encode("utf-8")).hexdigest()
            self.assertEqual(digest, provenance["historical_source_sha256"])


if __name__ == "__main__":
    unittest.main()
