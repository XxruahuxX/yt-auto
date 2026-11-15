"""Generador de Shorts verticales (1080x1920) a partir de un guion YAML.

Cada escena = una tarjeta con texto + narración TTS (Piper, local). Sin material ajeno.

    python -m ytauto.shorts guiones/001.yaml salida/001.mp4
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
import tempfile
import textwrap
import wave
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SEMI = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
GREEN_D, STRIPE, LINE = (6, 46, 28), (9, 56, 34), (40, 110, 70)
YELLOW, WHITE = (255, 214, 10), (255, 255, 255)
HANDLE = "@DatoCrack"


def _voice() -> str:
    models = sorted(glob.glob(str(Path(__file__).resolve().parent.parent / "models" / "*.onnx")))
    if not models:
        raise RuntimeError("No hay voz Piper en models/. Ver README.")
    return models[0]


def tts(text: str, out: Path, length_scale: float = 0.9) -> float:
    """ElevenLabs si hay ELEVENLABS_API_KEY; si no, Piper local."""
    if os.environ.get("ELEVENLABS_API_KEY"):
        return tts_elevenlabs(text, out)
    if (MODELS / "kokoro-v1.0.onnx").exists():
        return tts_kokoro(text, out)
    return tts_piper(text, out, length_scale)


MODELS = Path(__file__).resolve().parent.parent / "models"
_kokoro = None


def tts_kokoro(text: str, out: Path) -> float:
    """Kokoro (Apache 2.0, local, uso comercial permitido). Voces: em_alex, ef_dora, em_santa."""
    global _kokoro
    import soundfile as sf
    from kokoro_onnx import Kokoro
    if _kokoro is None:
        _kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    samples, sr = _kokoro.create(text, voice=os.environ.get("KOKORO_VOICE", "em_alex"),
                                 speed=float(os.environ.get("KOKORO_SPEED", "1.1")), lang="es")
    raw = out.with_suffix(".raw.wav")
    sf.write(str(raw), samples, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,aresample=44100", str(out)],
                   check=True)
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def tts_elevenlabs(text: str, out: Path) -> float:
    voice = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        params={"output_format": "mp3_44100_128"}, timeout=120,
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
        json={"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
              "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3}})
    if not resp.ok:
        raise RuntimeError(f"ElevenLabs HTTP {resp.status_code}: {resp.text[:300]}")
    mp3 = out.with_suffix(".mp3")
    mp3.write_bytes(resp.content)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ar", "44100", str(out)],
                   check=True)
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def tts_piper(text: str, out: Path, length_scale: float = 0.9) -> float:
    raw = out.with_suffix(".raw.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", _voice(), "-f", str(raw),
                    "--length-scale", str(length_scale), "--noise-w", "0.5",
                    "--sentence-silence", "0.15"],
                   input=text.encode(), check=True, capture_output=True)
    # quita silencios largos (el modelo mete hasta 1,5 s) y acelera un poco el ritmo
    af = ("silenceremove=start_periods=1:start_threshold=-40dB:stop_periods=-1:"
          "stop_duration=0.2:stop_threshold=-40dB,atempo=1.08,aresample=44100")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", af, str(out)],
                   check=True)
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def _background() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), GREEN_D)
    d = ImageDraw.Draw(img)
    for i in range(0, 8, 2):
        d.rectangle([i * W // 8, 0, (i + 1) * W // 8, H], fill=STRIPE)
    d.ellipse([W // 2 - 300, H // 2 - 300, W // 2 + 300, H // 2 + 300], outline=LINE, width=6)
    d.line([(0, H // 2), (W, H // 2)], fill=LINE, width=6)
    return img, d


def _fit(d, text: str, max_w: int, size: int, font_path: str, max_lines: int = 6):
    """Reduce la fuente hasta que el texto quepa en max_w y max_lines."""
    while size > 40:
        font = ImageFont.truetype(font_path, size)
        avg = d.textlength("abcdefghijklmnopqrstuvwxyz", font=font) / 26
        lines = textwrap.wrap(text, width=max(8, int(max_w / avg)))
        if len(lines) <= max_lines and all(d.textlength(l, font=font) <= max_w for l in lines):
            return font, lines
        size -= 6
    return ImageFont.truetype(font_path, size), textwrap.wrap(text, 20)


def card(label: str, text: str, out: Path, highlight: str | None = None, big: str | None = None,
         progress: float = 0.0) -> None:
    img, d = _background()
    # etiqueta superior
    lf = ImageFont.truetype(BOLD, 64)
    lw = d.textlength(label, font=lf)
    d.rounded_rectangle([(W - lw) / 2 - 40, 250, (W + lw) / 2 + 40, 360], 30, fill=YELLOW)
    d.text(((W - lw) / 2, 262), label, font=lf, fill=GREEN_D)
    # número o palabra grande opcional
    y = 560
    if big:
        bf, _ = _fit(d, big, 900, 260, BOLD, 1)
        d.text(((W - d.textlength(big, font=bf)) / 2, 520), big, font=bf, fill=YELLOW)
        y = 880
    # texto principal (zona segura: evita los 250 px inferiores de la interfaz de Shorts)
    font, lines = _fit(d, text, 900, 92, BOLD)
    lh = font.size * 1.22
    if not big:
        y = (H - lh * len(lines)) / 2 - 60
    for line in lines:
        x = (W - d.textlength(line, font=font)) / 2
        if highlight and highlight.lower() in line.lower():
            i = line.lower().index(highlight.lower())
            pre, hl = line[:i], line[i:i + len(highlight)]
            d.text((x, y), pre, font=font, fill=WHITE)
            x2 = x + d.textlength(pre, font=font)
            d.text((x2, y), hl, font=font, fill=YELLOW)
            d.text((x2 + d.textlength(hl, font=font), y), line[i + len(highlight):], font=font, fill=WHITE)
        else:
            d.text((x, y), line, font=font, fill=WHITE)
        y += lh
    # barra de progreso y firma
    d.rectangle([0, 0, int(W * progress), 14], fill=YELLOW)
    hf = ImageFont.truetype(SEMI, 48)
    d.text(((W - d.textlength(HANDLE, font=hf)) / 2, H - 420), HANDLE, font=hf, fill=(170, 210, 185))
    img.save(out)


def render(script_path: str | Path, out_path: str | Path) -> float:
    spec = yaml.safe_load(Path(script_path).read_text(encoding="utf-8"))
    scenes = spec["scenes"]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        clips = []
        for i, sc in enumerate(scenes):
            png, wav, mp4 = tmp / f"{i}.png", tmp / f"{i}.wav", tmp / f"{i}.mp4"
            card(sc.get("label", spec.get("label", "¿SABÍAS QUE...?")), sc["text"], png,
                 sc.get("highlight"), sc.get("big"), (i + 1) / len(scenes))
            dur = tts(sc.get("say", sc["text"]), wav) + sc.get("pause", 0.15)
            frames = int(dur * FPS)
            # zoom lento para dar movimiento a la tarjeta
            vf = (f"scale=1188:2112,zoompan=z='min(1+0.0009*on,1.08)':d={frames}"
                  f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png),
                            "-i", str(wav), "-vf", vf, "-af", f"apad=pad_dur={sc.get('pause', 0.35)}",
                            "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(mp4)], check=True)
            clips.append(mp4)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{c}'\n" for c in clips))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                        str(lst), "-c", "copy", "-movflags", "+faststart", str(out_path)], check=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                            "csv=p=0", str(out_path)], capture_output=True, text=True, check=True)
    return float(probe.stdout.strip())


if __name__ == "__main__":
    from .cli import load_env
    load_env()
    print(f"{render(sys.argv[1], sys.argv[2]):.1f} s -> {sys.argv[2]}")
