"""Resultados de los vídeos propios: vistas/hora por vídeo y por formato.

    python -m ytauto.stats   -> imprime informe y lo guarda en reports/own_YYYY-MM-DD.md
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

from .cli import load_env
from .publish import API, _h
from .scoring import hours_since

UPLOADS = Path("data/uploads.json")
HISTORY = Path("data/own_stats.jsonl")


def fetch() -> list[dict]:
    uploads = json.loads(UPLOADS.read_text()) if UPLOADS.exists() else {}
    ids = {(v["id"] if isinstance(v, dict) else v): script for script, v in uploads.items()}
    rows = []
    for i in range(0, len(ids), 50):
        chunk = list(ids)[i:i + 50]
        data = requests.get(f"{API}/videos", headers=_h(), timeout=30, params=dict(
            part="snippet,statistics,status", id=",".join(chunk))).json()
        for v in data.get("items", []):
            script = ids[v["id"]]
            spec = yaml.safe_load(Path(script).read_text(encoding="utf-8")) if Path(script).exists() else {}
            st = v.get("statistics", {})
            public = v["status"]["privacyStatus"] == "public"
            published = v["snippet"]["publishedAt"]
            views = int(st.get("viewCount", 0))
            rows.append({
                "id": v["id"], "script": script, "format": spec.get("format", "?"),
                "experiment": spec.get("experiment", "-"),
                "title": v["snippet"]["title"], "privacy": v["status"]["privacyStatus"],
                "views": views, "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "age_h": round(hours_since(published), 1),
                "vph": round(views / hours_since(published), 2) if public else 0.0,
            })
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    HISTORY.parent.mkdir(exist_ok=True)
    with HISTORY.open("a") as f:
        for r in rows:
            f.write(json.dumps({"t": now, **r}, ensure_ascii=False) + "\n")
    return rows


def report(rows: list[dict]) -> str:
    pub = [r for r in rows if r["privacy"] == "public"]
    by_fmt = defaultdict(list)
    for r in pub:
        by_fmt[r["format"]].append(r)
    out = [f"# Resultados propios {datetime.now().date()}", "",
           f"Vídeos subidos: {len(rows)} · públicos: {len(pub)} · vistas totales: {sum(r['views'] for r in rows)}", "",
           "| Formato | Vídeos | Vistas medianas | Vistas/hora medianas | Likes medios |", "|---|---|---|---|---|"]
    for fmt, rs in sorted(by_fmt.items(), key=lambda kv: -statistics.median(r["vph"] for r in kv[1])):
        out.append(f"| {fmt} | {len(rs)} | {statistics.median(r['views'] for r in rs):.0f} | "
                   f"{statistics.median(r['vph'] for r in rs):.2f} | {statistics.mean(r['likes'] for r in rs):.1f} |")
    by_exp = defaultdict(list)
    for r in pub:
        by_exp[r["experiment"]].append(r)
    if len(by_exp) > 1:
        out += ["", "| Experimento | Vídeos | Vistas/hora medianas |", "|---|---|---|"]
        for exp, rs in sorted(by_exp.items(), key=lambda kv: -statistics.median(r["vph"] for r in kv[1])):
            out.append(f"| {exp} | {len(rs)} | {statistics.median(r['vph'] for r in rs):.2f} |")
    out += ["", "| Vídeo | Formato | Estado | Vistas | Likes | Coment. | Edad (h) |", "|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: -r["views"]):
        out.append(f"| [{r['title'][:50]}](https://youtu.be/{r['id']}) | {r['format']} | {r['privacy']} | "
                   f"{r['views']} | {r['likes']} | {r['comments']} | {r['age_h']} |")
    return "\n".join(out)


if __name__ == "__main__":
    load_env()
    text = report(fetch())
    path = Path("reports") / f"own_{datetime.now().date()}.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(text)
