<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>02 检索</title>
<style>
@font-face{font-family:"NotoSC";src:url("assets/fonts/NotoSansSC-VF.ttf") format("truetype");font-weight:100 900}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0B0B0C}
#root{position:absolute;inset:0;font-family:"NotoSC",sans-serif;color:#F2F1EE}
.kicker{position:absolute;left:96px;top:72px;font-size:24px;letter-spacing:.2em;color:#6E6E73}
.head{position:absolute;left:96px;top:112px;font-size:48px;font-weight:600;letter-spacing:-.01em}
.hint{position:absolute;right:96px;top:120px;font-size:24px;color:#6E6E73}
.wall{position:absolute;left:96px;top:230px;width:1180px;display:grid;
  grid-template-columns:repeat(3,368px);gap:24px}
.card{height:150px;padding:18px 20px;background:#111114;border:1px solid #232327;
  overflow:hidden;position:relative}
.card .t{font-size:22px;line-height:1.42;color:#8A8A8F;font-weight:400}
.card em{font-style:normal;color:#8A8A8F}
.card em.on{color:#FFFFFF;font-weight:700}
.card.dim{opacity:.18}
.card.lit{border-color:#232327}
.scan{position:absolute;top:210px;height:790px;width:3px;background:#FFFFFF;opacity:0;
  box-shadow:0 0 70px 26px rgba(255,255,255,.06)}
.panel{position:absolute;left:1330px;top:230px;width:494px}
.plabel{font-size:20px;letter-spacing:.12em;color:#6E6E73;margin-bottom:26px}
.row{position:relative;height:104px;border-bottom:1px solid #232327;display:flex;
  align-items:center;gap:14px}
.row .name{width:210px;font-size:26px;font-weight:600;white-space:nowrap;overflow:hidden}
.row .name small{display:block;font-size:16px;font-weight:400;color:#6E6E73;margin-top:2px}
.row .track{flex:1;height:12px;background:#1C1C20;position:relative}
.row .fill{position:absolute;inset:0;background:#F2F1EE;transform-origin:left center;
  transform:scaleX(0)}
.row .n{width:44px;text-align:right;font-size:30px;font-weight:600;font-variant-numeric:tabular-nums}
.caption{position:absolute;left:96px;bottom:78px;font-size:36px;color:#A8A8AD}
.caption b{color:#FFFFFF;font-weight:700}
</style>
</head>
<body>
<div id="root" data-composition-id="retrieval" data-start="0" data-duration="20" data-width="1920" data-height="1080">
  <div class="kicker" id="r-kicker">01　检索</div>
  <div class="head" id="r-head">搜到的，是一堆文字</div>
  <div class="hint" id="r-hint">__ARTICLES__ 篇文章</div>

  <div class="wall" id="r-wall">
__CARDS__
  </div>

  <div class="panel" id="r-panel">
    <div class="plabel" id="r-plabel">被提及的车型</div>
__ROWS__
  </div>

  <div class="scan" id="r-scan"></div>
  <div class="caption" id="r-caption">从文字里，先找出 <b>__NCAND__</b> 台候选</div>
</div>
<script src="assets/vendor/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });

tl.fromTo("#r-kicker", { opacity: 0 }, { opacity: 1, duration: .4 }, 0.2);
tl.fromTo("#r-head", { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: .55, ease: "power3.out" }, 0.3);

tl.fromTo("#r-wall .card",
  { opacity: 0, y: 26 },
  { opacity: 1, y: 0, duration: .5, ease: "power3.out", stagger: .07 }, 1.0);

tl.fromTo("#r-scan", { x: 0, opacity: 0 }, { opacity: 1, duration: .25, ease: "none" }, 4.2);
tl.to("#r-scan", { x: 1180, duration: 3.6, ease: "none" }, 4.2);
tl.to("#r-scan", { opacity: 0, duration: .3 }, 7.8);
tl.to("#r-wall .card.lit", { borderColor: "#FFFFFF", duration: .3, stagger: .05 }, 4.5);
tl.fromTo("#r-wall em.on",
  { color: "#8A8A8F", fontWeight: 400 },
  { color: "#FFFFFF", fontWeight: 700, duration: .3, stagger: .05, ease: "none" }, 4.5);

tl.to("#r-wall .card:not(.lit)", { opacity: .16, duration: .6, stagger: .015 }, 8.4);
tl.fromTo("#r-panel .row", { opacity: 0, x: 30 },
  { opacity: 1, x: 0, duration: .45, stagger: .12, ease: "power3.out" }, 8.6);

tl.fromTo("#r-panel .fill",
  { scaleX: 0 },
  { scaleX: 1, duration: .8, stagger: .1, ease: "power2.out" }, 10.2);

document.querySelectorAll("#r-panel .n").forEach((el, i) => {
  const target = Number(el.dataset.n);
  const o = { v: 0 };
  tl.to(o, { v: target, duration: .8, ease: "power2.out",
    onUpdate: () => { el.textContent = Math.round(o.v); } }, 10.2 + i * 0.1);
});

tl.fromTo("#r-caption", { opacity: 0, y: 14 },
  { opacity: 1, y: 0, duration: .5, ease: "power3.out" }, 16.2);

window.__timelines["retrieval"] = tl;
tl.seek(0);
</script>
</body>
</html>
