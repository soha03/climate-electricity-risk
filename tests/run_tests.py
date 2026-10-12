import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_analysis import ElectricityMarketAnalysisTests


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ElectricityMarketAnalysisTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
