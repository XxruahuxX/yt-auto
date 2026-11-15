"""Subida de vídeos y cambios del canal con OAuth. Todo se sube en privado."""
from __future__ import annotations

import json
from pathlib import Path

import requests

from .auth import access_token

API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"


def _h(extra: dict | None = None) -> dict:
    h = {"Authorization": f"Bearer {access_token()}"}
    h.update(extra or {})
    return h


def _check(resp: requests.Response) -> dict:
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json() if resp.content else {}


def my_channel() -> dict:
    data = _check(requests.get(f"{API}/channels", headers=_h(), timeout=30,
                               params=dict(part="snippet,brandingSettings,statistics", mine="true")))
    return data["items"][0]


def upload_video(path: str | Path, title: str, description: str, tags: list[str],
                 category_id: str = "17", synthetic: bool = False, publish_at: str | None = None) -> str:
    """Subida reanudable (1.600 unidades). Devuelve el id del vídeo. Siempre privado."""
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": synthetic}
    if publish_at:
        status["publishAt"] = publish_at
    meta = {"snippet": {"title": title[:100], "description": description[:5000], "tags": tags,
                        "categoryId": category_id, "defaultLanguage": "es",
                        "defaultAudioLanguage": "es"},
            "status": status}
    path = Path(path)
    init = requests.post(f"{UPLOAD}/videos", timeout=60,
                         params={"uploadType": "resumable", "part": "snippet,status"},
                         headers=_h({"Content-Type": "application/json; charset=UTF-8",
                                     "X-Upload-Content-Type": "video/mp4",
                                     "X-Upload-Content-Length": str(path.stat().st_size)}),
                         data=json.dumps(meta))
    _check(init)
    with path.open("rb") as f:
        resp = requests.put(init.headers["Location"], data=f, timeout=600,
                            headers=_h({"Content-Type": "video/mp4"}))
    return _check(resp)["id"]


def set_thumbnail(video_id: str, image: str | Path) -> None:
    with open(image, "rb") as f:
        _check(requests.post(f"{UPLOAD}/thumbnails/set", params={"videoId": video_id},
                             headers=_h({"Content-Type": "image/png"}), data=f, timeout=120))


def update_channel(description: str | None = None, keywords: str | None = None,
                   banner: str | Path | None = None) -> None:
    """Descripción, palabras clave y banner. Nombre, @ y foto no se pueden cambiar por API."""
    ch = my_channel()
    branding = ch["brandingSettings"]
    if description is not None:
        branding.setdefault("channel", {})["description"] = description
    if keywords is not None:
        branding.setdefault("channel", {})["keywords"] = keywords
    if banner:
        with open(banner, "rb") as f:
            url = _check(requests.post(f"{UPLOAD}/channelBanners/insert", data=f, timeout=120,
                                       headers=_h({"Content-Type": "image/png"})))["url"]
        branding.setdefault("image", {})["bannerExternalUrl"] = url
    body = {"id": ch["id"], "brandingSettings": {"channel": branding.get("channel", {}),
                                                 "image": branding.get("image", {})}}
    if not body["brandingSettings"]["image"]:
        del body["brandingSettings"]["image"]
    _check(requests.put(f"{API}/channels", params={"part": "brandingSettings"}, headers=_h(
        {"Content-Type": "application/json"}), data=json.dumps(body), timeout=30))
