# UWB数据分析工具集

这是一个用于分析UWB（Ultra-Wideband）测距数据和加速度数据的Python工具集，支持批量处理、数据可视化和综合报告生成。

## 功能特性

### 🔍 数据解析
- **UWB测距数据包解析**：支持DD 66开头、AA BB结尾的数据包格式
- **加速度数据包解析**：支持AA CC FF 1C开头、DD CC结尾的数据包格式
- **批量文件处理**：支持同时处理多个数据文件
- **数据验证**：自动验证解析数据的合理性

### 📊 数据分析
- **统计分析**：计算平均值、标准差、最值等统计指标
- **数据可视化**：生成距离趋势图、分布直方图、箱线图等
- **异常检测**：识别和处理异常数据点
- **多文件对比**：支持多个数据文件的对比分析

### 📋 报告生成
- **HTML综合报告**：包含统计信息、数据表格和图表
- **JSON数据导出**：便于程序化处理
- **图表导出**：高质量PNG格式图表
- **可配置模板**：支持基础、详细、性能等多种分析模板

## 文件结构

```
3_Locate/
├── README.md                    # 本说明文件
├── config.py                    # 配置文件
├── run_analysis.py              # 批处理脚本（推荐使用）
├── uwb_analyzer_enhanced.py     # 增强版分析器
├── uwb_data_analyzer.py         # 原始分析器
├── distance_plotter.py          # 距离绘图器
├── data_table.html              # 生成的HTML报告
├── 19-24_1-2_1.txt             # 示例数据文件
├── 19-24_1-3_1.txt             # 示例数据文件
├── 19-24_2-1_1.txt             # 示例数据文件
├── 19-24_2-3_1.txt             # 示例数据文件
├── 19-24_3-1_1.txt             # 示例数据文件
├── 19-24_3-2_1.txt             # 示例数据文件
└── analysis_output/             # 分析结果输出目录
    ├── comprehensive_analysis.html
    ├── analysis_data.json
    └── uwb_analysis_charts.png
```

## 快速开始

### 1. 环境要求

```bash
pip install matplotlib numpy
```

### 2. 基本使用

```bash
# 使用默认设置分析所有txt文件
python run_analysis.py

# 分析特定模式的文件
python run_analysis.py -p "19-24_*.txt"

# 使用详细模板，输出到指定目录
python run_analysis.py -o results -t detailed

# 显示详细信息
python run_analysis.py -v
```

### 3. 命令行选项

```bash
python run_analysis.py --help
```

**主要选项：**
- `-p, --pattern`: 文件匹配模式（默认：*.txt）
- `-o, --output`: 输出目录（默认：analysis_output）
- `-t, --template`: 分析模板（basic/detailed/performance）
- `-v, --verbose`: 显示详细信息
- `--list`: 列出匹配的文件
- `--info FILE`: 显示指定文件的信息
- `--templates`: 显示可用的分析模板

## 数据格式说明

### UWB测距数据包格式
```
包头: DD 66 (2字节)
主机ID: 4字节 (大端序)
从机ID: 4字节 (大端序)
距离数据: 2字节 (大端序)
包尾: AA BB (2字节)
```

### 加速度数据包格式
```
包头: AA CC FF 1C (4字节)
设备ID: 4字节 (大端序)
X轴加速度: 2字节 (有符号，大端序)
Y轴加速度: 2字节 (有符号，大端序)
Z轴加速度: 2字节 (有符号，大端序)
X轴陀螺仪: 2字节 (有符号，大端序)
Y轴陀螺仪: 2字节 (有符号，大端序)
Z轴陀螺仪: 2字节 (有符号，大端序)
高度: 4字节 (大端序)
包尾: DD CC (2字节)
CRC16校验: 2字节 (大端序)
```

## 分析模板

### 基础模板 (basic)
- 生成HTML报告
- 包含基本统计信息
- 生成基础图表

### 详细模板 (detailed)
- 包含基础模板的所有功能
- 导出JSON和CSV数据
- 异常值分析
- 更详细的统计信息

### 性能模板 (performance)
- 包含详细模板的所有功能
- 性能指标分析
- 时序分析
- 系统性能评估

## 输出文件说明

### HTML报告 (comprehensive_analysis.html)
- 综合数据分析报告
- 包含统计摘要、数据表格和图表
- 支持多文件对比分析
- 响应式设计，支持移动端查看

### JSON数据 (analysis_data.json)
- 完整的分析数据
- 包含原始数据包和统计信息
- 便于程序化处理和二次开发

### 图表文件 (uwb_analysis_charts.png)
- 距离数据趋势图
- 数据分布直方图
- 统计箱线图
- 距离变化率图

## 配置说明

可以通过修改 `config.py` 文件来自定义分析参数：

```python
# 数据包配置
UWB_PACKET_CONFIG = {
    'header': [0xDD, 0x66],
    'tail': [0xAA, 0xBB],
    # ... 其他配置
}

# 数据验证配置
VALIDATION_CONFIG = {
    'uwb': {
        'distance_range': (0, 65535),
        # ... 其他配置
    }
}
```

## 高级用法

### 1. 程序化调用

```python
from uwb_analyzer_enhanced import EnhancedUWBAnalyzer

analyzer = EnhancedUWBAnalyzer()
results = analyzer.parse_multiple_files("*.txt")
output_files = analyzer.generate_comprehensive_report("output")
```

### 2. 自定义分析

```python
from config import AnalysisConfig

config = AnalysisConfig()
# 修改配置参数
config.ANALYSIS_CONFIG['filtering']['distance_threshold'] = (0, 5000)
```

### 3. 批量处理脚本

```bash
#!/bin/bash
# 批量处理多个目录
for dir in */; do
    echo "处理目录: $dir"
    cd "$dir"
    python ../run_analysis.py -o "../results/$dir"
    cd ..
done
```

## 故障排除

### 常见问题

1. **找不到文件**
   ```bash
   python run_analysis.py --list  # 检查文件是否存在
   ```

2. **解析错误**
   - 检查数据文件格式是否正确
   - 确认文件编码为UTF-8
   - 查看详细错误信息：`python run_analysis.py -v`

3. **图表生成失败**
   - 确保安装了matplotlib：`pip install matplotlib`
   - 检查中文字体支持

4. **内存不足**
   - 减少同时处理的文件数量
   - 使用基础模板而不是详细模板

### 调试模式

```bash
# 显示详细信息
python run_analysis.py -v

# 检查单个文件
python run_analysis.py --info your_file.txt
```

## 更新日志

### v2.0 (当前版本)
- ✅ 新增批量文件处理功能
- ✅ 增强的数据验证和错误处理
- ✅ 多种分析模板支持
- ✅ 改进的用户界面和命令行工具
- ✅ 综合HTML报告生成
- ✅ JSON数据导出功能
- ✅ 可配置的分析参数

### v1.0 (原始版本)
- ✅ 基础UWB数据解析
- ✅ 简单的HTML表格生成
- ✅ 基础距离图表绘制

## 贡献

欢迎提交问题报告和功能请求。如果您想贡献代码，请：

1. Fork 本项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 项目讨论区

---

**注意**：本工具集专为UWB定位系统数据分析设计，请根据实际数据格式调整配置参数。
