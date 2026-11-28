"""OAuth 2.0 para el canal (cliente de escritorio, flujo manual con redirección a localhost).

Uso:
    python -m ytauto.auth url            -> imprime el enlace de autorización
    python -m ytauto.auth code "<URL>"   -> canjea el código y guarda token.json
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

import requests

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT = "http://localhost:8765/"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]
TOKEN_FILE = Path(os.environ.get("YT_TOKEN_FILE", "token.json"))


def _client() -> tuple[str, str]:
    cid, secret = os.environ.get("YT_CLIENT_ID"), os.environ.get("YT_CLIENT_SECRET")
    if not cid or not secret:
        raise RuntimeError("Faltan YT_CLIENT_ID / YT_CLIENT_SECRET en .env")
    return cid, secret


def auth_url() -> str:
    cid, _ = _client()
    q = dict(client_id=cid, redirect_uri=REDIRECT, response_type="code", scope=" ".join(SCOPES),
             access_type="offline", prompt="consent")
    return f"{AUTH_URL}?{urllib.parse.urlencode(q)}"


def exchange(redirected_url_or_code: str) -> dict:
    cid, secret = _client()
    code = redirected_url_or_code.strip()
    if code.startswith("http"):
        code = urllib.parse.parse_qs(urllib.parse.urlparse(code).query)["code"][0]
    resp = requests.post(TOKEN_URL, data=dict(code=code, client_id=cid, client_secret=secret,
                                              redirect_uri=REDIRECT, grant_type="authorization_code"),
                         timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Error al canjear el código: {resp.status_code} {resp.text[:300]}")
    tok = resp.json()
    tok["expires_at"] = time.time() + tok.get("expires_in", 3600) - 60
    TOKEN_FILE.write_text(json.dumps(tok), encoding="utf-8")
    os.chmod(TOKEN_FILE, 0o600)
    return tok


def access_token() -> str:
    tok = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    if time.time() < tok.get("expires_at", 0):
        return tok["access_token"]
    cid, secret = _client()
    resp = requests.post(TOKEN_URL, data=dict(client_id=cid, client_secret=secret,
                                              refresh_token=tok["refresh_token"],
                                              grant_type="refresh_token"), timeout=30)
    if not resp.ok:
        raise RuntimeError(f"No se pudo renovar el token: {resp.status_code} {resp.text[:300]}")
    new = resp.json()
    tok.update(access_token=new["access_token"],
               expires_at=time.time() + new.get("expires_in", 3600) - 60)
    TOKEN_FILE.write_text(json.dumps(tok), encoding="utf-8")
    return tok["access_token"]


if __name__ == "__main__":
    from .cli import load_env
    load_env()
    if sys.argv[1:2] == ["url"]:
        print(auth_url())
    elif sys.argv[1:2] == ["code"]:
        exchange(sys.argv[2])
        print(f"Token guardado en {TOKEN_FILE}")
    else:
        print(__doc__)
