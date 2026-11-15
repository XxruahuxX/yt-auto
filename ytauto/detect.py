"""Recolección de vídeos recientes y cálculo de su puntuación de viralidad."""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta, timezone

from . import db
from .api import QuotaExceeded, YouTubeAPI
from .scoring import (acceleration, hours_since, is_short, parse_duration,
                      parse_time, viral_score, views_per_hour)

CHANNEL_CACHE_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize(item: dict, source: str, niche: str | None = None) -> dict:
    sn, cd = item.get("snippet", {}), item.get("contentDetails", {})
    duration = parse_duration(cd.get("duration", ""))
    thumbs = sn.get("thumbnails", {})
    thumb = (thumbs.get("maxres") or thumbs.get("high") or thumbs.get("default") or {}).get("url")
    return {
        "id": item["id"],
        "channel_id": sn.get("channelId"),
        "title": sn.get("title"),
        "description": (sn.get("description") or "")[:2000],
        "tags": json.dumps(sn.get("tags", []), ensure_ascii=False),
        "category_id": sn.get("categoryId"),
        "published_at": sn.get("publishedAt"),
        "duration_s": duration,
        "is_short": int(is_short(duration)),
        "thumbnail": thumb,
        "source": source,
        "niche": niche,
    }


def store(conn, items: list[dict], source: str, niche: str | None, taken_at: str) -> int:
    for it in items:
        db.upsert_video(conn, normalize(it, source, niche))
        st = it.get("statistics", {})
        db.add_snapshot(conn, it["id"], taken_at, int(st.get("viewCount", 0)),
                        int(st.get("likeCount", 0)), int(st.get("commentCount", 0)))
    conn.commit()
    return len(items)


def collect(api: YouTubeAPI, conn, config: dict, log=print) -> dict:
    """Descarga tendencias y búsquedas por nicho, guarda snapshots y actualiza canales."""
    taken_at = _iso(_now())
    max_age = config.get("max_age_days", 7)
    published_after = _iso(_now() - timedelta(days=max_age))
    stats = {"trending": 0, "search": 0, "channels": 0}

    try:
        for region in config.get("regions", ["ES"]):
            items = api.most_popular(region, pages=config.get("trending_pages", 1))
            stats["trending"] += store(conn, items, f"trending:{region}", None, taken_at)

        for niche, spec in config.get("niches", {}).items():
            ids = []
            for kw in spec.get("keywords", []):
                ids += api.search_ids(kw, published_after, region=spec.get("region", "ES"),
                                      language=spec.get("language", "es"))
            stats["search"] += store(conn, api.videos(ids), "search", niche, taken_at)
            log(f"  {niche}: {len(set(ids))} vídeos")

        # re-snapshot de vídeos jóvenes ya conocidos, para medir aceleración
        known = [r["id"] for r in conn.execute(
            "SELECT id FROM videos WHERE published_at >= ?", (published_after,))]
        store(conn, api.videos(known), "resnapshot", None, taken_at)

        stats["channels"] = refresh_channels(api, conn, config.get("max_channels_per_run", 150))
    except QuotaExceeded as exc:
        log(f"Cuota agotada, paro aquí: {exc}")
    stats["quota_used"] = api.used
    return stats


def refresh_channels(api: YouTubeAPI, conn, limit: int) -> int:
    """Actualiza suscriptores y mediana de vistas (últimos 30 vídeos) de canales sin datos recientes."""
    stale_before = _iso(_now() - timedelta(days=CHANNEL_CACHE_DAYS))
    rows = conn.execute(
        """SELECT DISTINCT v.channel_id FROM videos v LEFT JOIN channels c ON c.id = v.channel_id
           WHERE v.channel_id IS NOT NULL AND (c.id IS NULL OR c.updated_at < ?) LIMIT ?""",
        (stale_before, limit),
    ).fetchall()
    ids = [r[0] for r in rows]
    if not ids:
        return 0
    for ch in api.channels(ids):
        st, cd = ch.get("statistics", {}), ch.get("contentDetails", {})
        uploads = cd.get("relatedPlaylists", {}).get("uploads")
        median = None
        if uploads:
            recent = api.videos(api.recent_uploads(uploads, 30))
            views = [int(v.get("statistics", {}).get("viewCount", 0)) for v in recent]
            median = statistics.median(views) if len(views) >= 3 else None
        db.upsert_channel(conn, {
            "id": ch["id"], "title": ch["snippet"].get("title"),
            "subscribers": int(st.get("subscriberCount", 0)) if not st.get("hiddenSubscriberCount") else None,
            "video_count": int(st.get("videoCount", 0)), "uploads_playlist": uploads,
            "median_views": median, "updated_at": _iso(_now()),
        })
    conn.commit()
    return len(ids)


def score(conn, max_age_days: int = 7, now: datetime | None = None) -> list[dict]:
    """Devuelve los vídeos jóvenes con sus métricas, ordenados por puntuación."""
    now = now or _now()
    cutoff = _iso(now - timedelta(days=max_age_days))
    rows = conn.execute(
        """SELECT v.*, c.title AS channel_title, c.subscribers, c.median_views
           FROM videos v LEFT JOIN channels c ON c.id = v.channel_id
           WHERE v.published_at >= ?""",
        (cutoff,),
    ).fetchall()
    out = []
    for r in rows:
        snaps = db.last_two_snapshots(conn, r["id"])
        if not snaps:
            continue
        latest = snaps[0]
        vph = views_per_hour(latest["views"], r["published_at"], parse_time(latest["taken_at"]))
        accel = 1.0
        if len(snaps) == 2:
            prev = snaps[1]
            prev_vph = views_per_hour(prev["views"], r["published_at"], parse_time(prev["taken_at"]))
            # VPH en el intervalo entre snapshots frente al VPH medio anterior
            gap_h = (parse_time(latest["taken_at"]) - parse_time(prev["taken_at"])).total_seconds() / 3600
            if gap_h >= 1:
                interval_vph = (latest["views"] - prev["views"]) / gap_h
                accel = acceleration(prev_vph, interval_vph)
        median = r["median_views"]
        outlier = latest["views"] / median if median else None
        out.append({
            "id": r["id"], "url": f"https://youtu.be/{r['id']}", "title": r["title"],
            "channel": r["channel_title"], "subscribers": r["subscribers"], "niche": r["niche"],
            "source": r["source"], "is_short": bool(r["is_short"]), "duration_s": r["duration_s"],
            "published_at": r["published_at"],
            "age_h": round(hours_since(r["published_at"], now), 1),
            "views": latest["views"], "likes": latest["likes"], "comments": latest["comments"],
            "vph": round(vph, 1), "outlier": round(outlier, 2) if outlier else None,
            "accel": round(accel, 2), "score": viral_score(vph, outlier, accel),
            "thumbnail": r["thumbnail"],
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out
