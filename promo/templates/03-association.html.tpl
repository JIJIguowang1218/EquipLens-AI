<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>03 关联推荐</title>
<style>
@font-face{font-family:"NotoSC";src:url("assets/fonts/NotoSansSC-VF.ttf") format("truetype");font-weight:100 900}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0B0B0C}
#root{position:absolute;inset:0;font-family:"NotoSC",sans-serif;color:#F2F1EE}
.kicker{position:absolute;left:96px;top:64px;font-size:22px;letter-spacing:.18em;color:#9A9EA4}
.head{position:absolute;left:96px;top:104px;font-size:34px;color:#A8A8AD;max-width:1400px}
.head b{color:#F2F1EE}
svg.wires{position:absolute;inset:0;width:1920px;height:1080px;pointer-events:none}
.wire{fill:none;stroke:#2E2E33;stroke-width:1.6}
.wire.hot{stroke:#FFFFFF;stroke-width:2.4}
.node{position:absolute;transform:translate(-50%,-50%)}
.q{background:#F2F1EE;color:#0B0B0C;padding:16px 26px;font-size:28px;font-weight:600;white-space:nowrap}
.art{width:360px;background:#111114;border:1px solid #232327;padding:16px 18px}
.art .t{font-size:18px;line-height:1.45;color:#4E5157;height:52px;overflow:hidden}
.art .m{font-size:14px;color:#A6A29A;margin-top:8px}
.car{background:#111114;border:1px solid #2A2A2E;padding:14px 20px;display:flex;align-items:baseline;gap:14px;min-width:360px}
.car .b{font-size:27px;font-weight:600;white-space:nowrap}
.car .b small{font-size:15px;font-weight:400;color:#6E6E73;margin-left:6px}
.car .tag{font-size:15px;color:#FFFFFF;border:1px solid #3A3A3E;padding:3px 9px;white-space:nowrap}
.car .c{font-size:14px;color:#6E6E73;margin-left:auto}
.car.big{border-color:#F2F1EE}
.concl{position:absolute;left:96px;bottom:64px;background:#111114;border:1px solid #232327;
  padding:22px 28px;display:flex;align-items:center;gap:20px}
.concl .k{font-size:14px;letter-spacing:.1em;color:#6E6E73}
.concl .v{font-size:34px;font-weight:600}
.concl .r{font-size:16px;color:#B9B9BE}
</style>
</head>
<body>
<div id="root" data-composition-id="association" data-start="0" data-duration="24" data-width="1920" data-height="1080">
  <div class="kicker" id="a-kicker">02　关联推荐</div>
  <div class="head" id="a-head">每台车要回答三个问题：<b>什么关系 · 依据在哪 · 那篇怎么说的</b></div>

  <svg class="wires" id="a-wires">
__WIRES__
  </svg>

__NODES__

  <div class="concl" id="a-concl">
    <div><div class="k">结论</div><div class="v" id="a-cv">__TOP__</div></div>
    <div class="r" id="a-cr">__REASON__</div>
  </div>
</div>
<script src="assets/vendor/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });

tl.fromTo("#a-kicker", { opacity: 0 }, { opacity: 1, duration: .4 }, 0.2);
tl.fromTo("#a-head", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: .5, ease: "power3.out" }, 0.3);

// 检索词
tl.fromTo("#n-q", { opacity: 0, scale: .9 }, { opacity: 1, scale: 1, duration: .45, ease: "back.out(1.6)" }, 1.2);
tl.fromTo("#n-q", { opacity: .85 }, { opacity: 1, duration: .3 }, 1.2);

// 文章节点
tl.fromTo(".node.art", { opacity: 0, x: -18 }, { opacity: 1, x: 0, duration: .42, stagger: .16, ease: "power3.out" }, 2.2);
tl.fromTo(".wire.art", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: .5, stagger: .16, ease: "none" }, 2.5);

// 车型节点
tl.fromTo(".node.car", { opacity: 0, x: 20 }, { opacity: 1, x: 0, duration: .42, stagger: .14, ease: "power3.out" }, 6.4);
tl.fromTo(".wire.car", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: .5, stagger: .14, ease: "none" }, 6.7);

// 关系标签
tl.fromTo(".car .tag", { opacity: 0, y: 6 }, { opacity: 1, y: 0, duration: .3, stagger: .08 }, 11.4);

// 收束：只留最强的一条链
tl.to(".node.car:not(.big)", { opacity: .18, duration: .5 }, 16.4);
tl.to(".node.art:not(.keep)", { opacity: .18, duration: .5 }, 16.4);
tl.to(".wire.car", { opacity: .18, duration: .5 }, 16.4);
tl.to(".wire.car.keep", { opacity: 1, stroke: "#FFFFFF", duration: .5 }, 16.4);
tl.to(".node.car.big", { scale: 1.04, duration: .5, ease: "power2.out" }, 16.4);

tl.fromTo("#a-concl", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .5, ease: "power3.out" }, 17.4);

window.__timelines["association"] = tl;
tl.seek(0);
</script>
</body>
</html>
