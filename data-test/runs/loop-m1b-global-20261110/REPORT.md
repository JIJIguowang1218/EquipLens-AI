# v1：配额 bug 的现场（保留作证据）

本轮是 T38 独立测试的第一次运行：**20/12**（u-exact 10/8、u-intl 10/4）。

原因：`_state_fill` 只用配额算缺口，没有把它当占槽上限；`delivery` 的 degraded 也把“抓过图但未占槽”的车型算了进去（degraded 16 > delivered 12 的假象）。

修复后用同样的隔离条件重跑，见 [`../loop-m1b-global-v2/REPORT.md`](../loop-m1b-global-v2/REPORT.md)。
