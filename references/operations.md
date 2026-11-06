# 标注与数据提取操作索引

常规修改先用[增量命令](fast-execution.md)，而不是再次手写本表各步骤。`drawctl`负责输入绑定/单页更新/渲染/PDF/复核包/交付清单；本表负责它内部的微操作语义。实际范围：本包A4＋同轴球面单片/双胶合，其他形态先适配。

建议按当前任务查下表并复用 `scripts/drawing_ops.py`。API相关操作前先读[接口对齐](api-alignment.md)对应行；新工程和冻结依赖按[执行工序](execution-workflow.md)处理。

| 规则 | 操作方法 | 验证 |
|---|---|---|
| session开场 | 按[字段来源/开场](fields-and-defaults.md)展示问句、继承已有答案或集中补问 | 记录真实来源，新工程复制不自动触发再次确认 |
| 三位/直径两位 | dimension_value；R/CT/ET/倒角/焦距三位，D01/D02/机械直径两位；指数/百分比/角度/等级按各自约定 | 遍历DXF TEXT/MTEXT数值检查；玻璃牌号及原始API审计值不强制截位 |
| 默认公差 | center_thickness_tolerance解析薄片/常规/显式覆盖；vertical_diameter生成主值与上下偏差 | 当前上偏差0.00、下偏差−0.02，保持上下关系；CT标签与技术条款同源 |
| R与面号 | surface_point确定真实点，leader端点在曲线；局部S1/S2单独引线，胶合总图S1/S2/S3，每面另列原ZOS号 | 反查leader tip与对应曲面的距离，不凭左右文字判断对应面 |
| 历史圆十字 | polished_mark插入OMD_POLISHED_CROSS；块定义含CIRCLE+两LINE，中心沿法线偏移一半径 | 核INSERT缩放/层、相切位置；称用户历史图示，不编标准号 |
| 双面CA及机械径 | 单片/子片D01/S1、D02/S2；总图D01/S1、D02/S3，公共S2另列 | 来自各子片真实OD，公共胶合面API单一半径不代替两子片OD |
| 边厚/平台 | 用真实机械轮廓`z_back(r)-z_front(r)`；horizontal_dimension引线落真实外圆两端，标签`(ET数值)`作参考；平台起止径另列 | 与CAD坐标回读；不能把单独文字一串ET当作有标注 |
| 默认倒角 | 外露边默认径向0.200×45°；选起点r=D/2−c，直线z=z(r0)+sign*tan(angle)*(r-r0)；受CA/曲面斜率限制时列明确例外 | 真正LINE/直线段，非在sag上加位移的伪倒角；检查只去料且不进入CA |
| 涂墨 | 单独BLACKEN层虚线/加粗区示意，leader“外圆涂黑”指圆柱边；平台涂墨需额外箭头；胶合后涂，通光/胶合区遮蔽 | 不能仅技术条款；所有涂墨区域能从箭头/边界辨认 |
| 材质与允差 | API的Material/目录提取；table中每子片独立列牌号、ΔnD=2B、Δ(nF−nC)=2B | 胶合总图列两片，不能合成一个材料也不写“见图” |
| 有效径 | D01=2*CA前、D02=2*CA末；局部面号按[光学概念](optical-concepts.md#图面有效径命名) | 与API显式孔径核对，不由默认90%外径代算 |
| 原生CAD/回建 | 源ZOSAPI export STEP→读实体section，而非仅B-rep边线投影；DXF附页提取值新建ZOS | 原生STEP简化轮廓差异表；compare源/回建R/t/玻璃/孔径/系统设置/光线 |
| API复核入口 | 只load/read/print/disconnect，不创建磁盘文件锁或写报告；允许包内命名mutex序列化连接 | 主线程保存结果；增量证据继承按复核范围分流 |
| PDF毫米比例 | ezdxf/Matplotlib导最终DXF到精确A4画布，PDFium渲染该PDF作为proof | 用PDF矢量坐标量27mm×2=54mm线，再看全部页 |

## 直接API数据路径

可执行入口：`scripts/zos_read.py <source.zos>`，只读stdout；原生STEP批量导出用`zos_export.py --range name:first:last --out ...`，共用统一session和mutex，脚本已实际测试。`s=oss.LDE.GetSurfaceAt(i)`；读Radius、Thickness、Material、SemiDiameter、MechanicalSemiDiameter、ChipZone、IsStop。显式孔径另读ApertureData或核对保存ZMX中的CLAP，不能只读自动SemiDiameter。平面Radius回读为inf，写回用0。

全局系：`oss.LDE.GetGlobalMatrix(i)`；保存完整旋转平移并用真实顶点检查排列。CAD和PNG的原点可能不同；建议用GCRS与顶点全局坐标核对，而不是假定均在同一物理端面。

折射率：在不保存的只读分析副本中设置选定波长，`MFE.GetOperandValue(INDX, surf, wave, 0,0,0,0,0,0)`；计算独立单片焦距时前后介质为空气，胶合内部界面保留实际玻璃。使用折射矩阵`[[1,0],[-(n2-n1)/R,1]]`与平移`[[1,t/n], [0,1]]`，独立件EFL=-1/C。图上注明计算波长，不把该数称为已实测焦距。

`ΔnD=2B`、`Δ(nF−nC)=2B`是采用该示例配置的项目批准的材料验收等级；不能替换成另一套数值规范，例如Δnd±0.0005、Δvd±0.5%。D/d波长命名保留图框文本，计算nd另说明587.562nm；数值计算不承担解释2B标准定义。

## 冲突处理

图纸不允许“待定/TBD/见面表”。本次批准的默认先填；仍无值的必要制造项在出图前集中问，不造数值。签署栏保留空白签署区不伪造人名；数值栏不留占位词。当前默认胶种/墨种按厂内受控工艺选用并满足已给厚度/遮蔽/光学条件，可表述工艺要求，不把缺失参数换个词藏起来。

建议在出图前核对名义值与显示精度。需要改变R/CT时按已授权设计流程修调并冻结；仅有出图授权时不自动改源ZOS，也不将取整差称为精确还原。派生sag/平台高度以母曲面与截止径为主控，参考尺寸另标；原始全精度API快照用于审计。
