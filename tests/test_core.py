import pytest
from math import isclose
from src.removespikes import RemoveSpikes


class TestCalculateAngle:
    @pytest.mark.parametrize(
        "a, b, c, expected_angle",
        [
            ((0, 0), (1, 0), (2, 0), 180.0),  # Straight horizontal line
            ((0, 0), (0, 1), (0, 2), 180.0),  # Straight vertical line
            ((0, 0), (1, 1), (2, 2), 180.0),  # Straight diagonal line
            ((0, 0), (1, 1), (0, 2), 90.0),  # Right angle
            ((0, 0), (1, 0), (1, 1), 90.0),  # Right angle
            ((0, 0), (1, 0), (1, -1), 90.0),  # Right angle
            ((0, 0), (1, 0), (0.5, 0.5), 45.0),  # 45 degree angle
            ((0, 0), (0, 1), (-1, 0), 45.0),  # 45 degree angle
            ((0, 0), (1, 1), (2, 1), 135.0),  # 135 degree angle
            ((0, 0), (1, 0), (2, 1), 135.0),  # 135 degree angle
        ],
    )
    def test_calculate_angle(self, a, b, c, expected_angle):
        angle = RemoveSpikes._calculate_angle(a, b, c)
        assert isclose(
            angle, expected_angle, abs_tol=2e-6
        ), f"Expected {expected_angle}, got {angle}"

    @pytest.mark.parametrize(
        "a, b, c",
        [
            ((0, 0), (1, 1), (1, 1)),  # Duplicate points
            ((1, 1), (1, 1), (2, 2)),  # Duplicate points
            ((1, 1), (0, 0), (0, 0)),  # Duplicate points
        ],
    )
    def test_calculate_angle_zero_division(self, a, b, c):
        with pytest.raises(ZeroDivisionError):
            RemoveSpikes._calculate_angle(a, b, c)
