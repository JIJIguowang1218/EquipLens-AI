# A 测试：plan 串行 vs 并发

> 唯一变量：`--concurrency`。查询构造、抽取 prompt、模型、温度、topup 全部相同。
> 只跑 plan 阶段，不进 rank/loop。

| case | 臂 | 耗时 s | 候选 | 抽取 kept | tokens in/out | chat 调用 | chat 总 ms | 单次最大 ms |
|---|---|---:|---:|---:|---|---:|---:|---:|
| c1-desert-tractor | serial | 117.7 | 14 | 35 | 39410/20200 | 8 | 109775 | 22707 |
| c1-desert-tractor | concurrent | 49.5 | 20 | 39 | 39313/19066 | 8 | 103064 | 21889 |
| c2-reach-stacker | serial | 122.5 | 25 | 45 | 38702/20909 | 8 | 114234 | 21339 |
| c2-reach-stacker | concurrent | 39.3 | 21 | 33 | 38793/17619 | 8 | 98730 | 22611 |
| c3-tractor | serial | 99.2 | 30 | 39 | 29848/17640 | 6 | 92595 | 25006 |
| c3-tractor | concurrent | 23.1 | 27 | 38 | 29893/11931 | 6 | 66858 | 16672 |
| c4-forklift | serial | 97.6 | 27 | 34 | 29820/17595 | 6 | 91463 | 29206 |
| c4-forklift | concurrent | 25.2 | 21 | 24 | 29797/14134 | 6 | 74581 | 23867 |
| c5-roller | serial | 81.3 | 36 | 45 | 29858/14325 | 6 | 75201 | 16939 |
| c5-roller | concurrent | 18.2 | 36 | 40 | 29858/9946 | 6 | 52640 | 11545 |

## 汇总

- **serial**：总耗时 518.3s，候选 132，输出 tokens 90669
- **concurrent**：总耗时 155.3s，候选 125，输出 tokens 72696

**加速比：3.34×**（518s → 155s）
