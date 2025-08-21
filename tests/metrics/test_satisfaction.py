"""Tests for satisfaction score metric utility."""

from __future__ import annotations

import pytest

from apps.api.app.exceptions import InvalidRatingError
from apps.api.app.utils.metrics import calculate_satisfaction_score


def test_calculate_satisfaction_score_success() -> None:
    """Satisfaction score should exceed 0.9 for high ratings."""
    ratings = [5, 5, 4, 5]
    score = calculate_satisfaction_score(ratings)
    assert score > 0.9


@pytest.mark.parametrize(
    "ratings",
    [
        [],
        [0],
        [6],
        ["a"],
        None,
    ],
)
def test_calculate_satisfaction_score_invalid(ratings: list[int] | None) -> None:
    """Invalid inputs should raise ``InvalidRatingError``."""
    with pytest.raises(InvalidRatingError):
        calculate_satisfaction_score(ratings)  # type: ignore[arg-type]
