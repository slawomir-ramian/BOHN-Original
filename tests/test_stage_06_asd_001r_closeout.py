import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ASD001RCloseoutTests(unittest.TestCase):
    def test_full_result_and_separate_inventory(self):
        validator = load_module(
            ROOT / "tools" / "validate_asd_001r_closeout.py",
            "asd001r_closeout_validator",
        )
        result = validator.validate()
        self.assertEqual(result["fits"], 40)
        self.assertEqual(result["grade"], "STRUCTURAL_RECONSTRUCTION_CONFIRMED")
        self.assertEqual(result["original_inventory_rows"], 115)
        self.assertEqual(result["supplementary_inventory_rows"], 1)


if __name__ == "__main__":
    unittest.main()
