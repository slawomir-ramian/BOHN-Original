from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PROTOCOL_PATH = ROOT / "experiments" / "14_sota002_high_resolution_supplementary" / "stage16_protocol.json"
HISTORICAL = ROOT / "experiments" / "10_sota_and_scaling" / "SOTA-002" / "historical" / "source_from_monograph.py"
EXPECTED_SHA256 = "ba576b945052cc70b44dcecaece3bc90eb728787ecf86f9cece1d17217a4b116"

try:
    import torch
except (ImportError, OSError):
    torch = None


class Stage16StaticTests(unittest.TestCase):
    def test_historical_source_is_unchanged(self):
        self.assertTrue(HISTORICAL.exists())
        self.assertEqual(hashlib.sha256(HISTORICAL.read_bytes()).hexdigest(), EXPECTED_SHA256)

    def test_protocol_is_frozen_and_explicit(self):
        protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(protocol["protocol_id"], "STAGE_16_SOTA002_HIGH_RESOLUTION_V1")
        self.assertEqual(protocol["square_resolutions"], [28, 112, 448, 1024, 2048, 3840])
        self.assertEqual(protocol["rectangular_resolutions_hw"][-1], [2160, 3840])
        self.assertEqual(protocol["units"], ["SOTA-002R", "SOTA-002H"])

    def test_external_observations_are_not_runtime_targets(self):
        runtime = (ROOT / "tools" / "run_stage_16_unit.py").read_text(encoding="utf-8")
        self.assertNotIn("61.8", runtime)
        self.assertNotIn("29.75", runtime)
        self.assertNotIn("ResNet", runtime)

    def test_registration_is_idempotent(self):
        module_path = ROOT / "tools" / "register_stage_16_supplementary.py"
        spec = importlib.util.spec_from_file_location("stage16_registration", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "supplementary.csv"
            first = module.register(target)
            second = module.register(target)
            self.assertEqual(first, (2, 2))
            self.assertEqual(second, (0, 2))

    def test_red_is_reserved_for_errors(self):
        for script in ROOT.glob("*STAGE_16*.ps1"):
            text = script.read_text(encoding="utf-8-sig")
            for line in text.splitlines():
                if "ForegroundColor Red" in line:
                    self.assertTrue("ERROR" in line.upper() or "BLAD" in line.upper())


@unittest.skipIf(torch is None, "PyTorch is unavailable")
class Stage16TorchTests(unittest.TestCase):
    def test_historical_parameter_contracts(self):
        from bohn_original.sota_scaling import FractalSBOHN, parameter_count

        expected = {28: 54298, 112: 101338, 448: 853978}
        for resolution, count in expected.items():
            self.assertEqual(parameter_count(FractalSBOHN(resolution, 1, 10, 16, 4)), count)

    def test_hierarchical_model_is_resolution_independent(self):
        from bohn_original.stage16_high_resolution import HierarchicalFractalSBOHN, parameter_count

        model = HierarchicalFractalSBOHN().eval()
        count = parameter_count(model)
        self.assertGreater(count, 0)
        for height, width in ((28, 28), (112, 112), (64, 96)):
            with torch.inference_mode():
                tokens = model.encode_tokens(torch.randn(1, 1, height, width))
                output = model.relational_core(tokens)
            self.assertEqual(tuple(tokens.shape), (1, 16, 16))
            self.assertEqual(tuple(output.shape), (1, 10))
            self.assertTrue(torch.isfinite(output).all().item())
            self.assertEqual(parameter_count(model), count)


if __name__ == "__main__":
    unittest.main()

