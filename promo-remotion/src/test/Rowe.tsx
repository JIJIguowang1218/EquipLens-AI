import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate, Easing} from 'remotion';
import {Fonts} from '../common/lib';

// ---- monochrome palette ----
const BG = '#0B0B0C';
const INK = '#F2F1EE';
const GREY = '#6E6E73';
const LINE = '#26262A';
const DIM = '#3A3A3E';
const FONT = `'Noto Sans SC', 'Microsoft YaHei', sans-serif`;

const TITLES = [
  '陕汽德龙6x6 沙漠越野车 2026 新款报价',
  '陕汽重卡 德龙X3000 375马力 6X6 沙漠越野底盘',
  '沙漠牵引车交付阿联酋 法士特变速箱成亮点',
  '二手德龙自卸车 后八轮工程车 车况好',
  '穿越沙漠的卡车 智能分身实时回复',
  '豪沃 6×4 自卸车 工程车 现车销售',
  '东风天锦 沙漠工况 改装牵引车',
  '矿山 6X6 越野载货 底盘 参数表',
  '一汽解放 JH6 牵引车 前脸实拍',
];

const CAND = [
  {name: '德龙 6X6', n: 7},
  {name: '德龙', n: 5},
  {name: '豪沃 4', n: 3},
  {name: '天锦', n: 3},
  {name: '德龙 X3000', n: 3},
  {name: 'JH6', n: 2},
];

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
const ease = (f: number, a: number, b: number, easeFn = Easing.out(Easing.cubic)) =>
  easeFn(clamp01((f - a) / (b - a)));

// reticle: four L corners
const Corner: React.FC<{x: number; y: number; rot: number; p: number; size?: number}> = ({x, y, rot, p, size = 46}) => (
  <div style={{position: 'absolute', left: x, top: y, width: size, height: size, transform: `rotate(${rot}deg) scale(${0.94 + 0.06 * p})`, opacity: p,
    borderLeft: '2px solid #FFFFFF', borderTop: '2px solid #FFFFFF'}} />
);

export const TestRowe: React.FC = () => {
  const f = useCurrentFrame();

  // beat 1: count 0 -> 19
  const count = Math.round(interpolate(f, [8, 46], [0, 19], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const bigIn = ease(f, 4, 26);
  const bigOut = ease(f, 86, 104);

  // beat 2: wall pan
  const pan = interpolate(f, [96, 260], [0, -520], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});

  // beat 3: reticle lock at f 150..186
  const lock = ease(f, 150, 170);
  const lockFlash = f >= 170 && f < 178 ? 0.55 - (f - 170) * 0.06 : 0;

  // beat 4: rows
  const rowsIn = (i: number) => ease(f, 196 + i * 6, 220 + i * 6);

  // beat 5: final line
  const lineW = ease(f, 268, 292);

  return (
    <AbsoluteFill style={{backgroundColor: BG, fontFamily: FONT, color: INK}}>
      <Fonts />
      {/* grid */}
      <div style={{position: 'absolute', inset: 0, opacity: 0.35,
        backgroundImage: `linear-gradient(${LINE} 1px, transparent 1px), linear-gradient(90deg, ${LINE} 1px, transparent 1px)`,
        backgroundSize: '80px 80px'}} />

      {/* beat 1: big number */}
      <div style={{position: 'absolute', left: 96, top: 150, opacity: bigIn * (1 - bigOut)}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 18}}>
          <span style={{fontSize: 230, fontWeight: 900, lineHeight: 0.9, letterSpacing: -6}}>{count}</span>
          <span style={{fontSize: 40, color: GREY, fontWeight: 500}}>篇文章</span>
        </div>
        <div style={{marginTop: 18, fontSize: 30, color: GREY, opacity: ease(f, 30, 50)}}>
          为了一个类目，先读完这些
        </div>
      </div>

      {/* beat 2: title wall, scrolling */}
      <div style={{position: 'absolute', left: 0, right: 0, top: 120, bottom: 0, overflow: 'hidden',
        opacity: ease(f, 90, 112)}}>
        <div style={{position: 'absolute', left: 96, top: pan, width: 1180,
          display: 'grid', gridTemplateColumns: 'repeat(2, 570px)', gap: 22}}>
          {TITLES.map((t, i) => (
            <div key={i} style={{height: 110, border: `1px solid ${LINE}`, padding: '16px 20px',
              fontSize: 24, lineHeight: 1.4, color: i === 1 ? INK : '#8A8A8F'}}>
              {t}
            </div>
          ))}
        </div>
      </div>

      {/* reticle on the second card */}
      <div style={{position: 'absolute', left: 96 + 592, top: 120 + 110 + 22 + 0, width: 570, height: 110,
        opacity: ease(f, 148, 160)}}>
        <div style={{position: 'absolute', inset: 0, background: `rgba(255,255,255,${lockFlash})`}} />
      </div>

      {/* beat 3+4: extraction rows */}
      <div style={{position: 'absolute', right: 96, top: 200, width: 460}}>
        <div style={{fontSize: 22, letterSpacing: 6, color: GREY, marginBottom: 22, opacity: ease(f, 190, 210)}}>
          被提及的车型
        </div>
        {CAND.map((c, i) => (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 14, height: 62, borderBottom: `1px solid ${LINE}`,
            opacity: rowsIn(i), transform: `translateX(${(1 - rowsIn(i)) * 26}px)`}}>
            <div style={{width: 190, fontSize: 26, fontWeight: 600}}>{c.name}</div>
            <div style={{flex: 1, height: 2, background: LINE, position: 'relative'}}>
              <div style={{position: 'absolute', inset: 0, width: `${(c.n / 7) * 100}%`, background: INK}} />
            </div>
            <div style={{width: 34, textAlign: 'right', fontSize: 26, fontVariantNumeric: 'tabular-nums'}}>{c.n}</div>
          </div>
        ))}
      </div>

      {/* beat 5: conclusion line */}
      <div style={{position: 'absolute', left: 96, bottom: 110}}>
        <div style={{height: 2, width: 900 * lineW, background: INK, marginBottom: 22}} />
        <div style={{fontSize: 40, fontWeight: 700, opacity: ease(f, 280, 300)}}>
          19 篇文字 → <span style={{color: '#FFFFFF'}}>6 台候选</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
