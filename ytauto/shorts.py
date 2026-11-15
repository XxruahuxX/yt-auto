"""Generador de Shorts verticales (1080x1920) a partir de un guion YAML.

Cada escena = una tarjeta con texto + narración TTS (Piper, local). Sin material ajeno.

    python -m ytauto.shorts guiones/001.yaml salida/001.mp4
"""
from __future__ import annotations

import glob
import math
import os
import re
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
HANDLE = "@DatoCrackFutboll"


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


EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]+")


def _emoji_img(emoji: str, size: int) -> Image.Image:
    """Noto Color Emoji solo se rasteriza a 109 px; se escala después."""
    font = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (int(140 * len(emoji)), 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), emoji, font=font, embedded_color=True)
    im = im.crop(im.getbbox())
    k = size / im.height
    return im.resize((max(1, int(im.width * k)), size), Image.LANCZOS)


def _ease_out_back(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


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


class Background:
    """Césped con franjas que se desplazan y círculo central que late."""

    def __init__(self):
        self.tile = Image.new("RGB", (W * 2, H), GREEN_D)
        d = ImageDraw.Draw(self.tile)
        for i in range(0, 16, 2):
            d.rectangle([i * W // 8, 0, (i + 1) * W // 8, H], fill=STRIPE)

    def frame(self, t: float) -> Image.Image:
        off = int(t * 60) % (W // 4)
        img = self.tile.crop((off, 0, off + W, H))
        d = ImageDraw.Draw(img)
        r = 300 + 12 * math.sin(t * 2 * math.pi * 104 / 60)  # late al ritmo de la música
        d.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], outline=LINE, width=6)
        d.line([(0, H // 2), (W, H // 2)], fill=LINE, width=6)
        # viñeta inferior y superior para dar profundidad
        return img


def _word_img(word: str, font, color) -> Image.Image:
    w = int(font.getlength(word)) + 20
    h = int(font.size * 1.35)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((10 + 4, 6), word, font=font, fill=(0, 0, 0, 140))  # sombra
    d.text((10, 0), word, font=font, fill=color)
    return im


class Scene:
    def __init__(self, sc: dict, default_label: str, speech: float, dur: float):
        self.sc, self.speech, self.dur = sc, speech, dur
        self.label = sc.get("label", default_label)
        probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        self.big = sc.get("big")
        found = "".join(_EMOJI_RE.findall(sc["text"])).replace("\ufe0f", "")
        text = " ".join(_EMOJI_RE.sub("", sc["text"]).split())
        emoji = sc.get("emoji") or found
        self.emoji = _emoji_img(emoji, 230 if not self.big else 150) if emoji else None
        self.font, lines = _fit(probe, text, 900, 92, BOLD)
        hl = (sc.get("highlight") or "").lower().split()
        lh = self.font.size * 1.22
        y = 880 if self.big else (H - lh * len(lines)) / 2 + (90 if self.emoji else -40)
        self.words = []  # (img, x, y)
        for line in lines:
            x = (W - probe.textlength(line, font=self.font)) / 2
            for word in line.split():
                color = YELLOW if word.lower().strip(".,¿?¡!") in hl else WHITE
                im = _word_img(word, self.font, color)
                self.words.append((im, x - 10, y))
                x += probe.textlength(word + " ", font=self.font)
            y += lh
        self.lf = ImageFont.truetype(BOLD, 64)
        if self.big:
            self.bf, _ = _fit(probe, self.big, 900, 260, BOLD, 1)
            m = re.match(r"(\d+)(.*)", self.big)
            self.count = (int(m.group(1)), m.group(2)) if m and int(m.group(1)) > 9 else None

    def draw(self, img: Image.Image, t: float) -> None:
        d = ImageDraw.Draw(img)
        # etiqueta: cae desde arriba
        k = _ease_out_back(t / 0.35)
        lw = d.textlength(self.label, font=self.lf)
        y0 = -120 + (250 + 120) * k
        d.rounded_rectangle([(W - lw) / 2 - 40, y0, (W + lw) / 2 + 40, y0 + 110], 30, fill=YELLOW)
        d.text(((W - lw) / 2, y0 + 12), self.label, font=self.lf, fill=GREEN_D)
        # número grande: cuenta hacia arriba y rebota
        if self.big:
            text = self.big
            if "countdown" in self.sc.get("sfx", []):
                text = str(max(1, 3 - int((t - 0.15) / max(self.speech / 3, 0.3))))
            elif self.count:
                p = min(t / 0.7, 1.0)
                text = f"{round(self.count[0] * (1 - (1 - p) ** 3))}{self.count[1]}"
            s = 0.3 + 0.7 * _ease_out_back(t / 0.4)
            big = _word_img(text, self.bf, YELLOW)
            bw, bh = max(1, int(big.width * s)), max(1, int(big.height * s))
            big = big.resize((bw, bh), Image.LANCZOS)
            img.paste(big, (int((W - bw) / 2), int(640 - bh / 2)), big)
        # emoji: entra con rebote y luego flota
        if self.emoji is not None:
            s = _ease_out_back((t - 0.1) / 0.35) if t > 0.1 else 0
            if s > 0.05:
                e = self.emoji
                ew, eh = max(1, int(e.width * s)), max(1, int(e.height * s))
                e = e.resize((ew, eh), Image.BILINEAR).rotate(8 * math.sin(t * 3), expand=True,
                                                               resample=Image.BICUBIC)
                float_y = 14 * math.sin(t * 4)
                if self.big:
                    cx, cy = W - 170, 520
                else:
                    first_y = self.words[0][2] if self.words else H / 2
                    cx, cy = W / 2, first_y - 170
                img.paste(e, (int(cx - e.width / 2), int(cy - e.height / 2 + float_y)), e)
        # palabras: aparecen una a una al ritmo de la voz
        n = len(self.words)
        span = max(self.speech * 0.8, 0.3)
        for i, (im, x, y) in enumerate(self.words):
            t0 = 0.15 + span * i / max(n, 1)
            if t < t0:
                continue
            s = 0.4 + 0.6 * _ease_out_back((t - t0) / 0.18)
            if s >= 0.999 and abs(s - 1) < 1e-3:
                img.paste(im, (int(x), int(y)), im)
            else:
                w2, h2 = max(1, int(im.width * s)), max(1, int(im.height * s))
                r = im.resize((w2, h2), Image.BILINEAR)
                img.paste(r, (int(x + (im.width - w2) / 2), int(y + (im.height - h2) / 2)), r)


def render(script_path: str | Path, out_path: str | Path) -> float:
    from . import audio

    spec = yaml.safe_load(Path(script_path).read_text(encoding="utf-8"))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    default_label = spec.get("label", "¿SABÍAS QUE...?")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        scenes, voices, sfx, t = [], [], [], 0.0
        for i, sc in enumerate(spec["scenes"]):
            wav = tmp / f"{i}.wav"
            speech = tts(sc.get("say", sc["text"]), wav)
            dur = speech + sc.get("pause", 0.15) + 0.15
            voices.append((t + 0.15, audio.read_wav(wav)))
            sfx.append((max(0.0, t - 0.1), "whoosh"))
            if sc.get("big"):
                sfx.append((t + 0.1, "pop"))
            for name in sc.get("sfx", []):
                if name == "countdown":
                    sfx += [(t + 0.15 + k * speech / 3, "tick") for k in range(3)]
                else:
                    sfx.append((t + 0.15, name))
            scenes.append((t, Scene(sc, default_label, speech, dur)))
            t += dur
        total = t
        mixwav = tmp / "mix.wav"
        audio.mix(total, voices, sfx, mixwav)

        bg = Background()
        hf = ImageFont.truetype(SEMI, 48)
        proc = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(mixwav),
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out_path)],
            stdin=subprocess.PIPE)
        for f in range(int(total * FPS)):
            now = f / FPS
            start, scene = next((s, sc) for s, sc in reversed(scenes) if s <= now)
            local = now - start
            img = bg.frame(now)
            scene.draw(img, local)
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, int(W * now / total), 14], fill=YELLOW)
            d.text(((W - d.textlength(HANDLE, font=hf)) / 2, H - 420), HANDLE, font=hf,
                   fill=(170, 210, 185))
            # transición: pequeño zoom de entrada en cada escena
            if local < 0.2:
                z = 1.06 - 0.06 * (local / 0.2)
                zw, zh = int(W * z), int(H * z)
                img = img.resize((zw, zh), Image.BILINEAR).crop(
                    ((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
            proc.stdin.write(img.tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg falló al codificar el vídeo")
    return total


if __name__ == "__main__":
    from .cli import load_env
    load_env()
    print(f"{render(sys.argv[1], sys.argv[2]):.1f} s -> {sys.argv[2]}")
