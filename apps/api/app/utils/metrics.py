"""Utility functions for metrics calculations."""

from __future__ import annotations

from ..exceptions import InvalidRatingError, MetricsError


def calculate_satisfaction_score(ratings: list[int]) -> float:
    """Calculate a normalized satisfaction score from ratings.

    Args:
        ratings: A list of integer ratings from 1 to 5.

    Returns:
        The average rating normalized between 0 and 1.

    Raises:
        InvalidRatingError: If ratings are empty or contain invalid values.
        MetricsError: If calculation fails unexpectedly.
    """
    if not isinstance(ratings, list) or not ratings:
        raise InvalidRatingError("ratings must be a non-empty list of integers")

    if any(not isinstance(r, int) or r < 1 or r > 5 for r in ratings):
        raise InvalidRatingError("each rating must be an int between 1 and 5")

    try:
        return sum(ratings) / (len(ratings) * 5)
    except Exception as exc:  # pragma: no cover - defensive
        raise MetricsError("failed to calculate satisfaction score") from exc
