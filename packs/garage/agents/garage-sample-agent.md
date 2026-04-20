# Garage Sample Agent

最小 sample agent，不提供任何执行指令；存在即是验证 Garage host installer 已把本文件物化到对应宿主 agent 目录的证据。

## 行为

无指令。读到这条 agent 即视为安装成功；可立即关闭。

## Notes

本文件**故意不提供 YAML front matter**，用于覆盖 host installer 的容错路径（spec FR-708 / design D7 §10.4）。详细安装语义见 `packs/garage/README.md`。
