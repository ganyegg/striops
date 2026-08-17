"""Robust outlier screening for monthly operational series.

Public extracts change shape without warning: a re-categorised C3 feed or a
partial month can move a count by several multiples overnight. Striops must
not present that as a service finding, so a point that breaks out of its own
trailing range is marked for verification rather than asserted as a change.

The test is deliberately blunt — ratio against the trailing median, not a
z-score. Operational counts are neither normal nor stationary, and a rule an
executive can restate in one sentence survives a room better than one they
have to take on faith.
"""
from __future__ import annotations

from statistics import median

# Points needed before the screen will judge anything. Short series (a feed
# that has only just been wired) are left alone rather than guessed at.
MIN_HISTORY = 6

# A point this many times above — or this fraction below — its trailing median
# is treated as an extract artefact until a human confirms otherwise.
DEVIATION_FACTOR = 2.0


def _trailing_median(values: list[float], index: int, window: int) -> float | None:
    prior = values[max(0, index - window) : index]
    if len(prior) < window:
        return None
    baseline = median(prior)
    return baseline if baseline > 0 else None


def suspect_ratio(
    values: list[float],
    index: int,
    window: int = MIN_HISTORY,
) -> float | None:
    """Ratio of ``values[index]`` to its trailing median, or None if unjudgeable."""
    if index < 0 or index >= len(values):
        return None
    baseline = _trailing_median(values, index, window)
    if baseline is None:
        return None
    return values[index] / baseline


def is_suspect(
    values: list[float],
    index: int,
    factor: float = DEVIATION_FACTOR,
    window: int = MIN_HISTORY,
) -> bool:
    ratio = suspect_ratio(values, index, window)
    if ratio is None:
        return False
    return ratio >= factor or ratio <= 1 / factor


def suspect_indices(
    values: list[float],
    factor: float = DEVIATION_FACTOR,
    window: int = MIN_HISTORY,
) -> list[int]:
    return [i for i in range(len(values)) if is_suspect(values, i, factor, window)]


def describe_break(
    values: list[float],
    index: int,
    window: int = MIN_HISTORY,
    period_label: str | None = None,
) -> str | None:
    """One sentence naming the break, for use in place of a change claim.

    ``period_label`` names the month that broke, and must be passed whenever the
    break is *not* in the latest reading. The Pulse screens the comparison
    baseline as well as the latest point, so a note hardcoded to "Latest
    reading" ended up quoting the previous month's ratio next to the current
    month's figure: "10,205 requests/month in Jul 2026 — Latest reading is 2.5x
    above the median (11,529)", which is both wrong and self-evidently wrong to
    anyone doing the division.
    """
    ratio = suspect_ratio(values, index, window)
    if ratio is None:
        return None
    baseline = _trailing_median(values, index, window)
    if baseline is None:
        return None
    if ratio >= 1:
        shape = f"{ratio:.1f}x above"
    else:
        shape = f"{1 / ratio:.1f}x below"
    tail = (
        f"the median of the previous {window} periods ({baseline:,.0f}) — likely an "
        f"extract change rather than a service change. "
    )
    if period_label:
        return (
            f"The {period_label} reading it is measured against is {shape} {tail}"
            f"No month-on-month change can be read from it. "
            f"Verify with the publisher before acting on it."
        )
    return f"Latest reading is {shape} {tail}Verify with the publisher before acting on it."
