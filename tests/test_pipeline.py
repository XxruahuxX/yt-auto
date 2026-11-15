"""Prueba de extremo a extremo con una API falsa (sin red ni cuota real)."""
from datetime import datetime, timedelta, timezone

from ytauto import db
from ytauto.detect import collect, score
from ytauto.niches import rank_niches


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeAPI:
    def __init__(self, views_for):
        self.used = 0
        self.views_for = views_for
        now = datetime.now(timezone.utc)
        self.published = _iso(now - timedelta(hours=10))

    def _video(self, vid, channel):
        return {"id": vid,
                "snippet": {"channelId": channel, "title": f"Vídeo {vid}",
                            "publishedAt": self.published, "categoryId": "28"},
                "contentDetails": {"duration": "PT50S"},
                "statistics": {"viewCount": str(self.views_for(vid))}}

    def most_popular(self, region, pages=1):
        return []

    def search_ids(self, kw, published_after, region="ES", language="es"):
        return [f"{kw}-{i}" for i in range(25)]

    def videos(self, ids):
        return [self._video(i, "small" if i.endswith("-0") else "big") for i in ids]

    def channels(self, ids):
        subs = {"small": 2_000, "big": 1_000_000}
        return [{"id": c, "snippet": {"title": c},
                 "statistics": {"subscriberCount": str(subs[c]), "videoCount": "100"},
                 "contentDetails": {"relatedPlaylists": {"uploads": f"UU{c}"}}} for c in ids]

    def recent_uploads(self, playlist, limit=30):
        return [f"hist-{playlist}-{i}" for i in range(5)]


def test_pipeline_ranks_small_channel_outlier(tmp_path):
    def views_for(vid):
        if vid.startswith("hist-UUsmall"):
            return 1_000
        if vid.startswith("hist-UUbig"):
            return 100_000
        return 50_000  # todos los vídeos nuevos tienen 50k vistas

    conn = db.connect(tmp_path / "t.db")
    config = {"regions": [], "niches": {"tech": {"keywords": ["prog"]}}}
    stats = collect(FakeAPI(views_for), conn, config, log=lambda *_: None)
    assert stats["search"] == 25 and stats["channels"] == 2

    rows = score(conn)
    top = rows[0]
    assert top["id"] == "prog-0"  # canal pequeño: 50k frente a mediana de 1k = x50
    assert top["outlier"] == 50 and top["is_short"]
    assert 4_900 < top["vph"] < 5_100

    ranking = rank_niches(rows, min_videos=10)
    assert ranking[0]["niche"] == "tech"
    assert ranking[0]["small_channel_outlier_rate"] == round(1 / 25, 3)
