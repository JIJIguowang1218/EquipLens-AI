# 按新分镜重排配音与字幕（解说词不变）
import json, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
VO = ROOT / "assets" / "vo"
cfg = {c["i"]: c for c in json.loads((VO / "vo.json").read_text(encoding="utf-8"))}
TEXT = {c["i"]: c["text"] for c in cfg.values()}

# 段落 → 行号
SECTIONS = [(6, 16, [1, 2]), (16, 28, [3, 4]), (28, 36, [5]), (36, 50, [6, 7, 8, 9]),
            (50, 60, [10, 11, 12]), (60, 73, [13, 14, 15]), (81, 95, [16, 17, 18]),
            (101, 110, [19])]

def dur(i):
    with wave.open(str(VO / f"{i:02d}.wav"), "rb") as w:
        return w.getnframes() / w.getframerate()

plan = []
for a, b, ids in SECTIONS:
    total = b - a
    speech = [dur(i) for i in ids]
    gap = max(0.25, (total - sum(speech)) / max(1, len(ids)))
    t = a
    for i, d in zip(ids, speech):
        plan.append({"i": i, "start": round(t, 2), "end": round(t + d, 2), "text": TEXT[i]})
        t += d + gap

# SRT
def ts(x):
    h = int(x // 3600); m = int((x % 3600) // 60); s = x % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
srt = []
for n, c in enumerate(plan, 1):
    srt.append(f"{n}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n")
(ROOT / "assets" / "subs.srt").write_text("\n".join(srt), encoding="utf-8")

# 音轨
with wave.open(str(VO / "01.wav"), "rb") as w:
    SR = w.getframerate()
out = np.zeros(int(110 * SR), dtype=np.float32)
for c in plan:
    with wave.open(str(VO / f"{c['i']:02d}.wav"), "rb") as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    s = int(c["start"] * SR)
    out[s:s + len(d)] += d[: len(out) - s]
with wave.open(str(ROOT / "assets" / "vo-track.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
print("retimed", len(plan), "lines")
