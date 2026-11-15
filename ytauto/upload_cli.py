"""Sube Shorts renderizados (siempre en privado) usando el título/descripción del guion.

    python -m ytauto.upload_cli guiones/001.yaml videos/001.mp4 [...pares]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from .cli import load_env
from .publish import upload_video

LOG = Path("data/uploads.json")


def main(args: list[str]) -> None:
    load_env()
    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    for script, video in zip(args[::2], args[1::2]):
        if script in log:
            print(f"ya subido: {script} -> {log[script]}")
            continue
        spec = yaml.safe_load(Path(script).read_text(encoding="utf-8"))
        vid = upload_video(video, spec["title"], spec["description"], spec.get("tags", []),
                           synthetic=True)
        log[script] = vid
        LOG.parent.mkdir(exist_ok=True)
        LOG.write_text(json.dumps(log, indent=2))
        print(f"subido: {script} -> https://youtu.be/{vid}")


if __name__ == "__main__":
    main(sys.argv[1:])
