# 把真人录音切句、压缩到分镜时间轴、与配乐混音
import json, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
FULL = ROOT / "assets" / "vo-human" / "full-spliced.wav"
CUT = ROOT / "assets" / "vo-human" / "cut"
CUT.mkdir(exist_ok=True)
lines = json.loads((ROOT / "assets" / "vo-human" / "lines.json").read_text())

SECTIONS = [[1, 2], [3, 4], [5], [6, 7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18], [19]]
BOUNDS = [(6, 16), (16, 28), (28, 36), (36, 50), (50, 60), (60, 73), (81, 95), (101, 110)]

def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)

def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    return float(out.stdout.strip())

# 1) 逐句裁切 + 去首尾静音（只留 0.08s）
for i, (a, b) in enumerate(lines, 1):
    raw = CUT / f"raw{i:02d}.wav"
    out = CUT / f"{i:02d}.wav"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(FULL),
         "-ac", "1", "-ar", "48000", str(raw)])
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw),
         "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,"
                "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse",
         str(out)])

# 2) 分配时间：句在段落内顺排，超出则轻度加速
placed = []
for sec, (s, e) in zip(SECTIONS, BOUNDS):
    ds = [dur(CUT / f"{i:02d}.wav") for i in sec]
    need = sum(ds) + 0.25 * (len(sec) - 1)
    avail = (e - s) - 0.3
    atempo = max(1.0, min(1.45, need / max(0.5, avail)))
    t = s
    for i, d in zip(sec, ds):
        eff = d / atempo
        placed.append({"i": i, "start": round(t, 3), "end": round(t + eff, 3), "atempo": round(atempo, 3)})
        t += eff + 0.25

# 3) 合成音轨
with wave.open(str(CUT / "01.wav"), "rb") as w:
    SR = w.getframerate()
total = 110.0
buf = np.zeros(int(total * SR), dtype=np.float32)
for p in placed:
    src = CUT / f"tmp{p['i']:02d}.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(CUT / f"{p['i']:02d}.wav"),
         "-af", f"atempo={p['atempo']}" if p["atempo"] > 1.001 else "anull", str(src)])
    with wave.open(str(src), "rb") as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    st = int(p["start"] * SR)
    buf[st:st + len(d)] += d[: max(0, len(buf) - st)]
    src.unlink(missing_ok=True)

with wave.open(str(ROOT / "assets" / "vo-human" / "track.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())

(ROOT / "assets" / "vo-human" / "placed.json").write_text(json.dumps(placed, ensure_ascii=False, indent=1))
print("placed", len(placed), "atempo range", min(p["atempo"] for p in placed), max(p["atempo"] for p in placed))
