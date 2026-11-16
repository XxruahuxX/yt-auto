"""Subida a TikTok (Content Posting API) como borrador en la bandeja del usuario.

    python -m ytauto.tiktok url                 -> enlace de autorización
    python -m ytauto.tiktok code "<URL redirigida>"  -> guarda el token
    python -m ytauto.tiktok upload videos/011.mp4 [...] -> sube a la bandeja (borrador)

Credenciales en /mnt/project-files/yt-auto/secrets/ (tiktok.env, tiktok_token.json).
"""
from __future__ import annotations

import json
import secrets as _sec
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

SECRETS = Path("/mnt/project-files/yt-auto/secrets")
ENV = SECRETS / "tiktok.env"
TOKEN = SECRETS / "tiktok_token.json"
LOG = Path("data/tiktok_uploads.json")
REDIRECT = "https://github.com/XxruahuxX/yt-auto"
SCOPES = "user.info.basic,video.upload"
API = "https://open.tiktokapis.com/v2"


def creds() -> tuple[str, str]:
    kv = dict(l.split("=", 1) for l in ENV.read_text().split() if "=" in l)
    return kv["TIKTOK_CLIENT_KEY"], kv["TIKTOK_CLIENT_SECRET"]


def auth_url() -> str:
    key, _ = creds()
    q = {"client_key": key, "scope": SCOPES, "response_type": "code",
         "redirect_uri": REDIRECT, "state": _sec.token_urlsafe(8)}
    return "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(q)


def _save(tok: dict) -> dict:
    if "access_token" not in tok:
        raise SystemExit(f"Error de TikTok: {tok}")
    tok["obtained_at"] = int(time.time())
    TOKEN.write_text(json.dumps(tok, indent=2))
    TOKEN.chmod(0o600)
    return tok


def exchange(redirected: str) -> dict:
    code = parse_qs(urlparse(redirected).query).get("code", [redirected])[0]
    key, sec = creds()
    r = requests.post(f"{API}/oauth/token/", data={
        "client_key": key, "client_secret": sec, "code": code,
        "grant_type": "authorization_code", "redirect_uri": REDIRECT}, timeout=30)
    return _save(r.json())


def access_token() -> str:
    tok = json.loads(TOKEN.read_text())
    if time.time() > tok["obtained_at"] + tok.get("expires_in", 86400) - 300:
        key, sec = creds()
        r = requests.post(f"{API}/oauth/token/", data={
            "client_key": key, "client_secret": sec,
            "grant_type": "refresh_token", "refresh_token": tok["refresh_token"]}, timeout=30)
        tok = _save(r.json())
    return tok["access_token"]


def upload_draft(path: Path) -> str:
    """Sube el vídeo a la bandeja de TikTok; el usuario lo publica desde la app."""
    size = path.stat().st_size
    chunk = size if size <= 64 * 1024 * 1024 else 10 * 1024 * 1024
    n = max(1, size // chunk)
    h = {"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json; charset=UTF-8"}
    r = requests.post(f"{API}/post/publish/inbox/video/init/", headers=h, timeout=30, json={
        "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                        "chunk_size": chunk, "total_chunk_count": n}}).json()
    if r.get("error", {}).get("code") != "ok":
        raise RuntimeError(f"init falló: {r}")
    url, pid = r["data"]["upload_url"], r["data"]["publish_id"]
    data = path.read_bytes()
    for i in range(n):
        a = i * chunk
        b = size if i == n - 1 else a + chunk
        u = requests.put(url, data=data[a:b], timeout=300, headers={
            "Content-Type": "video/mp4", "Content-Range": f"bytes {a}-{b-1}/{size}"})
        if u.status_code not in (200, 201, 206):
            raise RuntimeError(f"chunk {i} falló: {u.status_code} {u.text[:200]}")
    return pid


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else "url"
    if cmd == "url":
        print(auth_url())
    elif cmd == "code":
        tok = exchange(argv[1])
        print("Token guardado. open_id:", tok.get("open_id"))
    elif cmd == "upload":
        log = json.loads(LOG.read_text()) if LOG.exists() else {}
        for f in argv[1:]:
            p = Path(f)
            if p.stem in log:
                print(p.stem, "ya subido:", log[p.stem]); continue
            pid = upload_draft(p)
            log[p.stem] = {"publish_id": pid, "at": int(time.time())}
            LOG.parent.mkdir(exist_ok=True)
            LOG.write_text(json.dumps(log, indent=2))
            print(p.stem, "-> bandeja TikTok", pid)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
