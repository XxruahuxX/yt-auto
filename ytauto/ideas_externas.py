"""Ideas de Shorts que funcionan en otros canales, adaptadas a DatoCrack con Gemini.

    python -m ytauto.ideas_externas        -> añade ideas nuevas a data/ideas_externas.json

Busca Shorts de fútbol de los últimos 7 días (YouTube Data API, unas 700 unidades de cuota),
se queda con los que más superan la media de su canal y pide a Gemini una idea adaptada
para cada uno. Las ideas se acumulan: cada búsqueda añade las nuevas arriba.
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .api import YouTubeAPI
from .scoring import parse_duration

OUT = Path("data/ideas_externas.json")
QUERIES = ["fútbol #shorts", "futbol animación shorts", "messi cristiano #shorts",
           "curiosidades fútbol shorts", "storytime fútbol", "historia fútbol shorts",
           "reto fútbol encuentra"]
MY_CHANNEL = "UCW6h72wddA8RvE3fUFFlYtw"
MAX_KEEP = 80
CADA_HORAS = 24
GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def load() -> dict:
    if OUT.exists():
        return json.loads(OUT.read_text(encoding="utf-8"))
    return {"fecha": None, "items": []}


def due(data: dict | None = None) -> bool:
    data = data or load()
    if not data.get("fecha"):
        return True
    last = datetime.fromisoformat(data["fecha"])
    return datetime.now(timezone.utc) - last > timedelta(hours=CADA_HORAS)


def candidates(api: YouTubeAPI, top: int = 10) -> list[dict]:
    now = datetime.now(timezone.utc)
    after = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids: list[str] = []
    for q in QUERIES:
        for vid in api.search_ids(q, after, region="ES", duration="short"):
            if vid not in ids:
                ids.append(vid)
    vids = api.videos(ids)
    chans = {c["id"]: c for c in api.channels({v["snippet"]["channelId"] for v in vids})}
    out = []
    for v in vids:
        sn, st = v["snippet"], v.get("statistics", {})
        if sn["channelId"] == MY_CHANNEL:
            continue
        dur = parse_duration(v.get("contentDetails", {}).get("duration", ""))
        if not dur or dur > 180:
            continue
        cs = chans.get(sn["channelId"], {}).get("statistics", {})
        views = int(st.get("viewCount", 0))
        n_vid, ch_views = int(cs.get("videoCount", 0) or 0), int(cs.get("viewCount", 0) or 0)
        avg = ch_views / n_vid if n_vid else 0
        age_h = max(1.0, (now - datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))).total_seconds() / 3600)
        outlier = views / avg if avg else None
        vph = views / age_h
        th = sn.get("thumbnails", {})
        out.append({
            "id": v["id"], "url": f"https://www.youtube.com/shorts/{v['id']}",
            "titulo": sn["title"], "canal": sn.get("channelTitle", ""),
            "suscriptores": int(cs.get("subscriberCount", 0) or 0),
            "publicado": sn["publishedAt"], "duracion_s": dur,
            "vistas": views, "likes": int(st.get("likeCount", 0)),
            "vph": round(vph, 1), "veces_media": round(outlier, 1) if outlier else None,
            "miniatura": (th.get("high") or th.get("medium") or th.get("default") or {}).get("url", ""),
            "descripcion": (sn.get("description") or "")[:300],
            "puntuacion": round(math.log10(vph + 1) * min(outlier or 1, 30), 2),
        })
    out.sort(key=lambda x: x["puntuacion"], reverse=True)
    return out[:top]


def adapt(items: list[dict]) -> list[dict]:
    """Pide a Gemini, en una sola petición, por qué funciona cada vídeo y una idea para DatoCrack."""
    if not os.environ.get("GEMINI_API_KEY"):
        from .cli import load_env
        load_env(str(Path(os.environ.get("YT_SECRETS_DIR", "secrets")) / "gemini.env"))
    key = os.environ.get("GEMINI_API_KEY")
    if not key or not items:
        return items
    model = os.environ.get("GEMINI_TEXT_MODEL", "gemini-flash-latest")
    lista = "\n".join(f"{i+1}. [{x['id']}] «{x['titulo']}» de {x['canal']} — {x['vistas']} vistas, "
                      f"{x['veces_media'] or '?'}× la media de su canal, {x['duracion_s']} s. {x['descripcion'][:150]}"
                      for i, x in enumerate(items))
    prompt = (
        "Eres guionista de DatoCrack, un canal de YouTube Shorts de fútbol en español de España: "
        "curiosidades, storytimes animados en 2D, retos «encuéntralo» y la serie 3D «La Concentración» "
        "(parodia con Messi, Cristiano y compañía en una concentración). Estos Shorts de otros canales "
        "están funcionando esta semana:\n\n" + lista + "\n\n"
        "Para cada uno, en frases cortas: por qué funciona (gancho, formato, tema) y una idea concreta "
        "para DatoCrack que copie el mecanismo, no el contenido, con un título propuesto. "
        "Responde solo JSON: una lista de objetos {\"id\", \"por_que\", \"idea\", \"titulo\", \"formato\"}, "
        "donde formato es uno de: storytime, reto, curiosidad, serie 3D, otro.")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7}}
    r = requests.post(GEMINI.format(model=model), json=body, timeout=120,
                      headers={"x-goog-api-key": key})
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    by_id = {x.get("id"): x for x in json.loads(text) if isinstance(x, dict)}
    for x in items:
        g = by_id.get(x["id"], {})
        x.update(por_que=g.get("por_que", ""), idea=g.get("idea", ""),
                 titulo_propuesto=g.get("titulo", ""), formato=g.get("formato", ""))
    return items


def run(force: bool = False) -> dict:
    data = load()
    if not force and not due(data):
        return data
    now = datetime.now(timezone.utc).isoformat(timespec="minutes")
    seen = {x["id"] for x in data["items"]}
    new = [x for x in candidates(YouTubeAPI(budget=1500)) if x["id"] not in seen]
    for x in adapt(new):
        x["encontrada"] = now
    data = {"fecha": now, "items": (new + data["items"])[:MAX_KEEP]}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


if __name__ == "__main__":
    from .cli import load_env
    load_env()
    d = run(force=True)
    for x in d["items"][:10]:
        print(f"{x['vistas']:>9} vistas  {x.get('veces_media')}×  {x['titulo'][:60]}\n   → {x.get('idea', '')[:140]}")
