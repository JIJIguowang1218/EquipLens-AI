# 依赖与运行环境

更新：2026-11-13

## 必需

- Python **3.11**（3.11.5 验证；不要用 3.13）
- `pip install -r requirements.txt`
- DeepSeek API key：`~/.equiplens/deepseek.env`
  ```
  DEEPSEEK_API_KEY=sk-...
  ```
  没有 key 时：只能跑门卫/本地抓取/部分测试；规划、引用核验、重规划不可用。
- 并发（2026-11-13 起）：只用标准库 `concurrent.futures.ThreadPoolExecutor`，
  **没有新增第三方依赖**；`requirements.txt` 未变。

## 模型

- 门卫：`unum-cloud/uform3-image-text-english-small`，首次运行自动下载（约 59MB）；
  `HF_ENDPOINT=https://hf-mirror.com` 已默认。
- 可选旧 Chinese-CLIP：`OFA-Sys/chinese-clip-vit-base-patch16`；
  只有旧探针用，当前 loop 不需要。

## 可选

- `torch` CPU 版 + `transformers`：旧 Chinese-CLIP 探针；
- `crawl4ai` + `playwright`：JS 门户真实渲染；当前 loop 不依赖；
- `python-pptx`：报告 PPT 导出。

## 快速自检

```bash
PYTHONPATH=src python scripts/check_env.py
PYTHONPATH=src python tests/test_retrieval_engine.py   # 40/40，需 test fixtures
PYTHONPATH=src python tests/test_imagesearch.py        # 14/14
PYTHONPATH=src python tests/test_planning.py           # 14/14
PYTHONPATH=src python scripts/run_ledger.py --check     # 87 records，0 issue
```

## 新机器接续

- 步骤：`docs/HANDOFF.md` §0.1（30 分钟接续）；
- 数据/测试文件哪些被重算、哪些结论作废：`docs/DATA-CHANGELOG.md`；
- 计价：`src/equiplens/pricing.py`（峰/谷 + Search/Fetch 按次）。

## 数据库

`data-test/equiplens.db` 是本地 SQLite **测试素材库**，不是测试结论：
- 存车型/资产/图片路径等，供分析/UI/旧 text-run 使用；
- 被 gitignore，不随仓库同步；
- `--web-only` 检索 loop 不依赖它；
- 新电脑缺它时，部分旧测试/演示会失败，但不影响核心检索代码。

## 启动正常检索

```bash
PYTHONPATH=src python -m equiplens.retrieval_engine \
  --brief data-test/evals/task-briefs-20261109/brief-m1-desert.json \
  --web-only \
  --plan data-test/runs/plan-ab4-20261111/A2/plan-ranked.json \
  --run-root data-test/runs --run-id my-run
```
