# 已落成的执行工具

建议先按[执行工序](execution-workflow.md)复制`.pdfout`工程，再用该工程中的脚本。背景观察单独见[Pi复盘](pi-replay-lessons.md)，此页只保留工具用法。

## 两文件首次建档

`python -X utf8 scripts/freeze_inputs.py design.zos mechanical.json --out NEW_ARCHIVE`

适用同轴Standard球面两面子片及双胶合，需先确认[接口能力边界](api-alignment.md#当前接口能力边界)。一次standalone连接读源处方/目录/F-d-C/STOP/GCRS/圆孔径，重算CT/EFL、ET与最小厚并分组，生成drawctl init输入；不保存源文件、不覆盖旧档案。原始机械JSON由工程冻结脚本另外保留。随后`drawctl init --archive NEW_ARCHIVE --out PROJECT`。

此入口仅完成建档；原生CAD、可读恢复附页和回建按本次工序补齐。建议首次新拓扑先确认适配范围，配置计数可查MCE.NumberOfConfigurations。

## 标记复用与文字

包内提供可由基础几何重新生成的符号库：`assets/symbols/optical-house-symbols.dxf`：

|块名|插入方式|含义和边界|
|---|---|---|
|OMD_POLISHED_CROSS|`polished_mark(ms,contact,normal,radius)`|圆十字，中心按法线偏移一个半径；用户历史图示，不宣称未经核验标准含义|
|OMD_ARROW|`arrow(ms,tip,tail,size)`|实心箭头；局部原点是尖端，统一缩放与旋转|

`symbol_blocks.ensure(doc)`只建一次定义，drawing_ops插入INSERT，减少重复实体/微操。块实体用layer0继承插入层；当前管线已经支持渲染INSERT。粗糙度/形位/基准图形暂不凭截图捏造，未找到原DWG/DXF标准块时保留当前合法标注。

`leader`用实际字体包围框定文字下划线及斜线起点；长说明用`wrapped_text(ms,text,point,width,height)`按字体宽换行。未知布局仍看图；这些函数不承诺全自动避碰。ET不是最小厚：两者由profiles独立计算，负片最小厚可在中心。

## 命令/进程

`python scripts/run_checked.py --log run.log --timeout 180 -- python -X utf8 script.py ...`

使用参数数组直接运行，不接tee/tail。日志旁JSON保存真实退出码/耗时；超时124只停止该自有命令，不杀用户ZOS。失败展示尾部；返回0不代替文件/哈希/图像验收。必须shell管道时显式pipefail并保存原Python退出码，echo/tail成功不能覆盖失败。

建议独立审查聚焦当前页/证据；明显滞后时先收紧范围，仍无终态则记录未完成并结束等待，避免重读大历史会话。

`drawctl pack`已规范化相对路径。纯图面改动沿用同源证据；变化页自动失效，未变页缓存保留。单页显式CT覆盖优先，尺寸与技术条款用同一解析值。

## 自动回建摘要

`python scripts/compare_rays.py source.zos rebuild.zos --out summary.json`。建议只看最大差、异常数与索引；`--details`用于有实际需要的诊断，不人工遍历全部光线。样本及适用范围见[复核与还原](review-and-roundtrip.md)，该命令不生成回建ZOS。
