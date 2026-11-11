# -*- coding: utf-8 -*-
"""360 主体 + Baidu 定向补位（实验，不写回 state）。

只对 primary/preferred 未占槽的 target 查 Baidu；若 accepted，提议替换最低优先级 accepted backup/pool。
"""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
from equiplens import imagesearch  # noqa
from equiplens.retrieval_engine.contracts import Asset, PartRequirement  # noqa
from equiplens.retrieval_engine.web import RuleVerifier  # noqa

def main():
    run=ROOT/'data-test/runs/loop-platform-360-20261112'
    brief=json.loads((ROOT/'data-test/evals/task-briefs-20261109/brief-m1-desert.json').read_text(encoding='utf-8'))
    st=json.loads((run/'state.json').read_text(encoding='utf-8'))
    reqs={p['part']:PartRequirement(part=p['part'],label=p.get('label',''),views=tuple(p.get('views') or [])) for p in brief['part_requirements']}
    part=next(iter(reqs)); ver=RuleVerifier(reqs,min_width=1200)
    accepted={t for u in st['units'].values() for t in u.get('accepted_targets',[])}
    missing=[(t,x) for t,x in st['targets'].items() if t not in accepted and x.get('role') in ('primary','backup')]
    missing.sort(key=lambda kv:int(kv[1].get('intent_rank') or 999))
    proposals=[]
    for tid,t in missing:
        q=t.get('query') or tid
        # 定向补位允许一次类目+品牌词的 fallback；不做车型专用规则
        import re as _re
        cls=((brief.get('request') or {}).get('class') or '')
        term=next((v for k,v in (('搅拌','搅拌车'),('自卸','矿用自卸车'),('高空作业','高空作业车'),('牵引','牵引车')) if k in cls), cls[:8])
        cn=[x for x in _re.findall(r'[一-鿿]{2,4}',tid) if x not in ('油田','专用','全驱','牵引','沙漠','运输','重型','驾驶室','康明斯','艾里逊','底盘')]
        fallback=(term+' '+' '.join(cn[:2])).strip()
        hits,diag=imagesearch.search_platforms(q,limit=8,model=tid,platforms=('baidu',))
        if not hits and fallback and fallback!=q:
            q=fallback
            hits,diag=imagesearch.search_platforms(q,limit=8,model=tid,platforms=('baidu',))
        accepted_assets=[]
        for h in hits:
            res=imagesearch._download_and_gate(h)
            if not res.get('data') or not (res.get('gate') or {}).get('pass'): continue
            w=(res.get('prefilter') or {}).get('width',0); hh=(res.get('prefilter') or {}).get('height',0)
            a=Asset(asset_id='x',target_id=tid,part=part,width=w,height=hh,url=h.get('url',''),title=h.get('title',''),model=tid)
            v=ver.verify(a,part)
            if v.accepted: accepted_assets.append({'url':h.get('url',''),'title':h.get('title',''),'identity':v.identity})
        proposals.append({'target':tid,'intent_rank':t.get('intent_rank'),'role':t.get('role'),
                          'query':q,'hits':len(hits),'accepted':accepted_assets,
                          'diag':diag})
        print(tid[:40],'hits',len(hits),'accepted',len(accepted_assets),flush=True)
    out=ROOT/'data-test/runs/loop-platform-360-20261112/BACKFILL-PROPOSAL.json'
    out.write_text(json.dumps(proposals,ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps({'missing':len(missing),'with_evidence':sum(1 for p in proposals if p['accepted'])},ensure_ascii=False))
if __name__=='__main__': raise SystemExit(main())
