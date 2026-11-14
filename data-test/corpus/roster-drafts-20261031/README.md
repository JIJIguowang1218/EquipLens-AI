# 名录草稿归档（2026-10-31）

> 一句话：这是 `roster-generate` 在 2026-10-31 生成的 22 份**候选名录草稿**，
> 已归档但**从未锁定**——用于追溯"10-30 之后名录生成为什么还在波动"，
> 不是生产数据，也不是评测基准。

## 1. 这些文件是什么

`equiplens.roster.generate_roster()` 的输出：给一个类目词，去百度网页搜索
"类目 + 车型榜单"类文章，在标题/摘要里抽品牌×型号，跨查询按频次合并，
产出候选名录（品牌 / 型号 / 提及次数 / 来源链接）。

生成命令（默认参数，未加 `--max-articles` / `--top`）：

```bash
python -m equiplens.cli roster-generate 沙漠牵引车 --data-dir data-test
python -m equiplens.cli roster-generate 牵引车   --data-dir data-test
```

产物命名 `roster-<类目>-<YYYYMMDD>-<HHMMSS>.json`，原本落在 `--data-dir` 根目录；
本次归档把 22 份整体搬进本目录，**文件名保持不变**（时间戳是唯一身份）。
每个文件的时间、数量、sha256 见 [`MANIFEST.json`](MANIFEST.json)。

## 2. 字段

| 字段 | 含义 |
|---|---|
| `category` | 输入的类目词 |
| `generated_at` | 生成时间（本地时间，秒级） |
| `status` | 恒为 `pending_lock`：等产品负责人增删后才算锁定 |
| `queries` | 实际发出的 3 条检索词（"…车型大全 推荐" / "…有哪些型号" / "…报价 型号"） |
| `articles` | 命中的文章（标题 + URL），只取 SERP 结果块，未抓正文 |
| `candidates` | 候选：`brand` / `model` / `mentions`（跨文章提及次数）/ `sources`（出处） |

## 3. 事实与边界（重要）

- 共 **22 次生成 / 2 个类目**：
  - `沙漠牵引车` 18 次（16:57:27 → 20:43:42），候选 4–12 个、文章 18–20 篇；
  - `牵引车` 4 次（17:27:39 → 18:12:45），候选稳定 4 个、文章 35 篇。
- **同参数重跑不稳定**：沙漠牵引车的候选数经历 **12 → 10 → 4 → 11 → 6** 四段变化，
  相邻两次重跑间隔最短 68 秒。当天 `src/equiplens/roster.py` 没有任何提交
  （最后一次改动是 10-18 的 `3197f85`），所以波动不是已提交代码变化带来的，
  只可能是 SERP 结果的随机性 / 抽取规则波动 / 本机未提交的临时调试（无法取证）。
  → 这批文件**不能当回归基线**，只能当"当时确实不稳定"的证据。
- **不是锁定名录**：`status` 全是 `pending_lock`，没有任何一份被增删锁定过。
  生产与评测用的是 T13–T15 的锁定名册（例：`data-test/roster-沙漠牵引车-20261017-163313.json`，
  当时标注"锁定=全量"，12 台）。
- **当时没有登记**：`docs/test-log.md` / `docs/DATA-CHANGELOG.md` 里原本没有这批 run 的记录，
  2026-11-14 归档时才补记（见 `docs/DATA-CHANGELOG.md` §24）。用途只能从时间、类目和
  内容反推，**不要为它编一个实验编号**。

## 4. 目录关系

| 位置 | 是什么 |
|---|---|
| **本目录** | 10-31 的名录草稿（22 份，未锁定） |
| `data-test/corpus/batch-corpus-roster-*-20261030/` | 由名录派生的**语料采集批**：名录 → 批次计划 → 正文 |
| `data-test/roster-<类目>-2026101{7,8}-*.json` | 10-17/18 的早期草稿，按历史约定直接放 `data-test/` 根，本次未迁移 |
| `src/equiplens/roster.py` | 生成器（其 docstring 规则④：名录 JSON 归档 `data-test/`） |

## 5. 复现与校验

```bash
# 重跑（新文件会写到 data-test/ 根目录，不覆盖本归档）
python -m equiplens.cli roster-generate 沙漠牵引车 --data-dir data-test

# 校验归档完整性（对照 MANIFEST.json 的 sha256）
python -c "import json,hashlib,pathlib;m=json.load(open('data-test/corpus/roster-drafts-20261031/MANIFEST.json',encoding='utf-8'));[hashlib.sha256(pathlib.Path(e['file']).read_bytes()).hexdigest()==e['sha256'] or (_ for _ in ()).throw(AssertionError(e['file'])) for e in m['files']];print(len(m['files']),'files OK')"
```

> 注意：重跑会触网（百度 SERP 需 Crawl4AI 真浏览器；requests 直连必触发安全验证），
> 且结果不可复现——这正是归档而不是"随时重跑"的原因。
