# 旧页面标注抢救

仅当**旧核对页仍然打开**时有效：

1. 不要关闭标签页；
2. 按 `F12` 打开开发者工具，点 `Console`；
3. 粘贴下面一行，回车：

```js
copy(JSON.stringify([...document.querySelectorAll('[data-v]')].reduce((o,e)=>(o[e.dataset.v]=e.value,o),{})))
```

4. 内容已复制到剪贴板，发给我，或保存为 JSON。

如果页面已经关闭/刷新：Edge 的 `file://` localStorage 没有写入，标注无法从磁盘恢复，只能在新版页面重标。
新版 `review.html` 已修复：localStorage 失败不会中断脚本；导出按钮会显示 JSON 文本框，可直接复制。
