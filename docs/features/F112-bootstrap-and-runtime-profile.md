# F112: Bootstrap And Runtime Profile

- Feature ID: `F112`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 bootstrap 责任链与 `RuntimeProfile` authority 的稳定语义。

## 1. 稳定语义

- bootstrap resolves topology before work starts
- `RuntimeProfile` owns provider/model authority
- host hints cannot override profile authority
