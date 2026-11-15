from datetime import datetime, timezone

import pytest

from ytauto.scoring import (acceleration, is_short, outlier_score, parse_duration, viral_score,
                            views_per_hour)

NOW = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize("iso,secs", [("PT45S", 45), ("PT1M5S", 65), ("PT2H", 7200),
                                       ("P1DT1S", 86401), ("", 0), ("bad", 0)])
def test_parse_duration(iso, secs):
    assert parse_duration(iso) == secs


def test_is_short():
    assert is_short(59) and is_short(180)
    assert not is_short(181) and not is_short(0)


def test_views_per_hour():
    assert views_per_hour(1000, "2026-11-15T02:00:00Z", NOW) == 100
    # vídeos de menos de 1 hora cuentan como 1 hora
    assert views_per_hour(500, "2026-11-15T11:59:00Z", NOW) == 500


def test_outlier_score():
    assert outlier_score(10_000, [1000, 2000, 3000]) == 5
    assert outlier_score(10_000, [1000, 2000]) is None
    assert outlier_score(10_000, [0, 0, 0]) is None


def test_acceleration_and_score():
    assert acceleration(100, 200) == 2
    assert acceleration(None, 200) == 1
    assert viral_score(0, 10) == 0
    assert viral_score(999, 10) == pytest.approx(30.0)
    assert viral_score(999, 1000) == viral_score(999, 50)  # outlier acotado a 50
