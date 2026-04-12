# F113: Session API And Shared Entry Binding

- Feature ID: `F113`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `SessionApi` 作为 shared entry seam 的稳定语义。

## 1. 稳定语义

- all entries bind through `SessionApi`
- `SessionApi` is the entry-facing choke point
- create / resume / attach / submitStep stay on one path
