# task-brief 人工评审（10 案例 × with/without skill）

## 怎么看

1. 打开本目录 `Cxx__with_skill.json`，看 `brief` 的 request/parts/regions/assumptions；
2. 对照 `skills/task-brief/evals/evals.json` 的 prompt / expected_output；
3. 每个案例按 0/1/2 打分（0=错/编造，1=部分可用，2=可直接用）：
   - 品类/基型/构型是否合理；
   - 设计对象分类（region / part / function）是否正确；
   - relation_axis（exact/environment/platform/cross）是否有依据；
   - design_axes 是否选对（2–4 个，且有 why）；
   - 未知部件是否保留为 custom_*、是否给出位置/功能/族；
   - 是否有编造（具体车型、无依据的尺寸/法规）。

> 自动断言只检查 schema/数量/是否有轴，**不判断语义对错**；这一页需要你判断。

| 案例 | with_skill 自动 | without_skill 自动 | 品类/基型 | 对象分类 | 关系轴 | 设计轴 | 未知部件 | 是否编造 | 总体 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| C01 | PASS | FAIL |  |  |  |  |  |  |  |
| C02 | PASS | FAIL |  |  |  |  |  |  |  |
| C03 | PASS | PASS |  |  |  |  |  |  |  |
| C04 | PASS | FAIL |  |  |  |  |  |  |  |
| C05 | PASS | FAIL |  |  |  |  |  |  |  |
| C06 | PASS | FAIL |  |  |  |  |  |  |  |
| C07 | PASS | FAIL |  |  |  |  |  |  |  |
| C08 | PASS | FAIL |  |  |  |  |  |  |  |
| C09 | PASS | FAIL |  |  |  |  |  |  |  |
| C10 | PASS | FAIL |  |  |  |  |  |  |  |

## 重点看哪几个

- **C02 重型吊车**：口语类目，看是否落成汽车起重机/全地面或明确待确认，而不是硬猜；
- **C06–C10**：挖掘机/装载机/搅拌车/环卫车/高空作业车，全部是 skill 没写过的品类；看有没有被硬套成“卡车”；
- **C08–C10 的上装件**（搅拌罐/压缩箱/臂架/支腿）：词表没有，必须 custom_* + 合理族/轴；
- **C01/C05**：同一“前脸+部件”在沙漠 vs 干线，关系轴应不同（environment vs platform/exact）。
