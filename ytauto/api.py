"""Cliente mínimo de YouTube Data API v3 con contador de cuota."""
from __future__ import annotations

import os
from typing import Iterable, Iterator

import requests

BASE = "https://www.googleapis.com/youtube/v3"

# Coste en unidades por llamada (cuota por defecto: 10.000/día).
COST = {"search": 100, "videos": 1, "channels": 1, "playlistItems": 1, "videoCategories": 1}


class QuotaExceeded(RuntimeError):
    pass


class YouTubeAPI:
    def __init__(self, api_key: str | None = None, budget: int = 9000, session=None):
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Falta YOUTUBE_API_KEY (ponla en .env o en el entorno).")
        self.budget = budget
        self.used = 0
        self.http = session or requests.Session()

    def _get(self, resource: str, **params) -> dict:
        cost = COST[resource]
        if self.used + cost > self.budget:
            raise QuotaExceeded(f"Presupuesto de cuota agotado ({self.used}/{self.budget}).")
        params["key"] = self.api_key
        resp = self.http.get(f"{BASE}/{resource}", params=params, timeout=30)
        self.used += cost
        if resp.status_code == 403 and "quota" in resp.text.lower():
            raise QuotaExceeded(resp.text)
        resp.raise_for_status()
        return resp.json()

    # --- descubrimiento ---
    def most_popular(self, region: str, category_id: str | None = None, pages: int = 1) -> list[dict]:
        items, token = [], None
        for _ in range(pages):
            params = dict(part="snippet,statistics,contentDetails", chart="mostPopular",
                          regionCode=region, maxResults=50)
            if category_id:
                params["videoCategoryId"] = category_id
            if token:
                params["pageToken"] = token
            data = self._get("videos", **params)
            items += data.get("items", [])
            token = data.get("nextPageToken")
            if not token:
                break
        return items

    def search_ids(self, query: str, published_after: str, region: str = "ES",
                   language: str = "es", duration: str | None = None) -> list[str]:
        params = dict(part="id", q=query, type="video", order="viewCount", maxResults=50,
                      publishedAfter=published_after, regionCode=region,
                      relevanceLanguage=language)
        if duration:
            params["videoDuration"] = duration  # short (<4 min), medium, long
        data = self._get("search", **params)
        return [it["id"]["videoId"] for it in data.get("items", []) if it["id"].get("videoId")]

    # --- detalle ---
    def videos(self, ids: Iterable[str]) -> list[dict]:
        out = []
        for chunk in _chunks(list(dict.fromkeys(ids)), 50):
            data = self._get("videos", part="snippet,statistics,contentDetails", id=",".join(chunk))
            out += data.get("items", [])
        return out

    def channels(self, ids: Iterable[str]) -> list[dict]:
        out = []
        for chunk in _chunks(list(dict.fromkeys(ids)), 50):
            data = self._get("channels", part="snippet,statistics,contentDetails", id=",".join(chunk))
            out += data.get("items", [])
        return out

    def recent_uploads(self, uploads_playlist: str, limit: int = 30) -> list[str]:
        data = self._get("playlistItems", part="contentDetails", playlistId=uploads_playlist,
                         maxResults=min(limit, 50))
        return [it["contentDetails"]["videoId"] for it in data.get("items", [])]


def _chunks(seq: list, size: int) -> Iterator[list]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]
