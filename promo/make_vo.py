# 生成旁白：读 SRT → piper 合成 → 按字幕时间轴排布 → 110s 音轨
import json, re, subprocess, wave
from pathlib import Path
from piper import PiperVoice, SynthesisConfig
from piper import SynthesisConfig

ROOT = Path(__file__).resolve().parent
SRT = ROOT.parent / "assets" / "subtitles" / "equiplens.srt"
MODEL = ROOT.parent / "tmp" / "piper" / "zh_CN-huayan-medium.onnx"
OUT = ROOT / "assets" / "vo"
OUT.mkdir(parents=True, exist_ok=True)


def parse_srt(p: Path):
    txt = p.read_text(encoding="utf-8").strip()
    cues = []
    for block in re.split(r"\n\s*\n", txt):
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        g = list(map(int, m.groups()))
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append({"start": a, "end": b, "text": "".join(lines[2:])})
    return cues


def dur_of(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


cues = parse_srt(SRT)
voice = PiperVoice.load(str(MODEL))
cfgs = []
for i, c in enumerate(cues, 1):
    wav = OUT / f"{i:02d}.wav"
    if not wav.exists():
        with wave.open(str(wav), "wb") as w:
            voice.synthesize_wav(c["text"].replace(chr(10), "，"), w, syn_config=SynthesisConfig(length_scale=1.12))
    d = dur_of(wav)
    slot = c["end"] - c["start"]
    atempo = max(1.0, min(1.35, d / max(0.2, slot)))
    cfgs.append({"i": i, "start": c["start"], "slot": round(slot, 2),
                 "dur": round(d, 2), "atempo": round(atempo, 3), "text": c["text"]})
(OUT / "vo.json").write_text(json.dumps(cfgs, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(cfgs[:4], ensure_ascii=False))
print("total cues", len(cfgs), "speech", round(sum(x["dur"] for x in cfgs), 1), "s")
