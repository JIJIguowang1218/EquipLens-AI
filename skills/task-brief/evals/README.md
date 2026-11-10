# task-brief 评测

按 Agent Skills 的 eval 约定：每个 case 同时跑 **with_skill** 与 **without_skill**，
比较“有没有方法引导”的差异，而不是只跑一次看输出像不像。

- 自动检查：schema 通过、部件保留（含 custom_*）、每件有 design_axes/why、assumptions 非空；
- 人工 rubric（0/1/2）：品类/基型/构型是否合理；设计对象分类；关系轴；设计轴；未知部件处理；是否编造；
- 泛化：至少留一类没在 skill 里出现过的品类（如矿山自卸车）和两个词表外部件；
- 判定：如果 with_skill 在 rubric 上没有稳定优势，就不要把它当“必要组件”，只保留 schema/校验。
