# 技术要求配置：先改字段，再一次构建

技术要求属于项目工艺约定，不能把旧项目数值写成通用国标要求。默认值供新项目确认；既有项目的 `spec` 保留本轮确认值，单页 `spec_overrides` 优先。面分类和几何仍来自实际模型。

## 可直接修改的字段

|最近反复修改项|配置 / 操作|同步输出|
|---|---|---|
|镀膜波段、平均反射率|`coating.band_nm`、`metric`、`comparison`、`reflectance_percent`|技术要求与底部镀膜栏共用函数|
|是否写最大反射率|`coating.include_max_reflectance`；上限 `max_reflectance_percent`、`max_comparison`|false 时两处均不写 Rmax|
|入射角、偏振|`coating.incidence_deg`、`polarization`；null/空值不显示|两处统一显示|
|光圈、表面疵病、材料允差|`surface_requirements.N/delta_N/scratch_dig`、`material_requirements.*`|沿用已有表格字段，光洁度同步技术要求|
|胶合总图两张要求表|`assembly_tables.material_values/part_values` 独立布尔值|true填写，false填`-`；子片图不受总图开关影响|
|工件类型 CT 公差|`tolerances.cemented_child_center_thickness_mm`、`cemented_assembly_center_thickness_mm`|子片/总图分开；单页明确 CT 覆盖仍优先|
|注释标题、胶种、模板|`technical_text.title/adhesive/cemented_templates/single_templates/common_templates/extra_templates`|按工件类型生成；自动编号|
|镀牢、疵病、遮蔽措辞|`technical_text.adhesion_* / quality_* / masking_*`|镀膜与不镀膜分支独立|
|涂黑与墨厚|`blackening.required/thickness_mm`、`technical_text.blackening_*`|关闭时不画涂黑线/箭头；平台尺寸仍保留|
|倒角说明|从每个面机械配方 `outer_bevel` 取得实际数值|说明与胶合边引线不再写死 0.200；修改几何仍走机械变更流程|

模板及可用占位槽见 `assets/technical-text.json` 与 `scripts/technical_spec.py:render_notes`。支持 Python 数字格式如 `{ct_tolerance:.3f}`；未知槽会报错，不能直接作为待定文字出图。长文本仍需图像复核遮挡；配置模板不等于自动排版。

### 底部两表的实际能力

面号/CA/机械直径/材料由模型数据填充，ΔnD及Δ(nF−nC)读配置；纵向位置通过 `aperture_table_y/material_table_y` 调整。底部表格的显示开关、列名、列宽、行高和字号尚未独立配置，仍在 `page_renderer.py`。请称为“数据驱动、部分布局可调”，不要笼统称“完全参数化”。上面的 `assembly_tables` 专指左上两张要求表，不控制底部面表/BOM。

恢复胶合总图零件要求时，可提交 `{"assembly_tables":{"material_values":false,"part_values":true}}`；字段来自本项目surface_requirements与实际组数据。材料表7项与零件表8项分别检查，D01/D02取组外露两面，f取组焦距。旧工程缺省仍兼容两表填`-`，所以新要求需要显式存入工程。

## 一次提交多字段

在本批 `.pdfout` 副本运行；旧冻结工程不动。只改文字不启动 ZOS/光追。

```powershell
# change.json 为 UTF-8，避免命令行传中文模板与引号的转义问题
# {"coating":{"include_max_reflectance":false},
#  "technical_text":{"adhesive":"光敏胶"}}
python <本批skill>/scripts/drawctl.py patch-spec <project.json> --file change.json
python <本批skill>/scripts/drawctl.py build <project.json>
python <本批skill>/scripts/drawctl.py review-packet <project.json>
```

单字段仍可 `set-spec --key coating.include_max_reflectance --value false`。单页加 `--page L2A`。`show-spec <project.json>` 导出逐页最终有效配置；`review/request.json` 自动带相同配置，verifier 以它为本轮工艺依据，不强行套历史例子。

旧工程首次配置编辑会补入文字模板与新增可配置键；保持其已有数值。历史未记录 Rmax 开关的工程按旧行为显示，用户明确删除时设 false。新工程默认不附加 Rmax。修改模板文件、policy 或渲染模块均计入缓存签名，防止改了却不重绘。

## 本轮复盘后暂不混入文字修改的项目

- 三组直径、平台宽度、通光口径：属于机械/光学事实，不能只修改技术说明代替验证。
- `blackening.region/ink_spec`、`inspection_data/coating_process`、`formatting_starting_points` 尚非完整可执行配置；本轮不宣称这些旧字段已生效。需要增补检测清单时先用 `extra_templates`，自定义涂黑区域仍改机械定义与引线。
- 字号与锚点已有 `set-layout`；新增超长模板时检查图像，不再为排版重跑光学。
