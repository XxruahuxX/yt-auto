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


def _channel_video_ids() -> list[str]:
    """Ids de todos los vídeos del canal (lista de subidas, incluye privados y programados)."""
    ch = _yt("channels", part="contentDetails", mine="true")["items"][0]
    playlist = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    out, token = [], None
    for _ in range(20):
        d = _yt("playlistItems", part="contentDetails", playlistId=playlist, maxResults=50,
                **({"pageToken": token} if token else {}))
        out += [it["contentDetails"]["videoId"] for it in d.get("items", [])]
        token = d.get("nextPageToken")
        if not token:
            break
    return out


def _thumb(v: dict | None) -> str:
    th = (v or {}).get("snippet", {}).get("thumbnails", {})
    return (th.get("high") or th.get("medium") or th.get("default") or {}).get("url", "")


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = len(xs) // 2
    return xs[k] if len(xs) % 2 else (xs[k - 1] + xs[k]) / 2


def _at(curve: dict, t: float):
    """Valor de la curva de retención en el punto más cercano a t (0-1)."""
    if not curve:
        return None
    k = min(curve, key=lambda x: abs(x - t))
    return curve[k]


def consejos(videos: list[dict], retention: list[dict]) -> None:
    """Añade a cada vídeo una lista de mejoras concretas, comparándolo con la mediana del canal."""
    curves: dict[str, dict] = {}
    for r in retention:
        curves.setdefault(r["id"], {})[r["t"]] = r["retencion"]
    pub = [v for v in videos if v["estado"] == "Publicado"]
    med = {
        "gancho": _median(_at(c, 0.1) for c in curves.values()),
        "mitad": _median(_at(c, 0.5) for c in curves.values()),
        "final": _median(_at(c, 1.0) for c in curves.values()),
        "pct": _median(v["pct_visto"] for v in pub),
        "likes": _median(v["likes_pct"] for v in pub),
        "vph": _median(v["vph"] for v in pub if v["edad_h"] and 24 <= v["edad_h"] <= 96),
        "subs": _median(v["subs"] for v in pub),
    }
    for v in videos:
        out = []
        add = lambda nivel, tema, texto: out.append({"nivel": nivel, "tema": tema, "texto": texto})
        c = curves.get(v["id"], {})
        if v["estado"] == "Programado":
            add("info", "Estado", "Programado. Las mejoras aparecerán cuando tenga datos.")
        elif v["estado"] == "Publicado":
            if v["pct_visto"] is None:
                add("info", "Datos", "YouTube Analytics aún no tiene datos de retención (tarda 2-3 días).")
            g, m, f = _at(c, 0.1), _at(c, 0.5), _at(c, 1.0)
            if g is not None and med["gancho"] and g < med["gancho"] * 0.92:
                add("alta", "Gancho", f"Al 10 % del vídeo sigue el {g*100:.0f} % del público (mediana del canal: "
                    f"{med['gancho']*100:.0f} %). Empieza por la imagen más llamativa y di el conflicto en la primera frase.")
            if m is not None and med["mitad"] and m < med["mitad"] * 0.85:
                add("media", "Ritmo", f"A mitad del vídeo queda el {m*100:.0f} % (mediana: {med['mitad']*100:.0f} %). "
                    "Recorta la parte central o mete un giro a mitad.")
            if f is not None and med["final"] and f < med["final"] * 0.85:
                add("media", "Final", f"Solo llega al final el {f*100:.0f} % (mediana: {med['final']*100:.0f} %). "
                    "Prueba un cierre en bucle que enlace con la primera frase.")
            elif f is not None and med["final"] and f > med["final"] * 1.3:
                add("bien", "Final", f"Llega al final el {f*100:.0f} %, muy por encima de la mediana. Repite este tipo de cierre.")
            if v["likes_pct"] is not None and med["likes"] and v["vistas"] >= 300 and v["likes_pct"] < med["likes"] * 0.7:
                add("media", "Likes", f"{v['likes_pct']:.1f} % de likes por vista (mediana: {med['likes']:.1f} %). "
                    "Pide una reacción concreta en el vídeo («dale like si lo sabías»).")
            if v["comentarios"] == 0 and v["vistas"] >= 500:
                add("baja", "Comentarios", "0 comentarios. Fija un comentario con una pregunta para abrir conversación.")
            if v["vph"] and med["vph"] and v["edad_h"] and 24 <= v["edad_h"] <= 96:
                if v["vph"] < med["vph"] * 0.5:
                    add("alta", "Alcance", f"{v['vph']:.0f} vistas/h, menos de la mitad de la mediana ({med['vph']:.0f}). "
                        "Prueba otro título y que la primera imagen sea distinta.")
                elif v["vph"] > med["vph"] * 1.5:
                    add("bien", "Alcance", f"{v['vph']:.0f} vistas/h, por encima de la mediana ({med['vph']:.0f}). "
                        "Haz una segunda parte o el mismo formato con otro tema.")
            if v["subs"] is not None and med["subs"] is not None and v["subs"] > max(3, med["subs"] * 2):
                add("bien", "Suscriptores", f"Ha traído {v['subs']} suscriptores (mediana: {med['subs']:.0f}). Es un formato que fideliza.")
            if v["tiktok"] == "No subido" and v["edad_h"] and v["edad_h"] <= 14 * 24:
                add("baja", "TikTok", "No está en TikTok. Súbelo: ahí cada vídeo suma 200-1.700 vistas más.")
        v["mejoras"] = out
        v["mejoras_n"] = sum(1 for x in out if x["nivel"] in ("alta", "media", "baja"))


def historial(videos: list[dict], now: datetime) -> list[dict]:
    """Guarda una foto de las vistas de cada vídeo en cada actualización y devuelve el historial."""
    path = Path("data/panel_historial.jsonl")
    snap = {"t": now.isoformat(timespec="minutes"),
            "v": {x["id"]: [x["vistas"], x["likes"]] for x in videos if x["id"] and x["estado"] == "Publicado"}}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(snap) + "\n")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[-500:]:
        try:
            s = json.loads(line)
        except ValueError:
            continue
        for vid, (views, likes) in s["v"].items():
            rows.append({"id": vid, "t": s["t"], "vistas": views, "likes": likes})
    return rows


def collect() -> dict[str, list]:
    uploads = json.loads(Path("data/uploads.json").read_text(encoding="utf-8"))
    retired = json.loads(Path("data/uploads_retirados.json").read_text(encoding="utf-8")) \
        if Path("data/uploads_retirados.json").exists() else {}
    tt_log = json.loads(Path("data/tiktok_uploads.json").read_text(encoding="utf-8")) \
        if Path("data/tiktok_uploads.json").exists() else {}
    now = datetime.now(timezone.utc)

    # --- Vídeos del canal: la lista sale de YouTube, no solo del registro local, para que
    # los vídeos subidos desde otro equipo aparezcan aunque data/uploads.json esté atrasado.
    known = {v["id"] for v in uploads.values()}
    for vid in _channel_video_ids():
        if vid not in known:
            uploads[f"canal/{vid}"] = {"id": vid}

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
        if script.startswith("canal/"):
            v0 = yt.get(uploads[script]["id"])
            st0 = (v0 or {}).get("status", {})
            # De lo que no está en el registro solo interesa lo público o programado
            if not v0 or not (st0.get("privacyStatus") == "public" or st0.get("publishAt")):
                continue
        p = Path(script)
        stem, num = p.stem, ("—" if script.startswith("canal/") else p.stem.split("_")[0])
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
            "miniatura": _thumb(v),
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

    consejos(videos, retention)
    hist = historial(videos, now)

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
                trafico=traffic, paises=countries, canal=canal, tiktok=tt_rows,
                historial=hist)


def main() -> None:
    load_env()
    data = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        (OUT / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        print(f"{name}: {len(rows)} filas")


if __name__ == "__main__":
    main()
