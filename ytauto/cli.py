"""CLI: python -m ytauto {collect,top,niches}."""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import yaml

from . import db
from .api import QuotaExceeded, YouTubeAPI
from .detect import collect, refresh_channels, score
from .niches import rank_niches


def load_env(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v
                        for k, v in r.items()})


def main(argv=None) -> None:
    load_env()
    ap = argparse.ArgumentParser(prog="ytauto")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", default="data/ytauto.db")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("collect", help="Descarga tendencias y búsquedas por nicho")
    sub.add_parser("channels", help="Solo actualiza suscriptores y mediana de los canales")
    top = sub.add_parser("top", help="Muestra los vídeos con más puntuación")
    top.add_argument("-n", type=int, default=25)
    top.add_argument("--shorts", action="store_true", help="Solo Shorts")
    top.add_argument("--niche")
    sub.add_parser("niches", help="Ranking de nichos por oportunidad")
    args = ap.parse_args(argv)

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    conn = db.connect(args.db)
    out_dir = Path("reports")

    if args.cmd == "collect":
        api = YouTubeAPI(budget=config.get("quota_budget", 9000))
        stats = collect(api, conn, config)
        print(json.dumps(stats, indent=2))
    elif args.cmd == "channels":
        api = YouTubeAPI(budget=config.get("quota_budget", 9000))
        try:
            n = refresh_channels(api, conn, config.get("max_channels_per_run", 150))
        except QuotaExceeded as exc:
            n = "parcial"
            print(f"Cuota agotada: {exc}")
        print(f"Canales actualizados: {n}. Cuota usada: {api.used}")
    elif args.cmd == "top":
        rows = score(conn, config.get("max_age_days", 7))
        if args.shorts:
            rows = [r for r in rows if r["is_short"]]
        if args.niche:
            rows = [r for r in rows if r["niche"] == args.niche]
        write_csv(rows, out_dir / "top.csv")
        for r in rows[: args.n]:
            kind = "S" if r["is_short"] else "L"
            print(f"{r['score']:>7} {kind} {r['vph']:>9}/h x{r['outlier'] or '-':<6} {r['title'][:70]}  {r['url']}")
        print(f"\n{len(rows)} vídeos. CSV completo en {out_dir / 'top.csv'}")
    elif args.cmd == "niches":
        ranking = rank_niches(score(conn, config.get("max_age_days", 7)),
                              config.get("min_videos_per_niche", 20))
        write_csv(ranking, out_dir / "niches.csv")
        for r in ranking:
            print(f"{r['opportunity']:>6}  {r['niche']:<24} outliers {r['outlier_rate']:.0%}  "
                  f"pequeños {r['small_channel_outlier_rate']:.0%}  VPH mediana {r['median_vph']}  "
                  f"Shorts {r['shorts_share']:.0%}")
        print(f"\nCSV en {out_dir / 'niches.csv'}")


if __name__ == "__main__":
    main()
