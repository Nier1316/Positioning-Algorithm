# UWB数据卡尔曼滤波分析工具

## 概述

本工具为UWB（Ultra-Wideband）测距数据提供了完整的卡尔曼滤波分析功能，能够有效减少测量噪声并提高数据质量。

## 功能特性

### 🔍 卡尔曼滤波算法
- **标准卡尔曼滤波**：适用于一般噪声环境
- **自适应滤波**：根据数据特性自动调整参数
- **多滤波器对比**：同时测试多种滤波器效果
- **最优选择**：自动选择噪声减少效果最好的滤波器

### 📊 数据分析功能
- **噪声减少分析**：计算滤波前后的噪声减少百分比
- **统计对比**：对比原始数据和滤波后数据的统计特性
- **可视化分析**：生成详细的对比图表
- **批量处理**：支持同时处理多个数据文件

### 📋 报告生成
- **HTML综合报告**：包含完整的分析结果和可视化图表
- **JSON数据导出**：便于程序化处理和二次开发
- **高质量图表**：PNG格式的分析图表

## 文件结构

```
3_Locate/
├── uwb_kalman_analyzer.py          # 卡尔曼滤波分析器（推荐使用）
├── kalman_filter.py                # 卡尔曼滤波器实现
├── uwb_analyzer_enhanced.py        # 增强版分析器（包含卡尔曼滤波）
├── kalman_output/                  # 分析结果输出目录
│   ├── kalman_analysis_report.html # HTML分析报告
│   ├── kalman_analysis_data.json   # JSON数据文件
│   └── kalman_analysis.png         # 分析图表
└── KALMAN_FILTER_README.md         # 本说明文件
```

## 快速开始

### 1. 环境要求

```bash
pip install matplotlib numpy
```

### 2. 基本使用

```bash
# 使用卡尔曼滤波分析器（推荐）
python uwb_kalman_analyzer.py

# 使用增强版分析器（包含卡尔曼滤波）
python uwb_analyzer_enhanced.py
```

### 3. 输出文件

运行后会生成以下文件：

- **kalman_analysis_report.html** - 综合HTML报告
- **kalman_analysis_data.json** - JSON格式数据
- **kalman_analysis.png** - 可视化分析图表

## 卡尔曼滤波原理

### 算法概述
卡尔曼滤波是一种最优估计算法，通过结合预测和观测信息来估计系统状态。对于UWB距离数据，它能够：

1. **预测步骤**：基于历史数据预测当前状态
2. **更新步骤**：结合新的测量数据更新估计
3. **噪声减少**：有效减少测量噪声的影响

### 参数说明
- **过程噪声 (Q)**：系统模型的不确定性
- **测量噪声 (R)**：传感器测量的不确定性
- **状态协方差 (P)**：估计误差的协方差

### 滤波器类型
1. **标准滤波器**：适用于一般噪声环境
2. **平滑滤波器**：适用于高噪声环境，提供更平滑的结果
3. **响应滤波器**：适用于快速变化的环境
4. **自适应滤波器**：根据数据特性自动调整参数

## 分析结果解读

### 噪声减少百分比
- **> 50%**：滤波效果优秀
- **30-50%**：滤波效果良好
- **10-30%**：滤波效果一般
- **< 10%**：滤波效果有限

### 统计指标
- **原始标准差**：滤波前数据的离散程度
- **滤波后标准差**：滤波后数据的离散程度
- **均方误差**：滤波误差的量化指标
- **信噪比改善**：信号质量改善的量化指标

## 可视化图表说明

### 1. 原始数据 vs 滤波后数据对比
- 蓝色线：原始测量数据
- 红色线：卡尔曼滤波后的数据
- 显示滤波效果和趋势保持情况

### 2. 噪声减少效果对比
- 柱状图显示各文件的噪声减少百分比
- 数值标签显示具体的减少百分比

### 3. 数据分布对比
- 直方图对比原始数据和滤波后数据的分布
- 显示滤波对数据分布的影响

### 4. 标准差对比
- 对比各文件滤波前后的标准差
- 直观显示噪声减少效果

## 高级用法

### 1. 自定义滤波器参数

```python
from uwb_kalman_analyzer import UWBKalmanAnalyzer, KalmanFilter

# 创建自定义滤波器
kalman = KalmanFilter(
    process_noise=2.0,      # 增加过程噪声
    measurement_noise=30.0   # 减少测量噪声
)

# 应用自定义滤波器
filtered_data = kalman.filter_sequence(your_data)
```

### 2. 批量处理多个目录

```python
import os
from uwb_kalman_analyzer import UWBKalmanAnalyzer

# 批量处理多个目录
for directory in ['data1', 'data2', 'data3']:
    analyzer = UWBKalmanAnalyzer()
    analyzer.run_analysis(
        file_pattern=f"{directory}/*.txt",
        output_dir=f"results/{directory}"
    )
```

### 3. 程序化调用

```python
from uwb_kalman_analyzer import UWBKalmanAnalyzer

# 创建分析器
analyzer = UWBKalmanAnalyzer()

# 解析文件
analyzer.parse_file("your_data.txt")

# 应用卡尔曼滤波
kalman_results = analyzer.apply_kalman_filtering()

# 获取结果
for file_path, result in kalman_results.items():
    print(f"文件: {file_path}")
    print(f"噪声减少: {result['statistics']['noise_reduction_percent']:.2f}%")
```

## 故障排除

### 常见问题

1. **没有找到UWB数据包**
   - 检查数据文件格式是否正确
   - 确认文件包含DD 66开头、AA BB结尾的数据包

2. **滤波效果不明显**
   - 尝试调整滤波器参数
   - 检查数据是否已经比较平滑

3. **图表生成失败**
   - 确保安装了matplotlib
   - 检查中文字体支持

4. **内存不足**
   - 减少同时处理的文件数量
   - 分批处理大量数据

### 调试技巧

```python
# 启用详细输出
analyzer = UWBKalmanAnalyzer()
analyzer.parse_file("your_file.txt")
print(f"找到 {len(analyzer.uwb_packets)} 个数据包")

# 检查数据质量
distances = [p.distance for p in analyzer.uwb_packets]
print(f"距离范围: {min(distances)} - {max(distances)}")
print(f"标准差: {np.std(distances):.2f}")
```

## 性能优化

### 1. 大数据集处理
- 使用分批处理
- 调整滤波器参数以减少计算量
- 考虑使用自适应滤波器

### 2. 实时处理
- 使用增量更新算法
- 优化滤波器初始化
- 减少不必要的计算

## 更新日志

### v1.0 (当前版本)
- ✅ 实现标准卡尔曼滤波器
- ✅ 支持多种滤波器类型
- ✅ 生成综合HTML报告
- ✅ 提供可视化分析图表
- ✅ 支持批量文件处理
- ✅ JSON数据导出功能

## 技术细节

### 卡尔曼滤波方程

**预测步骤：**
```
x_k|k-1 = F * x_k-1|k-1
P_k|k-1 = F * P_k-1|k-1 * F^T + Q
```

**更新步骤：**
```
K_k = P_k|k-1 * H^T / (H * P_k|k-1 * H^T + R)
x_k|k = x_k|k-1 + K_k * (z_k - H * x_k|k-1)
P_k|k = (I - K_k * H) * P_k|k-1
```

其中：
- `x`：状态估计
- `P`：状态协方差
- `F`：状态转移矩阵
- `H`：观测矩阵
- `Q`：过程噪声协方差
- `R`：测量噪声协方差
- `K`：卡尔曼增益
- `z`：测量值

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 项目讨论区

---

**注意**：本工具专为UWB定位系统数据分析设计，请根据实际数据格式调整参数。
