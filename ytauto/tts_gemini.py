"""Narración con Gemini TTS (mismo motor de voz que Google Flow/Veo), plan gratuito.

El plan gratis da pocas peticiones al día (~10), así que se pide TODO el guion en una sola
llamada y luego se corta por escenas buscando los silencios entre párrafos.

Variables de entorno:
    GEMINI_API_KEY      clave de Google AI Studio (obligatoria)
    GEMINI_TTS_MODEL    modelo (por defecto gemini-2.5-flash-preview-tts)
    GEMINI_VOICE        voz precargada (por defecto Puck)
    GEMINI_STYLE        instrucción de estilo (si no, la del guion o STYLE por defecto)
"""
from __future__ import annotations

import base64
import os
import subprocess
import wave
from pathlib import Path

import numpy as np
import requests

SR_IN = 24000  # Gemini devuelve PCM 16 bits, mono, 24 kHz
STYLE = ("Lee este guion como un narrador de vídeos cortos de humor y fútbol en YouTube, "
         "con acento de España (castellano peninsular). Tono cercano y con chispa, ritmo ágil "
         "pero claro, remarcando los momentos graciosos y bajando la voz en el suspense. "
         "Haz una pausa breve entre cada párrafo.")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _request(text: str, style: str, voice: str) -> np.ndarray:
    model = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    body = {
        "contents": [{"parts": [{"text": f"{style}\n\n{text}"}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    r = requests.post(URL.format(model=model), json=body, timeout=300,
                      headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    if not r.ok:
        raise RuntimeError(f"Gemini TTS HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    return np.frombuffer(base64.b64decode(data), dtype=np.int16).astype(np.float32) / 32768


def _silences(x: np.ndarray, min_len: float = 0.18, thr_db: float = -38) -> list[tuple[int, int]]:
    """Tramos de silencio (inicio, fin) en muestras."""
    hop = int(0.01 * SR_IN)
    frames = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    quiet = db < db.max() + thr_db
    out, start = [], None
    for i, q in enumerate(np.append(quiet, False)):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * 0.01 >= min_len:
                out.append((start * hop, i * hop))
            start = None
    return out


def split(x: np.ndarray, texts: list[str]) -> list[np.ndarray]:
    """Corta el audio en len(texts) trozos: elige, para cada frontera, el silencio más largo
    cerca de donde debería caer según la longitud del texto."""
    n = len(texts)
    if n == 1:
        return [x]
    sil = [s for s in _silences(x) if s[0] > 0 and s[1] < len(x)]
    weights = np.cumsum([len(t) for t in texts])[:-1] / sum(len(t) for t in texts)
    cuts, used = [], set()
    for w in weights:
        target = w * len(x)
        best, score = None, None
        for k, (a, b) in enumerate(sil):
            if k in used or (cuts and a <= cuts[-1]):
                continue
            mid = (a + b) / 2
            # penaliza la distancia al objetivo y premia los silencios largos (pausa de párrafo)
            s = abs(mid - target) / len(x) - 0.5 * (b - a) / SR_IN / 10
            if score is None or s < score:
                best, score = k, s
        if best is None:
            raise RuntimeError("No encuentro pausas para separar las escenas")
        used.add(best)
        cuts.append(int(sum(sil[best]) / 2))
    bounds = [0, *cuts, len(x)]
    return [x[bounds[i]:bounds[i + 1]] for i in range(n)]


def _save(x: np.ndarray, out: Path) -> float:
    raw = out.with_suffix(".raw.wav")
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR_IN)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    # recorta silencios al principio y al final, iguala volumen y pasa a 44,1 kHz
    af = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=80,"
          "aresample=44100")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", af, str(out)],
                   check=True)
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def tts_batch(texts: list[str], outs: list[Path], style: str | None = None,
              voice: str | None = None) -> list[float]:
    """Una sola petición para todo el guion; escribe un wav por escena y devuelve duraciones."""
    style = os.environ.get("GEMINI_STYLE") or style or STYLE
    voice = voice or os.environ.get("GEMINI_VOICE", "Puck")
    x = _request("\n\n".join(t.strip() for t in texts), style, voice)
    return [_save(part, out) for part, out in zip(split(x, texts), outs)]
