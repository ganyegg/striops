"""Tests for the outlier screen that keeps extract artefacts out of claims."""
from striops.core.anomaly import (
    MIN_HISTORY,
    describe_break,
    is_suspect,
    suspect_indices,
    suspect_ratio,
)


def test_short_series_is_never_judged():
    """A newly wired feed gets the benefit of the doubt, not a guess."""
    values = [10.0, 400.0]
    assert suspect_indices(values) == []
    assert suspect_ratio(values, 1) is None


def test_steady_series_has_no_suspects():
    values = [10_000.0, 10_500.0, 9_800.0, 11_200.0, 10_100.0, 10_900.0, 10_400.0]
    assert suspect_indices(values) == []


def test_spike_several_times_the_trailing_median_is_flagged():
    """The June 2026 refuse shape: a stable run, then a multiple."""
    values = [10_930.0, 12_068.0, 11_453.0, 11_605.0, 9_738.0, 13_518.0, 28_604.0]
    assert is_suspect(values, len(values) - 1)
    note = describe_break(values, len(values) - 1)
    assert note and "above" in note and "Verify" in note


def test_collapse_to_a_fraction_is_flagged():
    """A near-empty month is as broken as a spike — 336 against a ~10k baseline."""
    values = [10_936.0, 10_329.0, 10_085.0, 8_394.0, 8_645.0, 8_971.0, 336.0]
    assert is_suspect(values, len(values) - 1)
    note = describe_break(values, len(values) - 1)
    assert note and "below" in note


def test_trending_series_is_not_mistaken_for_an_artefact():
    """Steady growth must not trip the screen — only breaks out of trailing range do."""
    values = [6.0e9, 6.4e9, 6.9e9, 7.2e9, 7.4e9, 7.7e9, 8.9e9]
    assert not is_suspect(values, len(values) - 1)


def test_seasonal_swing_is_not_an_artefact():
    """Cape Town dam storage halves across a summer without the extract breaking."""
    values = [73.14, 84.34, 92.49, 87.63, 80.25, 70.47, 61.35]
    assert suspect_indices(values) == []


def test_window_is_trailing_not_whole_series():
    """Only the preceding `MIN_HISTORY` points set the baseline."""
    values = [1.0] * MIN_HISTORY + [100.0] * MIN_HISTORY + [105.0]
    # The step up is flagged where it happens...
    assert is_suspect(values, MIN_HISTORY)
    # ...but once it is the established level, the next point is normal again.
    assert not is_suspect(values, len(values) - 1)
