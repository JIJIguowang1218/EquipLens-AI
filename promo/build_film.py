# 逐段渲染 → 变速 → 拼接 → 合成配音字幕
import json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "tmp" / "parts"
OUT.mkdir(parents=True, exist_ok=True)

SEGS = [
    ("01-open", 13.0, 10.0),
    ("02-retrieval", 20.0, 12.0),
    ("03-evidence", 8.0, 8.0),
    ("03-association", 24.0, 14.0),
    ("04-gate", 17.0, 10.0),
    ("05-structure", 13.0, 13.0),
    ("07-orchestration", 8.0, 8.0),
    ("06-ui", 17.0, 14.0),
    ("09-pipeline", 6.0, 6.0),
    ("07-end", 5.0, 9.0),
]

for name, natural, target in SEGS:
    src = OUT / f"{name}-raw.mp4"
    dst = OUT / f"{name}.mp4"
    subprocess.run(["npx.cmd", "hyperframes", "render", "promo", "--composition",
                    f"compositions/{name}.html", "-o", str(src), "-f", "30", "-q", "looks"],
                   check=True, capture_output=True)
    speed = natural / target
    if speed > 1.001:
        vf = f"setpts=PTS/{speed:.4f},fps=30"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf,
                        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)], check=True)
    elif speed < 0.999:
        hold = target - natural
        vf = f"tpad=stop_mode=clone:stop_duration={hold:.2f},fps=30"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf,
                        "-t", f"{target:.2f}", "-c:v", "libx264", "-crf", "20",
                        "-pix_fmt", "yuv420p", str(dst)], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
                        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)], check=True)
    print(name, natural, "->", target, flush=True)

lst = OUT / "list.txt"
lst.write_text("".join(f"file '{OUT / (n + '.mp4')}'\n" for n, _, _ in SEGS), encoding="utf-8")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                str(ROOT.parent / "tmp" / "film-v5.mp4")], check=True)
print("concatenated", flush=True)
