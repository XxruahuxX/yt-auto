import numpy as np

from ytauto import tts_gemini as g


def _burst(sec):
    t = np.arange(int(sec * g.SR_IN)) / g.SR_IN
    # habla simulada: tono con pausas cortas entre "palabras" (0,08 s)
    x = 0.3 * np.sin(2 * np.pi * 180 * t)
    x[(t % 0.5) > 0.42] = 0
    return x


def test_split_por_pausas_de_parrafo():
    gap = np.zeros(int(0.45 * g.SR_IN))
    durs = [2.0, 3.0, 1.5]
    x = np.concatenate([_burst(durs[0]), gap, _burst(durs[1]), gap, _burst(durs[2])])
    texts = ["a" * 40, "b" * 60, "c" * 30]
    parts = g.split(x, texts)
    got = [len(p) / g.SR_IN for p in parts]
    for d, e in zip(got, [2.2, 3.45, 1.7]):
        assert abs(d - e) < 0.3, got
