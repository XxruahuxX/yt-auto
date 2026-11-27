"""Narración con Gemini TTS (mismo motor de voz que Google Flow/Veo), plan gratuito.

El plan gratis da pocas peticiones al día (~10), así que se pide TODO el guion en una sola
llamada y luego se corta por escenas buscando los silencios entre párrafos.

Variables de entorno:
    GEMINI_API_KEY      clave de Google AI Studio (obligatoria)
    GEMINI_TTS_MODEL    modelo (por defecto gemini-3.8-flash-tts)
    GEMINI_VOICE        voz precargada (por defecto Orus, elegida por el usuario el 27-nov)
    GEMINI_TEMPO        acelera el audio final (por defecto 1.0)
    GEMINI_STYLE        instrucción de estilo (si no, la del guion o STYLE por defecto)
"""
from __future__ import annotations

import base64
import difflib
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import requests

SR_IN = 24000  # Gemini devuelve PCM 16 bits, mono, 24 kHz
STYLE = ("Lee este guion como un narrador de Shorts de humor y fútbol en YouTube, con acento "
         "de España (castellano peninsular). Ritmo RÁPIDO, como en TikTok, sin pausas dentro de "
         "las frases. Tono cercano y con chispa, remarcando lo gracioso y bajando la voz en el "
         "suspense. Deja una pausa corta solo entre párrafos.")
# Formato de la guía de prompts de Gemini TTS: notas de dirección + transcripción.
# Solo se lee en voz alta lo que va bajo TRANSCRIPT.
PROMPT = """# AUDIO PROFILE: Narrador de Shorts de fútbol y humor
## DIRECTOR'S NOTES
{style}
## TRANSCRIPT
{text}"""
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _request(text: str, style: str, voice: str) -> np.ndarray:
    model = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(style=style, text=text)}]}],
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


def _norm(w: str) -> str:
    return re.sub(r"[^\wáéíóúüñ]", "", w.lower())


def _word_cuts(x: np.ndarray, texts: list[str]) -> list[int]:
    """Fronteras exactas con Whisper: transcribe con marcas de tiempo por palabra (usando el
    propio guion como pista), alinea las palabras con el guion y corta en el hueco entre la
    última palabra de una escena y la primera de la siguiente."""
    from faster_whisper import WhisperModel  # noqa: PLC0415

    global _whisper
    if _whisper is None:
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
        _whisper = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu",
                                compute_type="int8")
    y = np.interp(np.arange(0, len(x), SR_IN / 16000), np.arange(len(x)), x).astype(np.float32)
    segs, _ = _whisper.transcribe(y, language="es", word_timestamps=True,
                                  initial_prompt=" ".join(texts))
    heard = [w for sg in segs for w in sg.words]
    script = [_norm(w) for t in texts for w in t.split()]
    starts = np.cumsum([len(t.split()) for t in texts])[:-1]  # índice de la 1.ª palabra de cada escena
    m = difflib.SequenceMatcher(a=script, b=[_norm(w.word) for w in heard], autojunk=False)
    a2b = {}
    for blk in m.get_matching_blocks():
        for k in range(blk.size):
            a2b[blk.a + k] = blk.b + k
    cuts = []
    for k in starts:
        nxt = next((a2b[j] for j in range(k, len(script)) if j in a2b), None)
        if nxt is None or nxt == 0:
            raise RuntimeError("No pude alinear la voz con el guion")
        a, b = heard[nxt - 1].end, heard[nxt].start
        lo, hi = int(a * SR_IN), max(int(b * SR_IN), int(a * SR_IN) + 1)
        # dentro del hueco, el punto más silencioso (ventanas de 10 ms)
        win = int(0.01 * SR_IN)
        seg = x[lo:hi]
        if len(seg) > win:
            e = np.convolve(seg ** 2, np.ones(win), mode="valid")
            cuts.append(lo + int(e.argmin()) + win // 2)
        else:
            cuts.append((lo + hi) // 2)
    if any(b <= a for a, b in zip(cuts, cuts[1:])):
        raise RuntimeError("Cortes desordenados")
    return cuts


_whisper = None


def split(x: np.ndarray, texts: list[str]) -> list[np.ndarray]:
    """Corta el audio en len(texts) trozos. Con faster-whisper instalado usa las palabras
    (exacto); si no, el método de abajo por silencios."""
    if len(texts) > 1:
        try:
            cuts = _word_cuts(x, texts)
            bounds = [0, *cuts, len(x)]
            return [x[bounds[i]:bounds[i + 1]] for i in range(len(texts))]
        except Exception as e:  # noqa: BLE001
            print(f"Alineado por palabras falló ({e}); corto por silencios", file=sys.stderr)
    return split_silences(x, texts)


def split_silences(x: np.ndarray, texts: list[str]) -> list[np.ndarray]:
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
          "silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-40dB,"
          f"atempo={os.environ.get('GEMINI_TEMPO', '1.0')},highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=80,"
          "aresample=44100")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", af, str(out)],
                   check=True)
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def tts_batch(texts: list[str], outs: list[Path], style: str | None = None,
              voice: str | None = None) -> list[float]:
    """Una sola petición para todo el guion; escribe un wav por escena y devuelve duraciones."""
    style = os.environ.get("GEMINI_STYLE") or style or STYLE
    voice = voice or os.environ.get("GEMINI_VOICE", "Orus")
    x = _request("\n\n".join(t.strip() for t in texts), style, voice)
    return [_save(part, out) for part, out in zip(split(x, texts), outs)]
