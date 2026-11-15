"""Sube Shorts (en privado) y los programa en la siguiente franja libre.

Franjas diarias (hora de Madrid): 14:00, 18:00 y 21:00.

    python -m ytauto.upload_cli guiones/011.yaml videos/011.mp4 [...pares]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from .cli import load_env
from .publish import upload_video

LOG = Path("data/uploads.json")
TZ = ZoneInfo("Europe/Madrid")
SLOTS = [time(14), time(18), time(21)]


def load_log() -> dict:
    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    return {k: (v if isinstance(v, dict) else {"id": v, "publish_at": None}) for k, v in log.items()}


def save_log(log: dict) -> None:
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text(json.dumps(log, indent=2))


def next_slot(taken: set[str], now: datetime | None = None) -> str:
    """Primera franja libre al menos 1 h en el futuro, en UTC RFC 3339."""
    now = (now or datetime.now(timezone.utc)).astimezone(TZ)
    day = now.date()
    while True:
        for slot in SLOTS:
            dt = datetime.combine(day, slot, TZ)
            iso = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if dt > now + timedelta(hours=1) and iso not in taken:
                return iso
        day += timedelta(days=1)


def main(args: list[str]) -> None:
    load_env()
    log = load_log()
    for script, video in zip(args[::2], args[1::2]):
        if script in log:
            print(f"ya subido: {script} -> {log[script]['id']}")
            continue
        spec = yaml.safe_load(Path(script).read_text(encoding="utf-8"))
        taken = {v["publish_at"] for v in log.values() if v.get("publish_at")}
        at = next_slot(taken)
        vid = upload_video(video, spec["title"], spec["description"], spec.get("tags", []),
                           synthetic=True, publish_at=at)
        log[script] = {"id": vid, "publish_at": at}
        save_log(log)
        local = datetime.fromisoformat(at.replace("Z", "+00:00")).astimezone(TZ)
        print(f"subido: {script} -> https://youtu.be/{vid} · se publica {local:%a %d %H:%M}")


if __name__ == "__main__":
    main(sys.argv[1:])
