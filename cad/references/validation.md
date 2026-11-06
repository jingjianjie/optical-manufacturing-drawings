# 实测范围（2026-11-05）

环境：Windows，Python 3.11，ezdxf 1.4.5，matplotlib 3.7.1，fontTools 4.40.0；.NET 8 目标，ACadSharp 3.8.35。

- 实际光学图框：94 个 LINE/LWPOLYLINE/MTEXT 实体，中文路径，R2010 Unicode DXF → DWG → DXF 成功；回读预览中文与符号正常，目检已做。
- 合成夹具：布局/块/属性文字盘点，黑体缺 Ø 的检测，宋体 TTC 两个 face 检查，同文件比较一致，线端点变化能检出，R2000 中文转义转现代 DXF 后恢复成 Unicode 且实体数保持。
- 旧版失败案例：ANSI_1252/R2000 Unicode 转义被当成字面文本；同一错误内容前后相等，原有纯字符串比对无法发现。现由 inspect + unicode-copy + 最终回读预览识别和修正。
- 严格 compare 会报告某些 reader 补充默认 DXF 字段的差异；需区分默认值展开、编码表示变化和实际变更，不把差异数量当作丢实体数量。

未验证：AutoCAD GUI 原生打开/从 DWT 新建、动态块、代理对象、三维实体、SHX/bigfont 的真实绘制、打印机/CTB/纸空间打印。遇这些任务应切换合适路径验证。
