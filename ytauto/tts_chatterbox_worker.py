"""Worker de Chatterbox (MIT) que se ejecuta en su propio venv.

Lee por stdin líneas JSON {"text": ..., "out": ...}, escribe el wav y responde "ok <segundos>".
Voz elegida por el usuario el 18-nov: Chatterbox con referencia assets/voz_ref_davefx.wav
(voz Piper es_ES davefx, dataset CC0), exaggeration 0.7, cfg_weight 0.3.
"""
import json
import os
import sys

import torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
print("ready", flush=True)
for line in sys.stdin:
    job = json.loads(line)
    ref = os.environ.get("CB_REF")
    kw = dict(audio_prompt_path=ref, exaggeration=float(os.environ.get("CB_EXAG", "0.7")),
              cfg_weight=float(os.environ.get("CB_CFG", "0.3"))) if ref and os.path.exists(ref) else {}
    w = m.generate(job["text"], language_id="es", **kw)
    torchaudio.save(job["out"], w, m.sr)
    print(f"ok {w.shape[-1] / m.sr:.2f}", flush=True)
