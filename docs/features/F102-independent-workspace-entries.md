# F102: Independent Workspace Entries

- Feature ID: `F102`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `CLIEntry` 与 `WebEntry` 作为独立工作环境入口应共享的稳定产品语义。

## 1. 这份文档回答什么

什么叫“独立工作环境入口”。

## 2. 稳定语义

- CLI 与 Web 都是 `Garage` 自己的产品入口
- 它们可以有不同 UX，但不能拥有不同 runtime truth
- 它们都必须进入同一条 `Bootstrap -> SessionApi -> Session` 主链
