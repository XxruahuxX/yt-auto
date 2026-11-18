"""Worker de Chatterbox (MIT) que se ejecuta en su propio venv.

Lee por stdin líneas JSON {"text": ..., "out": ...}, escribe el wav y responde "ok <segundos>".
Voz elegida por el usuario el 18-nov: la voz por defecto de Chatterbox Multilingual en español.
"""
import json
import sys

import torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
print("ready", flush=True)
for line in sys.stdin:
    job = json.loads(line)
    w = m.generate(job["text"], language_id="es")
    torchaudio.save(job["out"], w, m.sr)
    print(f"ok {w.shape[-1] / m.sr:.2f}", flush=True)
