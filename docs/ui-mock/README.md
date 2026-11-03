# UI 语言样张（v2 规格的可视化依据）

三个 1440×900 画板：`s0`（立项台）、`s1`（检索台 · 结果筛选）、`s1r`（检索台 · 检索中）。

- `screens.html`：单文件样张，纯 CSS，无外部依赖（字体走系统栈）
- `shot.py`：用 Playwright 逐个画板截图（2× 分辨率）

重新生成：

```bash
python docs/ui-mock/shot.py
```

产物：`s0.png` / `s1.png` / `s1r.png`。

> 用途：评审视觉语言（墨/纸、测量轨、裁切标记、等宽型号）是否成立；不是最终实现。
> 正式实现见 `docs/web-interaction-spec-v2.md` §11 的技术栈。
