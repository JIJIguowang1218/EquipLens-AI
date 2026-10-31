# 生成温柔的铺底配乐（纯代码合成，无版权问题）
import wave
from pathlib import Path
import numpy as np

SR = 48000
DUR = 110.0
n = int(DUR * SR)
t = np.arange(n) / SR
rng = np.random.default_rng(7)

def note(name):
    names = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}
    p, octv = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[p] + 12 * (octv - 4) - 9) / 12)

def voice(f, dur, amp=1.0, attack=1.2, release=2.0):
    m = int(dur * SR); tt = np.arange(m) / SR
    env = np.minimum(1, tt / attack) * np.minimum(1, np.maximum(0, (dur - tt) / release))
    w = np.sin(2*np.pi*f*tt) * 0.6 + np.sin(2*np.pi*f*1.003*tt) * 0.25 + np.sin(2*np.pi*f*0.997*tt) * 0.15
    w += 0.12 * np.sin(2*np.pi*f*2*tt)  # 轻微泛音
    return (w * env * amp).astype(np.float32)

# 和弦进行：Cmaj7 - Am7 - Fmaj7 - G6（每 8 秒一个，循环）
prog = [
    ["C3","G3","E4","B4"],
    ["A2","E3","C4","G4"],
    ["F2","C3","A3","E4"],
    ["G2","D3","B3","E4"],
]
CH = 8.0
mix = np.zeros(n, dtype=np.float32)
k = 0
while k * CH < DUR:
    chord = prog[k % len(prog)]
    start = k * CH
    for j, nm in enumerate(chord):
        f = note(nm)
        amp = 0.10 if j == 0 else 0.06
        seg = voice(f, min(CH + 2.0, DUR - start), amp=amp, attack=1.6, release=2.6)
        s = int(start * SR); e = min(n, s + len(seg))
        mix[s:e] += seg[: e - s]
    k += 1

# 高音铃（每 4 秒一个，稀疏）
bells = ["E5","G5","B5","D5","C5","A4","G4","E4"]
for i in range(int(DUR // 4)):
    f = note(bells[i % len(bells)])
    dur = 3.0; m = int(dur * SR); tt = np.arange(m) / SR
    env = np.exp(-tt * 1.6) * np.minimum(1, tt / 0.02)
    b = (np.sin(2*np.pi*f*tt) * 0.8 + np.sin(2*np.pi*f*2.01*tt) * 0.2) * env * 0.035
    s = int((i * 4 + 1.2) * SR); e = min(n, s + len(b))
    mix[s:e] += b[: e - s].astype(np.float32)

# 低频铺底
root = np.sin(2*np.pi*55*t) * 0.05 + np.sin(2*np.pi*82.5*t) * 0.02
mix += root.astype(np.float32)

# 简易混响：几个衰减延迟
out = mix.copy()
for dly, g in ((0.11, 0.30), (0.19, 0.22), (0.29, 0.14), (0.41, 0.08)):
    sh = int(dly * SR)
    out[sh:] += mix[:-sh] * g

# 低频噪声底（很轻的空气感），低通
noise = rng.normal(0, 1, n).astype(np.float32)
b = np.exp(-np.arange(200) / 60.0); b /= b.sum()
noise = np.convolve(noise, b, mode="same").astype(np.float32)
out += noise * 0.008

# 整体淡入淡出 + 归一
fade = np.ones(n, dtype=np.float32)
fi = int(3 * SR); fo = int(6 * SR)
fade[:fi] = np.linspace(0, 1, fi) ** 2
fade[-fo:] = np.linspace(1, 0, fo) ** 2
out *= fade
out /= (np.abs(out).max() + 1e-9)
out *= 0.55

pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
p = Path(__file__).resolve().parent / "assets" / "bed-soft.wav"
with wave.open(str(p), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", p)
