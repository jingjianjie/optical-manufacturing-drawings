# API阅读与操作对齐

建议每个涉及API的新工序先读本表对应入口和脚本的相关函数，再对照安装版本帮助确认对象/枚举/参数及副作用。无需每次读完整手册：优先复用已验证入口；发现版本差异时，查安装版ZOS-API Syntax Help、zospy方法签名或连接后的CLR `__doc__` / `GetType()`，用小范围读回验证结论。网络资料仅作本地说明不足时的补充。

|工序|先阅读的接口／实现|建议对齐方法与读回|
|---|---|---|
|加载与只读快照|[zos_read.py](../scripts/zos_read.py)的session/snapshot；ZOS.connect、系统load、LDE.GetSurfaceAt|核standalone、路径、面数、源哈希；命名mutex序列化，结束disconnect；不写源文件|
|首次两输入建档|[freeze_inputs.py](../scripts/freeze_inputs.py)；[profile_geometry.py](../scripts/profile_geometry.py)|调用前确认同轴、配置、面型和机械schema；索引+1映射，CT取API，ET/min厚分别算；输出只是intake|
|材料目录|MaterialCatalogs.GetCatalogsInUse/AddCatalog；ILDERow.Material/MaterialCatalog|目录在解析牌号前加入，MaterialCatalog按读取属性使用；读回真实目录，避免拼目录前缀当材料名；CLR数组先转list再切片|
|折射率／独立件EFL|freeze_inputs的INDX调用；MFE.GetOperandValue签名；constants.Editors.MFE.MeritOperandType|读surface/wavelength序号与参数签名，直接查询无需建删operand；F/d/C分析在不保存源模型的内存实例完成，系统波长先冻结|
|坐标与STOP|LDE.GetGlobalMatrix、ILDERow.IsStop、Aperture.GCRS.GetSelectedSurface/SetSelectedSurface|先读轴和原点；设置STOP时只设目标面True，别循环给所有其他面False；全局矩阵与选中面读回|
|回建系统|ZOS.create_new_system('Sequential')、SystemData、MCE.NumberOfConfigurations、Fields/Wavelengths、ApertureData、Cell.Solve|先按[恢复字段](review-and-roundtrip.md#通过图纸包还原zos)列字段，再读相应安装版接口；用实际ZemaxApertureType/FieldType枚举；主波长读IsPrimary；保存重开核对。尚无通用回建CLI时记录专项适配|
|原生CAD|[zos_export.py](../scripts/zos_export.py)、Tools.OpenExportCAD、CADFileType|核面范围、SurfacesAsSolids、DummyThickness0.001、Succeeded及文件；现有几何证据导出NumberOfRays=0|
|读STEP剖切|[step_section.py](../scripts/step_section.py)及OCP对应接口|核读取状态、实体/切平面及坐标；Edge/Edge_s按版本适配；只读原生几何|
|DXF／图块／文字|[drawing_ops.py](../scripts/drawing_ops.py)、[symbol_blocks.py](../scripts/symbol_blocks.py)、[包内CAD](../cad/CAD.md)|核INSERT缩放/旋转、文本bbox、layer与纸面单位；看新DXF回读图像|
|公差／缓存／PDF|[drawctl.py](../scripts/drawctl.py)、[pdf_export.py](../scripts/pdf_export.py)|先看--help和project字段；签名失效范围、尺寸与notes同源；PDF验A4和一条真实长度|
|回建采样比较|[compare_rays.py](../scripts/compare_rays.py)、BatchRayTrace.CreateNormUnpol/ReadNextResult|核success/error/vignette、xyz/lmn返回位置、Radial归一化与样本；默认摘要＋异常索引，--details诊断可选|

## 当前接口能力边界

- `freeze_inputs`的“同轴球面”是调用前提，不是全功能拓扑证明；复杂配置、偏心、非球面或未冻结solve宜先专项适配。平面半径以null表示，图面标签为“平面”；未知面型仍需专项适配。
- `zos_read`基础快照不是完整系统恢复器；完整字段仍按恢复清单对照。
- `drawctl init`可接受尚无native/附页的intake用于开发，但不证明CAD/回建齐全；两份receipt只是记录实际审查，不认证内容。
- defaults镀膜`incidence_deg/polarization/surface_selection`预留null；当前`set-spec`不支持将这些null字段补为任意类型，renderer也未消费它们。null不是零度/无偏振承诺。本次给了这些条件时，建议在冻结工程内适配schema/渲染并检验图面，不能仅改JSON就称已落图。当前自动AR面来自外露/胶合拓扑。
- 原始mechanical.json建议由`freeze_project`留存；freeze_inputs的data/mechanical.json含重算派生量，不代替原始输入。

整体光路PNG使用[system_layout.py](../scripts/system_layout.py)，见[能力与例子](system-layout.md)。环境/字体路径见[environment](environment.md)，无需其他skill。
