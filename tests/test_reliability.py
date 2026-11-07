import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from meta.reliability import alpha


def test_krippendorff_alpha_known_values():
    # Two coders, A = 1 1 0 0, B = 1 0 0 0: Do = 2/8, De = 30/56, alpha = 8/15.
    assert alpha([[1, 1], [1, 0], [0, 0], [0, 0]], interval=False) == pytest.approx(8 / 15)
    assert alpha([[1, 1, 1], [0, 0], [0.5, 0.5]], interval=True) == pytest.approx(1.0)
    assert alpha([[1, 0], [0, 1]], interval=False) < 0
    assert alpha([[1, 1], [1, 1]], interval=False) is None  # no variation: undefined
