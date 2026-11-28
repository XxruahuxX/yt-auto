"""Datos del panel del canal: estadísticas, retención, costes y estado de cada vídeo.

    python -m ytauto.panel            -> escribe reports/panel/*.json

Fuentes:
- YouTube Data API (vistas, likes, estado, duración) y YouTube Analytics API
  (retención, % medio visto, suscriptores, fuentes de tráfico, países). Usa token.json
  con el scope yt-analytics.readonly.
- TikTok (opcional): vistas por vídeo de la cuenta, emparejadas por título.
- Registro local: data/uploads.json, data/tiktok_uploads.json, guiones/*.yaml, vídeos y
  fotogramas 3D en la carpeta del proyecto, caché de voz Gemini.

Los costes son estimaciones: tokens de voz por caracteres y segundos de audio, cuota de
YouTube por llamada. Los precios están en PRICES y se cambian aquí.
"""
from __future__ import annotations

import json
import os
import re
import wave
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

from .cli import load_env
from .publish import API, _h

ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
PROJECT = Path(os.environ.get("YT_PROJECT_DIR", "/mnt/project-files/yt-auto"))
OUT = Path("reports/panel")
START = "2026-11-01"

# Precios supuestos (USD por millón de tokens). Gemini TTS en capa gratuita cuesta 0;
# estos valores dicen cuánto costaría en la capa de pago.
PRICES = {"tts_in": 0.50, "tts_out": 10.0}
AUDIO_TOKENS_PER_S = 32          # tokens de audio por segundo (Gemini)
CHARS_PER_TOKEN = 4.0
QUOTA_UPLOAD = 1600               # videos.insert
QUOTA_THUMB = 50                  # thumbnails.set


def _yt(path: str, **params) -> dict:
    r = requests.get(f"{API}/{path}", headers=_h(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _an(**params) -> list[dict]:
    end = date.today().isoformat()
    r = requests.get(ANALYTICS, headers=_h(), timeout=60,
                     params=dict(ids="channel==MINE", startDate=START, endDate=end, **params))
    r.raise_for_status()
    d = r.json()
    cols = [c["name"] for c in d.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in d.get("rows", [])]


def _iso_dur(s: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return 0
    h, mi, se = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + se


def _spec(script: Path) -> dict:
    try:
        return yaml.safe_load(script.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _texts(spec: dict) -> list[str]:
    return [s.get("say", "") for s in spec.get("scenes", []) if isinstance(s, dict) and s.get("say")]


def _gemini_audio(texts: list[str]) -> float | None:
    """Segundos de audio Gemini en caché para estas frases (None si no se usó Gemini)."""
    try:
        from . import tts_gemini as g
    except Exception:
        return None
    total, hits = 0.0, 0
    for t in texts:
        p = g._key(t, *g._cfg(None, None))
        if p.exists():
            with wave.open(str(p)) as w:
                total += w.getnframes() / w.getframerate()
            hits += 1
    return round(total, 1) if hits else None


def _frames_3d(num: str) -> int:
    d = PROJECT / "b3d" / num
    return sum(1 for _ in d.glob("x_3d_*/f_*.png")) if d.exists() else 0


def _tiktok() -> tuple[list[dict], dict]:
    """Vídeos y cuenta de TikTok. La API no da el texto del vídeo (todos se titulan
    «#DatoCrack»), así que no se emparejan con los guiones."""
    try:
        from .tiktok import API as TT, access_token as tt_token
        h = {"Authorization": f"Bearer {tt_token()}", "Content-Type": "application/json"}
        rows, cursor = [], None
        for _ in range(10):
            body = {"max_count": 20, **({"cursor": cursor} if cursor else {})}
            v = requests.post(f"{TT}/video/list/", headers=h, timeout=30, json=body, params={
                "fields": "id,create_time,view_count,like_count,comment_count,share_count"}).json()
            data = v.get("data", {})
            for x in data.get("videos", []):
                rows.append({"id": x["id"],
                             "fecha": datetime.fromtimestamp(x["create_time"], timezone.utc).isoformat(timespec="minutes"),
                             "vistas": x.get("view_count", 0), "likes": x.get("like_count", 0),
                             "comentarios": x.get("comment_count", 0), "compartidos": x.get("share_count", 0),
                             "url": f"https://www.tiktok.com/@datocrack/video/{x['id']}"})
            if not data.get("has_more"):
                break
            cursor = data.get("cursor")
        u = requests.get(f"{TT}/user/info/", headers=h, timeout=30, params={
            "fields": "follower_count,likes_count,video_count"}).json().get("data", {}).get("user", {})
        return rows, u
    except Exception as e:  # sin token o sin red: el panel sigue sin TikTok
        print("TikTok no disponible:", e)
        return [], {}


def collect() -> dict[str, list]:
    uploads = json.loads(Path("data/uploads.json").read_text(encoding="utf-8"))
    retired = json.loads(Path("data/uploads_retirados.json").read_text(encoding="utf-8")) \
        if Path("data/uploads_retirados.json").exists() else {}
    tt_log = json.loads(Path("data/tiktok_uploads.json").read_text(encoding="utf-8")) \
        if Path("data/tiktok_uploads.json").exists() else {}
    now = datetime.now(timezone.utc)

    # --- YouTube Data API
    ids = {v["id"]: s for s, v in uploads.items()}
    yt: dict[str, dict] = {}
    for i in range(0, len(ids), 50):
        chunk = list(ids)[i:i + 50]
        for v in _yt("videos", part="snippet,statistics,status,contentDetails",
                     id=",".join(chunk)).get("items", []):
            yt[v["id"]] = v

    # --- YouTube Analytics por vídeo
    per_video = {r["video"]: r for r in _an(
        metrics="views,engagedViews,estimatedMinutesWatched,averageViewDuration,"
                "averageViewPercentage,likes,shares,subscribersGained",
        dimensions="video", sort="-views", maxResults=200)}

    tt_rows, tt_user = _tiktok()

    videos, costs, retention = [], [], []
    retired_paths = {k.split("#")[0] for k in retired}
    scripts = sorted({*uploads, *(str(p) for p in Path("guiones").glob("*.yaml"))} - (retired_paths - set(uploads)))
    for script in scripts:
        p = Path(script)
        stem, num = p.stem, p.stem.split("_")[0]
        spec = _spec(p)
        up = uploads.get(script)
        v = yt.get(up["id"]) if up else None
        an = per_video.get(up["id"], {}) if up else {}
        mp4 = (PROJECT / "shorts" / f"{stem}.mp4").exists()
        frames = _frames_3d(num)
        tt_entry = tt_log.get(stem)
        title = (v or {}).get("snippet", {}).get("title") or spec.get("title") or stem

        # Estado del pipeline
        if v:
            st = v["status"]
            pub_at = st.get("publishAt")
            if st["privacyStatus"] == "public":
                estado = "Publicado"
            elif pub_at and datetime.fromisoformat(pub_at.replace("Z", "+00:00")) > now:
                estado = "Programado"
            else:
                estado = "Privado sin programar"
        elif up:
            estado = "Subido (no encontrado)"
        elif tt_entry:
            estado = "Solo TikTok"
        elif mp4:
            estado = "Renderizado sin subir"
        elif frames:
            estado = "Renderizando 3D"
        else:
            estado = "Guion"

        tiktok = ("Borrador" if tt_entry and tt_entry.get("modo") == "borrador" else
                  ("Enviado" if tt_entry else "No subido"))

        st = (v or {}).get("statistics", {})
        dur = _iso_dur((v or {}).get("contentDetails", {}).get("duration", ""))
        published = (v or {}).get("status", {}).get("publishAt") or (v or {}).get("snippet", {}).get("publishedAt")
        if v and v["status"]["privacyStatus"] == "public":
            published = up.get("publish_at") or v["snippet"]["publishedAt"]
        age_h = (now - datetime.fromisoformat(published.replace("Z", "+00:00"))).total_seconds() / 3600 \
            if published else None
        views = int(st.get("viewCount", 0))
        public = estado == "Publicado"
        videos.append({
            "num": num, "guion": stem, "titulo": title,
            "formato": spec.get("format", "?"), "experimento": spec.get("experiment", "-"),
            "estilo": "3D" if frames or "3d" in stem else "2D",
            "estado": estado, "tiktok": tiktok,
            "id": up["id"] if up else "", "url": f"https://youtu.be/{up['id']}" if up else "",
            "publicacion": published or "",
            "edad_h": round(age_h, 1) if age_h and age_h > 0 else None,
            "duracion_s": dur or None,
            "vistas": views, "likes": int(st.get("likeCount", 0)),
            "comentarios": int(st.get("commentCount", 0)),
            "compartidos": an.get("shares"), "vistas_comprometidas": an.get("engagedViews"),
            "pct_visto": an.get("averageViewPercentage"), "segundos_vistos": an.get("averageViewDuration"),
            "minutos_vistos": an.get("estimatedMinutesWatched"), "subs": an.get("subscribersGained"),
            "vph": round(views / age_h, 1) if public and age_h and age_h > 0 else None,
            "likes_pct": round(100 * int(st.get("likeCount", 0)) / views, 2) if views else None,
        })

        # Costes estimados
        texts = _texts(spec)
        chars = sum(len(t) for t in texts)
        gem = _gemini_audio(texts)
        motor = "Gemini (Orus)" if gem else "Local (gratis)"
        audio_s = gem if gem else (dur or 0)
        tts_in = round((chars + 380) / CHARS_PER_TOKEN) if gem else 0   # 380 = instrucción de estilo
        tts_out = round(audio_s * AUDIO_TOKENS_PER_S) if gem else 0
        guion_tok = round(len(p.read_text(encoding="utf-8")) / 3.5) if p.exists() else 0
        quota = (QUOTA_UPLOAD + QUOTA_THUMB) if up else 0
        costs.append({
            "num": num, "guion": stem, "estilo": "3D" if frames or "3d" in stem else "2D",
            "tokens_guion": guion_tok, "motor_voz": motor, "caracteres_voz": chars,
            "audio_s": round(audio_s, 1), "tokens_voz_in": tts_in, "tokens_voz_out": tts_out,
            "fotogramas_3d": frames, "cuota_youtube": quota,
            "usd_voz": round(tts_in * PRICES["tts_in"] / 1e6 + tts_out * PRICES["tts_out"] / 1e6, 4),
        })

        # Retención (solo públicos con vistas)
        if public and views >= 50:
            for r in _an(metrics="audienceWatchRatio,relativeRetentionPerformance",
                         dimensions="elapsedVideoTimeRatio", filters=f"video=={up['id']}"):
                retention.append({"id": up["id"], "num": num,
                                  "t": round(r["elapsedVideoTimeRatio"], 2),
                                  "retencion": round(r["audienceWatchRatio"], 4),
                                  "relativa": round(r["relativeRetentionPerformance"], 4)})

    # Subidas retiradas (sustituidas o borradas): cuentan en la cuota gastada
    for key, val in retired.items():
        path = key.split("#")[0]
        if isinstance(val, dict):
            vid, stem = val["id"], Path(path).stem
            title = val.get("title") or _spec(Path(path)).get("title") or stem
            pub = val.get("publish_at", "")
        else:
            vid, stem, title, pub = key, f"{str(val).split()[0]}_retirado", str(val), ""
        tag = key.split("#")[1] if "#" in key else vid
        num = stem.split("_")[0]
        videos.append({"num": num, "guion": f"{stem}~{tag}", "titulo": title, "formato": "-",
                       "experimento": "-", "estilo": "-", "estado": "Retirado", "tiktok": "-",
                       "id": vid, "url": "", "publicacion": pub, "edad_h": None, "duracion_s": None,
                       "vistas": 0, "likes": 0, "comentarios": 0, "compartidos": None,
                       "vistas_comprometidas": None, "pct_visto": None, "segundos_vistos": None,
                       "minutos_vistos": None, "subs": None, "vph": None, "likes_pct": None})
        costs.append({"num": num, "guion": f"{stem}~{tag}", "estilo": "-", "tokens_guion": 0,
                      "motor_voz": "-", "caracteres_voz": 0, "audio_s": 0, "tokens_voz_in": 0,
                      "tokens_voz_out": 0, "fotogramas_3d": 0,
                      "cuota_youtube": QUOTA_UPLOAD + QUOTA_THUMB, "usd_voz": 0.0})

    daily = _an(metrics="views,engagedViews,likes,shares,subscribersGained,subscribersLost,"
                        "estimatedMinutesWatched", dimensions="day", sort="day")
    traffic = _an(metrics="views", dimensions="insightTrafficSourceType", sort="-views")
    countries = _an(metrics="views", dimensions="country", sort="-views", maxResults=12)
    ch = _yt("channels", part="statistics", mine="true")["items"][0]["statistics"]
    canal = [{"fecha": now.isoformat(timespec="minutes"),
              "suscriptores": int(ch.get("subscriberCount", 0)),
              "vistas_totales": int(ch.get("viewCount", 0)),
              "videos": int(ch.get("videoCount", 0)),
              "tiktok_seguidores": tt_user.get("follower_count"),
              "tiktok_likes": tt_user.get("likes_count"),
              "tiktok_videos": tt_user.get("video_count")}]
    return dict(videos=videos, costes=costs, retencion=retention, diario=daily,
                trafico=traffic, paises=countries, canal=canal, tiktok=tt_rows)


def main() -> None:
    load_env()
    data = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        (OUT / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        print(f"{name}: {len(rows)} filas")


if __name__ == "__main__":
    main()
