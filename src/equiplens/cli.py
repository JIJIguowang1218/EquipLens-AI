"""EquipLens 命令行入口。

用法（在仓库根目录）:
  python -m equiplens ingest <图片文件夹> [--data-dir data] [--platform 名称] [--license 档位] [--report 输出.json]
"""

import argparse
import json
import sys
from pathlib import Path

from . import ingest


def main(argv=None):
    parser = argparse.ArgumentParser(prog="equiplens", description="EquipLens-AI 数据工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="批量导入图片并判重（M1）")
    p_ingest.add_argument("folder", help="待导入的图片文件夹")
    p_ingest.add_argument("--data-dir", default="data", help="数据目录（默认 ./data）")
    p_ingest.add_argument("--platform", default="本地导入", help="来源平台说明")
    p_ingest.add_argument("--license", default="web_third_party",
                          choices=["client_provided", "self_captured", "web_official", "web_third_party"],
                          help="本批素材授权档（默认 web_third_party 待确认，最保守）")
    p_ingest.add_argument("--report", default=None, help="导入报告 JSON 输出路径（可选）")

    args = parser.parse_args(argv)

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
    return 1


if __name__ == "__main__":
    sys.exit(main())
