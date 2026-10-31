# 把逐句配音按字幕时间排成 110s 音轨
import json, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
VO = ROOT / "assets" / "vo"
cfg = json.loads((VO / "vo.json").read_text(encoding="utf-8"))
TOTAL = 110.0

with wave.open(str(VO / "01.wav"), "rb") as w:
    SR, CH = w.getframerate(), w.getnchannels()

out = np.zeros(int(TOTAL * SR) + SR, dtype=np.float32)
for c in cfg:
    p = VO / f"{c['i']:02d}.wav"
    if not p.exists():
        continue
    with wave.open(str(p), "rb") as w:
        assert w.getframerate() == SR, "需统一采样率"
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if CH == 2 and data.ndim == 1:
        data = data.reshape(-1, CH)[:, 0]
    start = int(c["start"] * SR)
    out[start:start + len(data)] += data

out = np.clip(out, -1, 1)
pcm = (out * 32767).astype(np.int16)
with wave.open(str(ROOT / "assets" / "vo-track.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("vo track", SR, "Hz,", round(len(out) / SR, 2), "s")
