"""EquipLens 命令行入口。

用法（在仓库根目录, 需 PYTHONPATH=src）:
  python -m equiplens ingest <图片文件夹> [--data-dir data] [--platform 名称] [--license 档位]
  python -m equiplens vehicle-add <品牌> <型号> [--category 类别] [--generation 年款]
  python -m equiplens vehicle-list
  python -m equiplens pool                          # 待归号池
  python -m equiplens bind <素材ID> <车型ID>         # 对号
  python -m equiplens unbind <素材ID>
  python -m equiplens tag <素材ID> <视角>            # 视角打标(hero_lf/front/...)
  python -m equiplens crop <源素材ID> <x> <y> <w> <h> <部位ID>
  python -m equiplens hero <车型ID> <素材ID>
  python -m equiplens reject <素材ID>
  python -m equiplens summary <车型ID>
  python -m equiplens undo <日志ID或操作号>
"""

import argparse
import json
import sys
from pathlib import Path

from . import db, ingest, query, workflow


def main(argv=None):
    parser = argparse.ArgumentParser(prog="equiplens", description="EquipLens-AI 数据工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="批量导入图片并判重（M1）")
    p.add_argument("folder")
    p.add_argument("--data-dir", default="data")
    p.add_argument("--platform", default="本地导入")
    p.add_argument("--license", default="web_third_party",
                   choices=["client_provided", "self_captured", "web_official", "web_third_party"])
    p.add_argument("--report", default=None)

    p = sub.add_parser("vehicle-add", help="新建车型")
    p.add_argument("brand"); p.add_argument("model")
    p.add_argument("--category", default=None); p.add_argument("--generation", default=None)

    sub.add_parser("vehicle-list", help="车型列表")
    sub.add_parser("pool", help="待归号池")

    p = sub.add_parser("bind", help="素材对号到车型")
    p.add_argument("asset_id"); p.add_argument("vehicle_id")
    p = sub.add_parser("unbind", help="退回待归号池"); p.add_argument("asset_id")
    p = sub.add_parser("tag", help="视角打标"); p.add_argument("asset_id"); p.add_argument("view")
    p = sub.add_parser("crop", help="从原图裁部件特写")
    p.add_argument("asset_id"); p.add_argument("x", type=int); p.add_argument("y", type=int)
    p.add_argument("w", type=int); p.add_argument("h", type=int); p.add_argument("part_id")
    p = sub.add_parser("hero", help="设主图"); p.add_argument("vehicle_id"); p.add_argument("asset_id")
    p = sub.add_parser("reject", help="拒绝素材"); p.add_argument("asset_id")
    p = sub.add_parser("summary", help="车型摘要"); p.add_argument("vehicle_id")
    p = sub.add_parser("undo", help="按日志ID/操作号撤销"); p.add_argument("ref")

    p = sub.add_parser("find", help="组合过滤检索")
    p.add_argument("--vehicle", default=None); p.add_argument("--view", default=None)
    p.add_argument("--kind", default=None); p.add_argument("--part", default=None)
    p.add_argument("--license", default=None); p.add_argument("--flag", default=None)
    p.add_argument("--status", default=None); p.add_argument("--binding", default=None)
    p.add_argument("--all-rejected", action="store_true")
    p = sub.add_parser("search", help="全局文字搜索"); p.add_argument("text")
    p = sub.add_parser("clusters", help="同尺寸疑似变体聚类"); p.add_argument("--min", type=int, default=2)
    p = sub.add_parser("similar", help="感知哈希相似检索"); p.add_argument("asset_id")
    p.add_argument("--max-dist", type=int, default=8)
    p = sub.add_parser("group-variant", help="人工确认后建立变体分组")
    p.add_argument("assets", nargs="+")
    p = sub.add_parser("ungroup", help="移出变体分组"); p.add_argument("asset_id")
    sub.add_parser("vocab-list", help="词表(默认仅正式项)")
    p = sub.add_parser("vocab-add", help="新增自由标签(进提名池)"); p.add_argument("term")
    p = sub.add_parser("vocab-promote", help="提名转正"); p.add_argument("term_id")
    p = sub.add_parser("vocab-retire", help="退役词表项"); p.add_argument("term_id")

    args = parser.parse_args(argv)
    conn = db.connect(Path(args.data_dir if hasattr(args, "data_dir") else "data") / "equiplens.db") \
        if args.command != "ingest" else None
    if conn is not None:
        db.init_db(conn)  # 幂等建库 + 旧库无损迁移

    if args.command == "ingest":
        report = ingest.ingest_directory(Path(args.data_dir), Path(args.folder),
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
        aid = workflow.crop_asset(conn, Path("data"), args.asset_id,
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
        op = db.undo(conn, args.ref)
        print(f"已整体撤销操作: {op}")
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
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
