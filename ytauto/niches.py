"""Ranking de nichos: dónde canales pequeños consiguen vídeos muy por encima de su media."""
from __future__ import annotations

import math
import statistics
from collections import defaultdict

OUTLIER_THRESHOLD = 5.0
SMALL_CHANNEL_SUBS = 50_000


def rank_niches(scored: list[dict], min_videos: int = 20) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for v in scored:
        if v.get("niche"):
            groups[v["niche"]].append(v)

    ranking = []
    for niche, vids in groups.items():
        with_outlier = [v for v in vids if v["outlier"] is not None]
        if len(with_outlier) < min_videos:
            continue
        outliers = [v for v in with_outlier if v["outlier"] >= OUTLIER_THRESHOLD]
        small_outliers = [v for v in outliers
                          if v["subscribers"] is not None and v["subscribers"] < SMALL_CHANNEL_SUBS]
        outlier_rate = len(outliers) / len(with_outlier)
        small_rate = len(small_outliers) / len(with_outlier)
        median_vph = statistics.median(v["vph"] for v in vids)
        shorts_share = sum(v["is_short"] for v in vids) / len(vids)
        # Oportunidad: muchos outliers, sobre todo de canales pequeños, con demanda (VPH) alta.
        opportunity = (outlier_rate + 2 * small_rate) * math.log10(median_vph + 10)
        ranking.append({
            "niche": niche,
            "videos": len(vids),
            "outlier_rate": round(outlier_rate, 3),
            "small_channel_outlier_rate": round(small_rate, 3),
            "median_vph": round(median_vph, 1),
            "shorts_share": round(shorts_share, 2),
            "opportunity": round(opportunity, 3),
            "top_examples": [v["url"] for v in sorted(outliers, key=lambda x: -x["score"])[:3]],
        })
    ranking.sort(key=lambda r: r["opportunity"], reverse=True)
    return ranking
