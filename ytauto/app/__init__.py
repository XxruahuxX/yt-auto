"""Aplicación de escritorio del panel del canal.

    pip install pywebview
    python -m ytauto.app        (o DatoCrackPanel.exe dentro de la carpeta del repo)

Abre una ventana con el panel. Al arrancar muestra los últimos datos guardados en
reports/panel/; el botón «Actualizar» los vuelve a pedir a YouTube y TikTok (unos 40 s).

Rutas de tu PC, en .env (opcionales):
    YT_PROJECT_DIR   carpeta con shorts/, b3d/ y voces/cache (fotogramas 3D y voz Gemini)
    YT_SECRETS_DIR   carpeta con tiktok.env y tiktok_token.json
    YT_TOKEN_FILE    token.json de YouTube (por defecto, el de la raíz del repo)
"""
from __future__ import annotations

import json
import os
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path

import sys

if getattr(sys, "frozen", False):  # .exe de PyInstaller: el repo es la carpeta del .exe
    ROOT = Path(os.environ.get("YT_REPO_DIR") or Path(sys.executable).parent)
    WEB = Path(sys._MEIPASS) / "ytauto" / "app" / "web"
else:
    ROOT = Path(os.environ.get("YT_REPO_DIR") or Path(__file__).resolve().parents[2])
    WEB = Path(__file__).resolve().parent / "web"
NAMES = ["videos", "retencion", "costes", "diario", "trafico", "paises", "canal", "tiktok", "ideas"]


class Api:
    """Funciones que la ventana llama desde JavaScript (window.pywebview.api)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def datos(self) -> dict:
        out = ROOT / "reports" / "panel"
        data: dict = {}
        for n in NAMES:
            p = ROOT / "data" / "ideas.json" if n == "ideas" else out / f"{n}.json"
            data[n] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        if data["canal"] is None:
            return {"error": "Aún no hay datos guardados. Pulsa «Actualizar»."}
        return data

    def actualizar(self) -> dict:
        if not self._lock.acquire(blocking=False):
            return {"error": "Ya se está actualizando."}
        try:
            if not (ROOT / "data" / "uploads.json").exists():
                return {"error": f"No encuentro data/uploads.json en {ROOT}. "
                                 "Pon el .exe en la carpeta del repo yt-auto."}
            _collect()
            return self.datos()
        except Exception as e:
            traceback.print_exc()
            return {"error": f"No se pudo actualizar: {e}"}
        finally:
            self._lock.release()


def _collect() -> None:
    from .. import panel
    panel.main()


def main() -> None:
    os.chdir(ROOT)
    from ..cli import load_env
    load_env()
    try:
        import webview
    except ImportError:
        raise SystemExit("Falta pywebview. Instálalo con: pip install pywebview")
    webview.create_window("DatoCrack · Panel", str(WEB / "index.html"), js_api=Api(),
                          width=1280, height=860, min_size=(420, 600))
    webview.start(http_server=True)
