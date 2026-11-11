# 扩源测试 34 张图核对

- 来源：`data-test/evals/source-expansion-verify-20261111.json`
- 目标：3 个无图车型（泰安五岳 / 沙漠越野重型 / K-65959）
- 方法：短 query + 360 来源页 harvest；所有图均通过门卫
- 结果：34 张，identity 33 unknown / 1 probable；核验通过 1
- 页面：`review.html`（本地缩略图 22 张，其余保留原图链接）
- 用途：人工判断 unknown 到底是“标题没证据”还是“真的不是该车”

## 标注丢失说明

旧版页面在 `file://` 下访问 `localStorage` 抛错，脚本中断，标注只存在页面内存，未写入 Edge Local Storage。
Edge 的 LevelDB 中没有 `file://` key；无法从磁盘恢复。若旧标签页仍打开，见 `RESCUE.md`。
