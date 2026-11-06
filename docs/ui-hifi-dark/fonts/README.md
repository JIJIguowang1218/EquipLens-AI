# Equip 字体（暗色高保真）

本目录里的字体是 **IBM Plex** 家族的子集，按 SIL Open Font License 1.1 使用，
并已改名以遵守 IBM 保留字体名 “Plex” 的条款。界面里显示为：

| 字体 | 用途 | 来源 | 字重 |
|---|---|---|---|
| Equip Sans | 拉丁文、数字、界面正文 | IBM Plex Sans（variable） | 100–700 |
| Equip Sans SC | 简体中文、中文标点 | IBM Plex Sans SC 1.1.0 | 400 / 500 / 600 |
| Equip Mono | 计数、页码、序号、字段标签 | IBM Plex Mono | 400 / 500 / 600 |

## 为什么用它

- **可商用**：SIL OFL 1.1 允许商用、嵌入、子集化与再分发；只要保留版权与许可声明，
  且修改版不使用保留字体名 “Plex”。
- **中英同一骨架**：Plex Sans 与 Plex Sans SC 同属一个设计家族，中英混排不会出现
  “拉丁一套、中文另一套”的骨架冲突；Plex 的工程感也贴合设备/工业语境。
- **可移植**：不再依赖 Windows 的 Microsoft YaHei 或 macOS 的 PingFang 作为主中文字体，
  在无系统中文字体的环境里也能得到一致结果。

## 做了什么修改

1. 从 IBM Plex Sans / Sans SC / Mono 的官方文件中取 UI 用到的 706 个字符
   （HTML + JS + fixture 文案 + 常用中英标点）做子集，输出 woff2；
2. 将字体名从 “IBM Plex …” 改为 “Equip …”（family / full / PostScript / 命名实例），
   以符合 OFL 的 Reserved Font Name 条款；
3. 未改变字形轮廓、字距或任何设计参数。若需要完整字符集，可换回未子集的原始字体，
   页面 CSS 的 `@font-face` 指向新文件即可。

## 许可

- `OFL-IBMPlexSans.txt`
- `OFL-IBMPlexSansSC.txt`
- `OFL-IBMPlexMono.txt`

OFL 1.1 允许把字体嵌入产品并随产品分发，但不允许单独售卖字体本身。
如果之后要把字体换成别的家族，请同时替换本目录文件、`hifi.css` 顶部的
`@font-face` 和 `index.html` 里的内联 `@font-face`。

## 原始来源

- IBM Plex：<https://github.com/IBM/plex>
- IBM Plex Sans SC（npm 包，含完整 woff2）：<https://www.npmjs.com/package/@ibm/plex-sans-sc>
- SIL Open Font License 1.1：<https://openfontlicense.org/>
