# legacy 词表（静默，不参与主链）

这些文件**默认不被主体代码加载**，只用于考古、对照实验或旧脚本。
规则见 `docs/vocabulary-policy.md`。

| 文件 | 说明 | 加载方式 |
|---|---|---|
| `part_taxonomy.json` | 11 个内置部件键/区域/术语 | 仅 `scripts/make_ui_fixtures.py` 显式读取 |
| `category_profiles.json` | 类目档案（旧 textrun） | 旧链路默认路径；loop 不读 |
| `brand_aliases.json` | 中外品牌别名 | 仅 `EQUIPLENS_ENABLE_LEGACY_BRANDS=1` |

sha256：

```
0b4a521be01152ed63aa8c4bf856c70a34d8b5ec749b8c8d3dd589e4240053bb  part_taxonomy.json
4f1e79a3357834aba354305cf49118c884482753c03cc0ea037197b2b89b7703  category_profiles.json
a3bb257a8117de60a98a2d1dc4e79ea33f738a822800c351acb499dd4fba5654  brand_aliases.json
```

**不要**把这里的文件重新 import 进 `src/equiplens/`；确需对照，用显式开关并记录在实验文档里。
