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


def _bp(x: np.ndarray, lo: int, hi: int) -> np.ndarray:
    """Paso banda barato: resta de dos medias móviles (lo, hi en muestras)."""
    a = np.convolve(x, np.ones(lo) / lo, mode="same")
    b = np.convolve(x, np.ones(hi) / hi, mode="same")
    return a - b


def sniff() -> np.ndarray:
    """Tres olfateos cortos de perro."""
    out = np.zeros(int(0.5 * SR))
    for k in range(3):
        n = int(0.075 * SR)
        x = _bp(_rng.standard_normal(n), 3, 14) * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
        p = int((0.02 + 0.14 * k) * SR)
        out[p:p + n] += x * (0.9 - 0.15 * k)
    return out * 0.9


def bark() -> np.ndarray:
    """Ladrido corto de dibujos (dos «guau»)."""
    out = np.zeros(int(0.62 * SR))
    for k, f0 in enumerate((520, 470)):
        n = int(0.17 * SR)
        t = np.arange(n) / SR
        f = f0 * (1.15 - 0.45 * t / t[-1])
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = sum(np.sin(h * ph) / h ** 0.7 * (1.6 if 900 < h * f0 < 1700 else 1) for h in range(1, 9))
        x = np.tanh(1.8 * x) + 0.25 * _bp(_rng.standard_normal(n), 2, 8)
        envl = np.clip(t / 0.012, 0, 1) * np.exp(-9 * t)
        p = int(k * 0.24 * SR)
        out[p:p + n] += x * envl * 0.32
    return out


def paper() -> np.ndarray:
    """Papel de periódico que se arruga."""
    n = int(0.7 * SR)
    x = np.zeros(n)
    for _ in range(70):
        p = _rng.integers(0, n - 800)
        m = _rng.integers(80, 700)
        x[p:p + m] += _rng.standard_normal(m) * _env(m, 0.0005, 60) * _rng.uniform(0.2, 1)
    return (x - np.convolve(x, np.ones(6) / 6, mode="same")) * 0.35


def shutter() -> np.ndarray:
    """Flash de cámara antigua: clic + zumbido corto."""
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    click = _rng.standard_normal(n) * _env(n, 0.0003, 160) * 0.6
    whine = np.sin(2 * np.pi * (3200 + 2400 * t) * t) * np.exp(-14 * t) * 0.08
    return click + whine


def typewriter() -> np.ndarray:
    """Ráfaga de teclas de máquina de escribir."""
    out = np.zeros(int(0.9 * SR))
    for k in range(9):
        n = int(0.03 * SR)
        x = (_rng.standard_normal(n) + np.sin(2 * np.pi * 1800 * np.arange(n) / SR)) * _env(n, 0.0003, 150)
        p = int((k * 0.085 + _rng.uniform(0, 0.02)) * SR)
        out[p:p + n] += x * 0.3
    return out


def cuffs() -> np.ndarray:
    """Esposas: dos clics metálicos con resonancia."""
    out = np.zeros(int(0.5 * SR))
    for k in range(2):
        n = int(0.25 * SR)
        t = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((2900, 1), (4300, 0.6), (6100, 0.3)))
        x = x * np.exp(-30 * t) * 0.18 + _rng.standard_normal(n) * _env(n, 0.0002, 200) * 0.5
        p = int(k * 0.13 * SR)
        out[p:p + n] += x
    return out


def stinger() -> np.ndarray:
    """Golpe de orquesta grave (re menor) para giros de guion."""
    n = int(1.8 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (73.42, 146.83, 174.61, 220.0, 293.66):
        ph = 2 * np.pi * f * t
        x += sum(np.sin(h * ph) / h for h in range(1, 7)) * 0.22
    x += np.sin(2 * np.pi * 36.7 * t) * 1.2
    x = np.tanh(x * 0.9) * np.exp(-2.6 * t) * np.clip(t / 0.006, 0, 1)
    hitn = _rng.standard_normal(n) * _env(n, 0.001, 22) * 0.5
    return (x * 0.55 + hitn) * 0.75


def riser() -> np.ndarray:
    """Subida de ruido de 1,1 s que acaba en seco (antes de una revelación)."""
    n = int(1.1 * SR)
    t = np.linspace(0, 1, n)
    noise = _rng.standard_normal(n)
    hp = noise - np.convolve(noise, np.ones(30) / 30, mode="same")
    lp = np.convolve(noise, np.ones(10) / 10, mode="same")
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * t ** 2) / SR)
    return (lp * (1 - t) + hp * t + 0.25 * tone) * t ** 2.2 * 0.35


def chime() -> np.ndarray:
    """Destello dorado: arpegio de campanillas en Re mayor."""
    n = int(2.2 * SR)
    out = np.zeros(n)
    for k, f in enumerate((1174.7, 1480.0, 1760.0, 2349.3, 2960.0, 3520.0)):
        m = n - int(k * 0.07 * SR)
        t = np.arange(m) / SR
        x = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-3.2 * t)
        out[int(k * 0.07 * SR):] += x * 0.09
    return out


def thump() -> np.ndarray:
    """Latido grave (dos golpes)."""
    out = np.zeros(int(0.6 * SR))
    for k, a in ((0, 1.0), (0.22, 0.7)):
        n = int(0.2 * SR)
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * np.cumsum(40 + 50 * np.exp(-25 * t)) / SR) * _env(n, 0.002, 20)
        p = int(k * SR)
        out[p:p + n] += x * a * 0.7
    return out


def _peak(fn, level):
    def f():
        x = fn()
        return x * level / max(1e-9, np.abs(x).max())
    f.__name__ = fn.__name__
    return f


sniff, paper, shutter, typewriter = _peak(sniff, 0.45), _peak(paper, 0.35), _peak(shutter, 0.5), _peak(typewriter, 0.35)
cuffs, stinger, riser, bark = _peak(cuffs, 0.45), _peak(stinger, 0.85), _peak(riser, 0.45), _peak(bark, 0.55)

SFX = {"hit": hit, "whoosh": whoosh, "pop": pop, "tick": tick, "ding": ding, "boom": boom, "fall": fall,
       "sniff": sniff, "bark": bark, "paper": paper, "shutter": shutter, "typewriter": typewriter,
       "cuffs": cuffs, "stinger": stinger, "riser": riser, "chime": chime, "thump": thump}


# ------------------------------------------------------------------ música por tramos (cine negro)
def _pluck(f: float, dur: float, decay: float = 5.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    return x * np.clip(t / 0.006, 0, 1) * np.exp(-decay * t)


def _pad(freqs, dur: float, attack: float = 0.4) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.004):
            ph = 2 * np.pi * f * (1 + det) * t
            x += sum(np.sin(h * ph) / h ** 1.6 for h in range(1, 6))
    a = np.clip(t / attack, 0, 1) * np.clip((dur - t) / 0.25, 0, 1)
    return x * a / max(1, len(freqs))


def _vibes(f: float, dur: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 4 * f * t)
    return x * np.exp(-2.2 * t) * (0.75 + 0.25 * np.sin(2 * np.pi * 5.5 * t))


def _noir_tracks(seconds: float, bpm: int = 100) -> dict:
    """Pistas completas para cada ambiente; luego se mezclan por tramos."""
    n = int(seconds * SR) + SR
    beat = 60 / bpm
    tr = {k: np.zeros(n) for k in ("tension", "light", "dark", "reveal")}

    def add(name, sig, start):
        p = int(start * SR)
        e = min(p + len(sig), n)
        if e > p:
            tr[name][p:e] += sig[: e - p]

    # re menor: i - VI - iv - V
    roots = [73.42, 58.27, 98.0, 110.0]
    chords = [[293.66, 349.23, 440.0], [233.08, 293.66, 349.23], [196.0, 233.08, 293.66], [220.0, 277.18, 329.63]]
    walk = [[0, 7, 12, 10], [0, 4, 7, 9], [0, 3, 7, 5], [0, 4, 7, 6]]
    motif = [587.33, 698.46, 659.25, 554.37]
    i, t = 0, 0.0
    brush_n = int(0.11 * SR)
    while t < seconds + 1:
        bar, step = divmod(i, 4)
        ch = bar % 4
        add("tension", _pluck(roots[ch] * 2 ** (walk[ch][step] / 12), beat * 0.95, 4.0) * 0.5, t)
        b = _rng.standard_normal(brush_n)
        add("tension", (b - np.convolve(b, np.ones(5) / 5, mode="same")) * _env(brush_n, 0.01, 30)
            * (0.10 if step % 2 else 0.05), t + (beat * 0.66 if step % 2 else 0))
        if step == 0:
            add("tension", _pad(chords[ch], beat * 4, 0.6) * 0.22, t)
            if bar % 2 == 1:
                add("tension", _vibes(motif[ch], beat * 2) * 0.10, t + beat * 2)
        # ambiente ligero (humor): re mayor saltarín
        lr = [73.42, 110.0, 82.41, 110.0][bar % 4]
        add("light", _pluck(lr if step % 2 == 0 else lr * 2, beat * 0.4, 9) * 0.45, t)
        mel = [587.33, 739.99, 880.0, 739.99, 659.25, 880.0, 987.77, 880.0][(i * 3) % 8]
        add("light", _pluck(mel, beat * 0.3, 14) * 0.16, t + beat * 0.5)
        if step == 0:
            add("light", _pad([293.66, 369.99, 440.0], beat * 4, 0.1) * 0.08, t)
        i += 1
        t += beat
    # oscuro: zumbido grave y notas sueltas
    tt = np.arange(n) / SR
    tr["dark"] += (np.sin(2 * np.pi * 36.71 * tt) * 0.5 + np.sin(2 * np.pi * 55.0 * tt) * 0.25) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * tt))
    tr["dark"] += np.sin(2 * np.pi * 622.25 * tt) * 0.03 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * tt))
    for k in range(int(seconds / (beat * 2)) + 1):
        add("dark", _pluck([146.83, 138.59, 130.81, 123.47][k % 4], beat * 2, 1.8) * 0.35, k * beat * 2)
    return tr


def music_sections(seconds: float, sections: list[tuple[float, float, str]], bpm: int = 100) -> np.ndarray:
    """Música que cambia de ambiente por tramos: tension, light, dark, reveal, silence.

    reveal = acorde de re mayor que se abre al empezar el tramo (golpe de luz).
    """
    tr = _noir_tracks(seconds, bpm)
    n = int(seconds * SR)
    out = np.zeros(n)
    xf = int(0.08 * SR)
    for t0, t1, mood in sections:
        p0, p1 = max(0, int(t0 * SR)), min(n, int(t1 * SR))
        if p1 <= p0 or mood == "silence":
            continue
        g = np.ones(p1 - p0)
        k = min(xf, len(g) // 2)
        if k:
            g[:k] = np.linspace(0, 1, k)
            g[-k:] = np.linspace(1, 0, k)
        if mood == "reveal":
            sw = _pad([146.83, 185.0, 220.0, 293.66, 369.99, 440.0], (p1 - p0) / SR + 0.3, 0.05) * 0.55
            sw += _pad([73.42], (p1 - p0) / SR + 0.3, 0.02) * 0.5
            out[p0:p1] += sw[: p1 - p0] * g
        elif mood == "build":
            seg = tr["tension"][p0:p1] * g
            ramp = np.linspace(0.6, 1.4, p1 - p0)
            out[p0:p1] += seg * ramp
        else:
            out[p0:p1] += tr[mood][p0:p1] * g
    return out


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
        out: Path, music_gain: float = 0.15, bpm: int = 104,
        sections: list[tuple[float, float, str]] | None = None, duck_to: float = 0.3) -> None:
    n = int(total * SR)
    voice, fx = np.zeros(n), np.zeros(n)
    for start, data in voices:
        _place(voice, start, data)
    for start, name in sfx:
        _place(fx, start, SFX[name]())
    bed = music_sections(total, sections, bpm) if sections else music(total, bpm=bpm)
    # ducking: baja la música mientras habla la voz
    env = np.convolve(np.abs(voice), np.ones(2205) / 2205, mode="same")
    duck = np.convolve(np.where(env > 0.01, duck_to, 1.0), np.ones(4410) / 4410, mode="same")
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

