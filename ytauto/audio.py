"""Música de fondo y efectos de sonido sintetizados (originales, sin derechos de terceros)."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _env(n: int, attack: float = 0.005, decay: float = 8.0) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    return a * np.exp(-decay * t)


def whoosh(dur: float = 0.35) -> np.ndarray:
    n = int(dur * SR)
    noise = _rng.standard_normal(n)
    # barrido: de grave a agudo con forma de campana
    t = np.linspace(0, 1, n)
    shape = np.sin(np.pi * t) ** 2
    lp = np.convolve(noise, np.ones(12) / 12, mode="same")
    hp = noise - np.convolve(noise, np.ones(40) / 40, mode="same")
    return (lp * (1 - t) + hp * t) * shape * 0.35


def pop() -> np.ndarray:
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = 600 + 900 * np.exp(-30 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 30) * 0.5


def tick() -> np.ndarray:
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * t) + 0.5 * _rng.standard_normal(n)) * _env(n, 0.0005, 90) * 0.35


def ding() -> np.ndarray:
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((1318.5, 1), (1975.5, 0.5), (2637, 0.25)))
    return x * _env(n, 0.002, 4) * 0.3


def music(seconds: float, bpm: int = 104) -> np.ndarray:
    """Loop sencillo: bombo, hi-hat, bajo y arpegio en La menor."""
    n = int(seconds * SR) + SR
    out = np.zeros(n)
    beat = 60 / bpm
    kick_n = int(0.25 * SR)
    kt = np.arange(kick_n) / SR
    kick = np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-25 * kt)) / SR) * _env(kick_n, 0.001, 14)
    hat_n = int(0.04 * SR)
    hat_noise = _rng.standard_normal(hat_n)
    hat = (hat_noise - np.convolve(hat_noise, np.ones(4) / 4, mode="same")) * _env(hat_n, 0.0005, 70) * 0.25
    roots = [55.0, 43.65, 65.41, 49.0]  # A1 F1 C2 G1
    chords = [[220, 261.63, 329.63], [174.61, 220, 261.63], [261.63, 329.63, 392], [196, 246.94, 293.66]]

    def add(sig: np.ndarray, p: int) -> None:
        end = min(p + len(sig), n)
        out[p:end] += sig[: end - p]

    i, t = 0, 0.0
    while t < seconds + 1:
        bar, step = divmod(i, 8)  # corcheas
        pos = int(t * SR)
        if step in (0, 4):
            add(kick * 0.9, pos)
        add(hat * (1.0 if step % 2 else 0.6), pos)
        if step in (0, 3, 6):
            bn = int(beat * 0.9 * SR)
            bt = np.arange(bn) / SR
            add(np.tanh(2 * np.sin(2 * np.pi * roots[bar % 4] * bt)) * _env(bn, 0.005, 3) * 0.28, pos)
        nn = int(beat / 2 * 0.9 * SR)
        nt = np.arange(nn) / SR
        f = chords[bar % 4][step % 3] * (2 if step >= 4 else 1)
        add((np.sin(2 * np.pi * f * nt) + 0.3 * np.sin(4 * np.pi * f * nt)) * _env(nn, 0.003, 9) * 0.10, pos)
        i += 1
        t += beat / 2
    return out[: int(seconds * SR)]


def boom() -> np.ndarray:
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    noise = np.convolve(_rng.standard_normal(n), np.ones(60) / 60, mode="same") * 6
    sub = np.sin(2 * np.pi * (55 * np.exp(-1.5 * t) + 30) * t)
    return (noise * 0.6 + sub) * _env(n, 0.004, 2.5) * 0.7


def fall() -> np.ndarray:
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    f = 1800 * np.exp(-1.6 * t) + 200
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + 0.15 * _rng.standard_normal(n)
    return x * np.clip(t / 0.3, 0, 1) * 0.4


def hit() -> np.ndarray:
    """Golpe corto para palabras clave: bombo grave + chasquido."""
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-30 * t)) / SR) * _env(n, 0.001, 18)
    click = _rng.standard_normal(n) * _env(n, 0.0005, 120) * 0.25
    return (body * 0.55 + click) * 0.7


SFX = {"hit": hit, "whoosh": whoosh, "pop": pop, "tick": tick, "ding": ding, "boom": boom, "fall": fall}


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
        assert w.getframerate() == SR, "las voces deben ir a 44,1 kHz"
    return data


def _place(track: np.ndarray, start: float, sig: np.ndarray) -> None:
    p = int(start * SR)
    end = min(p + len(sig), len(track))
    if end > p:
        track[p:end] += sig[: end - p]


def mix(total: float, voices: list[tuple[float, np.ndarray]], sfx: list[tuple[float, str]],
        out: Path, music_gain: float = 0.15, bpm: int = 104) -> None:
    n = int(total * SR)
    voice, fx = np.zeros(n), np.zeros(n)
    for start, data in voices:
        _place(voice, start, data)
    for start, name in sfx:
        _place(fx, start, SFX[name]())
    bed = music(total, bpm=bpm)
    # ducking: baja la música mientras habla la voz
    env = np.convolve(np.abs(voice), np.ones(2205) / 2205, mode="same")
    duck = np.convolve(np.where(env > 0.01, 0.3, 1.0), np.ones(4410) / 4410, mode="same")
    fade = np.ones(n)
    k = int(0.4 * SR)
    fade[:k] = np.linspace(0, 1, k)
    fade[-k:] = np.linspace(1, 0, k)
    master = voice + fx + bed * music_gain * duck * fade
    master /= max(1.0, np.abs(master).max() / 0.95)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((master * 32767).astype(np.int16).tobytes())

