"""EquipLens 命令行入口。所有子命令均支持 --data-dir（默认 ./data）。

常用流程（在仓库根目录, 需 PYTHONPATH=src）:
  python -m equiplens ingest <图片文件夹> --platform 甲方邮件 --license client_provided
  python -m equiplens vehicle-add 品牌 型号 && vehicle-list
  python -m equiplens plan --type full --vehicles ... --out plan.json
  python -m equiplens retrieve plan.json --channel-root <夹具渠道目录>
  python -m equiplens review-pack <批次号> --out review.html
  python -m equiplens apply-review decisions.json
  python -m equiplens doctor
"""

import argparse
import json
import sys
from pathlib import Path

from . import channels, db, doctor, ingest, query, retrieval, review, reviewserver, webchannel, workflow


def main(argv=None):
    parser = argparse.ArgumentParser(prog="equiplens", description="EquipLens-AI 数据工具")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-dir", default="data", help="数据目录（默认 ./data）")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", parents=[common], help="批量导入图片并判重（M1）")
    p.add_argument("folder")
    p.add_argument("--platform", default="本地导入")
    p.add_argument("--license", default="web_third_party",
                   choices=["client_provided", "self_captured", "web_official", "web_third_party"])
    p.add_argument("--report", default=None)

    p = sub.add_parser("vehicle-add", parents=[common], help="新建车型")
    p.add_argument("brand"); p.add_argument("model")
    p.add_argument("--category", default=None); p.add_argument("--generation", default=None)
    sub.add_parser("vehicle-list", parents=[common], help="车型列表")
    sub.add_parser("pool", parents=[common], help="待归号池")

    p = sub.add_parser("bind", parents=[common], help="素材对号到车型")
    p.add_argument("asset_id"); p.add_argument("vehicle_id")
    p = sub.add_parser("unbind", parents=[common], help="退回待归号池"); p.add_argument("asset_id")
    p = sub.add_parser("tag", parents=[common], help="视角打标"); p.add_argument("asset_id"); p.add_argument("view")
    p = sub.add_parser("crop", parents=[common], help="从原图裁部件特写")
    p.add_argument("asset_id"); p.add_argument("x", type=int); p.add_argument("y", type=int)
    p.add_argument("w", type=int); p.add_argument("h", type=int); p.add_argument("part_id")
    p = sub.add_parser("hero", parents=[common], help="设主图"); p.add_argument("vehicle_id"); p.add_argument("asset_id")
    p = sub.add_parser("reject", parents=[common], help="拒绝素材"); p.add_argument("asset_id")
    p = sub.add_parser("summary", parents=[common], help="车型摘要"); p.add_argument("vehicle_id")
    p = sub.add_parser("undo", parents=[common], help="按日志ID/操作号撤销")
    p.add_argument("ref"); p.add_argument("--force", action="store_true")

    sub.add_parser("doctor", parents=[common], help="数据完整性巡检")

    p = sub.add_parser("plan", parents=[common], help="生成检索计划（D12 输入四要素→任务树）")
    p.add_argument("--type", dest="ptype", required=True,
                   choices=["full", "gap_fill", "part_focus"])
    p.add_argument("--vehicles", nargs="+", required=True, help="名录（测试期人工给定，R2 起联网生成）")
    p.add_argument("--parts", nargs="*", default=[])
    p.add_argument("--page-type", default="vehicle_page")
    p.add_argument("--pages", type=int, default=1)
    p.add_argument("--category", default=None)
    p.add_argument("--out", required=True, help="计划 JSON 输出路径")

    p = sub.add_parser("review-pack", parents=[common], help="按批次生成审核包 HTML")
    p.add_argument("batch_id"); p.add_argument("--out", required=True)

    p = sub.add_parser("apply-review", parents=[common], help="回读审核决策落账")
    p.add_argument("decisions")

    p = sub.add_parser("review-serve", parents=[common], help="实时审核服务(localhost, 每点即存)")
    p.add_argument("batch_id"); p.add_argument("--port", type=int, default=8765)

    p = sub.add_parser("crawl-web", parents=[common], help="B 案真实抓取: 厂商官网 → 候选")
    p.add_argument("--roots", nargs="+", required=True, help="厂商官网根 URL")
    p.add_argument("--keywords", nargs="*", default=None, help="产品页筛选关键词")
    p.add_argument("--max-pages", type=int, default=10)
    p.add_argument("--max-total", type=int, default=40)
    p.add_argument("--license", default="web_third_party")

    p = sub.add_parser("retrieve", parents=[common], help="执行检索计划（R1: images 任务, 夹具渠道）")
    p.add_argument("plan_json")
    p.add_argument("--channel-root", required=True, help="夹具渠道根目录（含 pages/ 与图片）")
    p.add_argument("--license", default="web_third_party")

    p = sub.add_parser("find", parents=[common], help="组合过滤检索")
    p.add_argument("--vehicle", default=None); p.add_argument("--view", default=None)
    p.add_argument("--kind", default=None); p.add_argument("--part", default=None)
    p.add_argument("--license", default=None); p.add_argument("--flag", default=None)
    p.add_argument("--status", default=None); p.add_argument("--binding", default=None)
    p.add_argument("--all-rejected", action="store_true")
    p = sub.add_parser("search", parents=[common], help="全局文字搜索"); p.add_argument("text")
    p = sub.add_parser("clusters", parents=[common], help="同尺寸疑似变体聚类"); p.add_argument("--min", type=int, default=2)
    p = sub.add_parser("similar", parents=[common], help="感知哈希相似检索"); p.add_argument("asset_id")
    p.add_argument("--max-dist", type=int, default=8)
    p = sub.add_parser("group-variant", parents=[common], help="人工确认后建立变体分组")
    p.add_argument("assets", nargs="+")
    p = sub.add_parser("ungroup", parents=[common], help="移出变体分组"); p.add_argument("asset_id")
    sub.add_parser("vocab-list", parents=[common], help="词表(默认仅正式项)")
    p = sub.add_parser("vocab-add", parents=[common], help="新增自由标签(进提名池)"); p.add_argument("term")
    p = sub.add_parser("vocab-promote", parents=[common], help="提名转正"); p.add_argument("term_id")
    p = sub.add_parser("vocab-retire", parents=[common], help="退役词表项"); p.add_argument("term_id")

    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir)
    if args.command != "ingest":
        data_dir.mkdir(parents=True, exist_ok=True)
        conn = db.connect(data_dir / "equiplens.db")
        db.init_db(conn)  # 幂等建库 + 旧库无损迁移
    else:
        conn = None

    if args.command == "ingest":
        report = ingest.ingest_directory(data_dir, Path(args.folder),
                                         platform=args.platform, license=args.license)
        print(ingest.summarize(report))
        for item in report["skipped"]:
            print(f"  跳过: {item['file']} — {item['reason']}")
        for item in report["near_duplicate"]:
            print(f"  疑似重复: {item['file']} (asset {item['asset_id']})")
        if args.report:
            Path(args.report).write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"报告已写入 {args.report}")
        return 0

    if args.command == "vehicle-add":
        vid = workflow.create_vehicle(conn, args.brand, args.model,
                                      args.category, args.generation)
        print(f"车型已创建: {vid}")
    elif args.command == "vehicle-list":
        for r in conn.execute("SELECT id, brand, model_name, generation, list_status FROM vehicles ORDER BY created_at"):
            print(f"  {r['id']}  {r['brand']}/{r['model_name']} {r['generation'] or ''} [{r['list_status']}]")
    elif args.command == "pool":
        rows = db.unbound_pool(conn)
        print(f"待归号池 {len(rows)} 个:")
        for r in rows:
            print(f"  {r['id']}  {r['width']}x{r['height']} {r['file_path']}")
    elif args.command == "bind":
        workflow.bind_asset(conn, args.asset_id, args.vehicle_id)
        print(f"已对号: {args.asset_id} → {args.vehicle_id}")
    elif args.command == "unbind":
        workflow.unbind_asset(conn, args.asset_id)
        print(f"已退回待归号池: {args.asset_id}")
    elif args.command == "tag":
        workflow.set_view(conn, args.asset_id, args.view)
        print(f"已打标: {args.asset_id} view={args.view}")
    elif args.command == "crop":
        aid = workflow.crop_asset(conn, data_dir, args.asset_id,
                                  {"x": args.x, "y": args.y, "w": args.w, "h": args.h},
                                  args.part_id)
        print(f"裁图已生成: {aid}")
    elif args.command == "hero":
        db.set_hero(conn, args.vehicle_id, args.asset_id)
        print(f"主图已设定: {args.vehicle_id} → {args.asset_id}")
    elif args.command == "reject":
        workflow.reject_asset(conn, args.asset_id)
        print(f"已拒绝: {args.asset_id}")
    elif args.command == "summary":
        s = workflow.vehicle_summary(conn, args.vehicle_id)
        print(json.dumps(s, ensure_ascii=False, indent=2))
    elif args.command == "undo":
        op = db.undo(conn, args.ref, force=args.force)
        print(f"已整体撤销操作: {op}")
    elif args.command == "doctor":
        report = doctor.doctor(conn, data_dir)
        if report["ok"]:
            print("巡检通过: 无问题")
        else:
            print(f"巡检发现 {report['total_issues']} 项问题:")
            labels = {"missing_files": "缺失文件", "orphan_files": "孤儿文件",
                      "dangling_hero": "悬空主图", "dangling_parent": "悬空父图",
                      "dangling_vehicle": "悬空车型", "stale_variant_groups": "残留变体组"}
            for key, items in report["issues"].items():
                for it in items:
                    print(f"  [{labels[key]}] {it}")
        conn.close()
        return 0 if report["ok"] else 1
    elif args.command == "find":
        rows = query.query_assets(conn, vehicle_id=args.vehicle, view=args.view,
                                  kind=args.kind, part_id=args.part, license=args.license,
                                  quality_flag=args.flag, confirm_status=args.status,
                                  binding_status=args.binding, include_rejected=args.all_rejected)
        print(f"命中 {len(rows)} 个素材:")
        for r in rows:
            print(f"  {r['id']}  {r['view_angle']:>10} {r['width'] or '?'}x{r['height'] or '?'}"
                  f" [{r['confirm_status']}] {r['file_path']}")
    elif args.command == "search":
        rows = query.text_search(conn, args.text)
        print(f"命中 {len(rows)} 个素材:")
        for r in rows:
            print(f"  {r['id']}  {r['file_path']}")
    elif args.command == "clusters":
        groups = query.same_dimension_clusters(conn, min_group=args.min)
        print(f"同尺寸聚类 {len(groups)} 组:")
        for g in groups:
            print(f"  {g[0]['width']}x{g[0]['height']} ×{len(g)}:")
            for r in g:
                vg = f" 组:{r['variant_group'][:8]}" if r["variant_group"] else ""
                print(f"    {r['id']}  {r['file_path']}{vg}")
    elif args.command == "similar":
        hits = query.find_similar(conn, args.asset_id, max_dist=args.max_dist)
        print(f"与 {args.asset_id} 相似(距离≤{args.max_dist}) {len(hits)} 个:")
        for r, d in hits:
            print(f"  距离={d:<3} {r['id']}  {r['file_path']}")
    elif args.command == "group-variant":
        op = workflow.link_variants(conn, args.assets)
        print(f"已建立变体分组: {op}")
    elif args.command == "ungroup":
        workflow.unlink_variant(conn, args.asset_id)
        print(f"已移出变体分组: {args.asset_id}")
    elif args.command == "vocab-list":
        for r in query.vocab_list(conn, include_pending=True, include_retired=True):
            print(f"  [{r['status']:>8}] {r['id']}  {r['term']}")
    elif args.command == "vocab-add":
        tid = query.vocab_add(conn, args.term)
        print(f"已进提名池: {tid} (pending)")
    elif args.command == "vocab-promote":
        query.vocab_promote(conn, args.term_id)
        print(f"已转正: {args.term_id}")
    elif args.command == "vocab-retire":
        query.vocab_retire(conn, args.term_id)
        print(f"已退役: {args.term_id}")
    elif args.command == "plan":
        plan = retrieval.build_plan(
            {"type": args.ptype, "vehicles": args.vehicles, "parts": args.parts,
             "page_types": [{"type": args.page_type, "pages": args.pages}],
             "category": args.category}, conn=conn)
        Path(args.out).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"检索计划已生成: {plan['plan_id']}（任务 {len(plan['tasks'])} 条, 每车配额 {plan['quota_per_vehicle']}）→ {args.out}")
    elif args.command == "review-pack":
        info = review.build_review_pack(conn, data_dir, args.batch_id, Path(args.out))
        print(f"审核包已生成: {info['assets']} 个素材 / {info['groups']} 组 → {info['out']}")
    elif args.command == "apply-review":
        summary = review.apply_review(conn, args.decisions, data_dir)
        print(f"审核落账完成: {summary}")
    elif args.command == "review-serve":
        reviewserver.serve(conn, data_dir, args.batch_id, port=args.port)
        return 0
    elif args.command == "crawl-web":
        result = webchannel.crawl_vendor_sites(
            conn, data_dir, args.roots, keywords=args.keywords,
            max_pages=args.max_pages, max_total=args.max_total, license=args.license)
        # 完整报告落盘(data/*.json 已放行), 控制台只打摘要——避免管道截断丢统计
        (data_dir / f"{result['batch_id']}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"完整报告: {data_dir / (result['batch_id'] + '.json')}")
        print(f"来源页 {result['pages_crawled']} | 新候选 {result['candidates']} | "
              f"跳过 {result['skipped']} | 门卫拦截 {len(result['gate_blocked'])} | "
              f"门卫耗时 {result['gate_ms']:.0f}ms")
        print(f"下一步: python -m equiplens review-pack {result['batch_id']} --out review.html --data-dir {data_dir}")
    elif args.command == "retrieve":
        plan = json.loads(Path(args.plan_json).read_text(encoding="utf-8"))
        channel = channels.FixtureChannel(Path(args.channel_root))
        result = retrieval.execute_plan(conn, data_dir, plan, channel, license=args.license)
        print(f"批次 {result['batch_id']}（计划 {result['plan_id']}）:")
        for r in result["reports"]:
            line = f"  {r['vehicle']}: 新候选 {r['candidates']}, 已在库 {r.get('existing', 0)}, 跳过 {r['skipped']}"
            if r.get("status"):
                line += f" — {r['status']}"
            print(line)
            for s in r.get("statuses", []):
                print(f"    {s['status']:>14}  {s['src']}")
        print(f"下一步: python -m equiplens review-pack {result['batch_id']} --out review.html --data-dir {data_dir}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
