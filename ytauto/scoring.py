"""Métricas de viralidad: vistas por hora, outlier score y puntuación final."""
from __future__ import annotations

import math
import re
import statistics
from datetime import datetime, timezone

SHORT_MAX_SECONDS = 180

_DURATION_RE = re.compile(
    r"^P(?:(?P<d>\d+)D)?(?:T(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?)?$"
)


def parse_duration(iso: str) -> int:
    """Convierte una duración ISO 8601 de la API (p. ej. PT1M5S) a segundos."""
    match = _DURATION_RE.match(iso or "")
    if not match:
        return 0
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    return parts["d"] * 86400 + parts["h"] * 3600 + parts["m"] * 60 + parts["s"]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def is_short(duration_s: int) -> bool:
    return 0 < duration_s <= SHORT_MAX_SECONDS


def hours_since(published_at: str, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    hours = (now - parse_time(published_at)).total_seconds() / 3600
    return max(hours, 1.0)  # evita dividir por casi cero en vídeos recién subidos


def views_per_hour(views: int, published_at: str, now: datetime | None = None) -> float:
    return views / hours_since(published_at, now)


def outlier_score(views: int, channel_views: list[int]) -> float | None:
    """Vistas del vídeo / mediana de vistas de los vídeos recientes del canal."""
    sample = [v for v in channel_views if v is not None]
    if len(sample) < 3:
        return None
    median = statistics.median(sample)
    if median <= 0:
        return None
    return views / median


def acceleration(vph_first: float | None, vph_second: float | None) -> float:
    if not vph_first or not vph_second:
        return 1.0
    return vph_second / vph_first


def viral_score(vph: float, outlier: float | None, accel: float = 1.0) -> float:
    """log10(VPH) × min(outlier, 50) × aceleración (acotada a [0.5, 3])."""
    if vph <= 0:
        return 0.0
    out = min(outlier if outlier is not None else 1.0, 50.0)
    acc = min(max(accel, 0.5), 3.0)
    return round(math.log10(vph + 1) * out * acc, 3)
