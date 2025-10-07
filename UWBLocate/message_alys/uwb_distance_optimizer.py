#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB距离数据优化程序
对相同距离下的多次测量数据进行优化计算，得到最优距离值
"""

import os
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import statistics

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 宏定义：数据文件相对路径
LOCATION = "1.2b.txt"

@dataclass
class UWBPacket:
    """UWB测距数据包结构体"""
    header: bytes  # DD 66 (2字节)
    host_id: int   # 主机ID (4字节)
    slave_id: int  # 从机ID (4字节)
    distance: int  # 测距数据 (2字节)
    tail: bytes    # AA BB (2字节)
    
    def __str__(self):
        return f"UWB: Host={self.host_id:08X}, Slave={self.slave_id:08X}, Distance={self.distance}"

@dataclass
class OptimizationResult:
    """优化结果数据类"""
    method: str
    optimized_value: float
    confidence: float
    error_margin: float
    sample_count: int
    statistics: Dict[str, float]

class UWBDistanceOptimizer:
    """UWB距离数据优化器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.uwb_packets: List[UWBPacket] = []
        self.distances: List[int] = []
        self.optimization_results: List[OptimizationResult] = []
        
    def read_hex_file(self) -> bytes:
        """读取十六进制文件并转换为字节数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 移除空格和换行符
            hex_string = content.replace(' ', '').replace('\n', '')
            
            # 将十六进制字符串转换为字节
            return bytes.fromhex(hex_string)
        except FileNotFoundError:
            print(f"错误：找不到文件 {self.file_path}")
            return b''
        except Exception as e:
            print(f"错误：读取文件时发生异常 - {e}")
            return b''
    
    def find_uwb_packet(self, data: bytes, start_pos: int) -> Optional[Tuple[UWBPacket, int]]:
        """查找UWB测距数据包"""
        # 查找DD 66开头的数据包
        for i in range(start_pos, len(data) - 11):  # 至少需要12字节
            if data[i] == 0xDD and data[i+1] == 0x66:
                # 查找AA BB结尾
                for j in range(i + 2, len(data) - 1):
                    if data[j] == 0xAA and data[j+1] == 0xBB:
                        # 解析UWB数据包
                        try:
                            host_id = struct.unpack('>I', data[i+2:i+6])[0]  # 大端序4字节
                            slave_id = struct.unpack('>I', data[i+6:i+10])[0]  # 大端序4字节
                            distance = struct.unpack('>H', data[i+10:i+12])[0]  # 大端序2字节
                            
                            packet = UWBPacket(
                                header=data[i:i+2],
                                host_id=host_id,
                                slave_id=slave_id,
                                distance=distance,
                                tail=data[j:j+2]
                            )
                            return packet, j + 2
                        except struct.error:
                            continue
        return None
    
    def parse_data(self):
        """解析UWB数据包并提取距离信息"""
        print("开始解析距离数据...")
        data = self.read_hex_file()
        if not data:
            return
        
        pos = 0
        packet_count = 0
        
        while pos < len(data):
            # 查找UWB数据包
            uwb_result = self.find_uwb_packet(data, pos)
            if uwb_result:
                uwb_packet, new_pos = uwb_result
                self.uwb_packets.append(uwb_packet)
                self.distances.append(uwb_packet.distance)
                pos = new_pos
                packet_count += 1
                
                if packet_count <= 5:  # 只显示前5个数据包
                    print(f"找到UWB数据包 {packet_count}: 距离={uwb_packet.distance}")
                elif packet_count == 6:
                    print("...")
                continue
            
            # 如果没找到UWB数据包，继续搜索
            pos += 1
        
        print(f"\n解析完成！")
        print(f"UWB数据包数量: {len(self.uwb_packets)}")
        print(f"距离数据范围: {min(self.distances)} - {max(self.distances)}")
    
    def calculate_statistics(self) -> Dict[str, float]:
        """计算距离数据的统计信息"""
        if not self.distances:
            return {}
        
        distances_array = np.array(self.distances)
        
        stats = {
            'mean': np.mean(distances_array),
            'median': np.median(distances_array),
            'mode': statistics.mode(self.distances) if len(set(self.distances)) < len(self.distances) else np.mean(distances_array),
            'std': np.std(distances_array),
            'variance': np.var(distances_array),
            'min': np.min(distances_array),
            'max': np.max(distances_array),
            'range': np.max(distances_array) - np.min(distances_array),
            'q1': np.percentile(distances_array, 25),
            'q3': np.percentile(distances_array, 75),
            'iqr': np.percentile(distances_array, 75) - np.percentile(distances_array, 25),
            'skewness': self._calculate_skewness(distances_array),
            'kurtosis': self._calculate_kurtosis(distances_array)
        }
        
        return stats
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """计算偏度"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 3)
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """计算峰度"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 4) - 3
    
    def optimize_arithmetic_mean(self) -> OptimizationResult:
        """算术平均值优化"""
        if not self.distances:
            return None
        
        optimized_value = np.mean(self.distances)
        std_dev = np.std(self.distances)
        confidence = 1.0 / (1.0 + std_dev / optimized_value) if optimized_value > 0 else 0
        error_margin = 1.96 * std_dev / np.sqrt(len(self.distances))  # 95%置信区间
        
        return OptimizationResult(
            method="算术平均值",
            optimized_value=optimized_value,
            confidence=confidence,
            error_margin=error_margin,
            sample_count=len(self.distances),
            statistics=self.calculate_statistics()
        )
    
    def optimize_median(self) -> OptimizationResult:
        """中位数优化"""
        if not self.distances:
            return None
        
        optimized_value = np.median(self.distances)
        mad = np.median(np.abs(self.distances - optimized_value))  # 中位数绝对偏差
        confidence = 1.0 / (1.0 + mad / optimized_value) if optimized_value > 0 else 0
        error_margin = 1.4826 * mad  # 基于MAD的误差估计
        
        return OptimizationResult(
            method="中位数",
            optimized_value=optimized_value,
            confidence=confidence,
            error_margin=error_margin,
            sample_count=len(self.distances),
            statistics=self.calculate_statistics()
        )
    
    def optimize_weighted_mean(self) -> OptimizationResult:
        """加权平均值优化（基于频率）"""
        if not self.distances:
            return None
        
        # 计算每个值的频率作为权重
        from collections import Counter
        counter = Counter(self.distances)
        total_count = len(self.distances)
        
        weighted_sum = sum(value * count for value, count in counter.items())
        total_weight = sum(counter.values())
        
        optimized_value = weighted_sum / total_weight if total_weight > 0 else 0
        
        # 计算加权标准差
        weighted_variance = sum(count * (value - optimized_value) ** 2 for value, count in counter.items()) / total_weight
        weighted_std = np.sqrt(weighted_variance)
        
        confidence = 1.0 / (1.0 + weighted_std / optimized_value) if optimized_value > 0 else 0
        error_margin = 1.96 * weighted_std / np.sqrt(total_weight)
        
        return OptimizationResult(
            method="加权平均值",
            optimized_value=optimized_value,
            confidence=confidence,
            error_margin=error_margin,
            sample_count=len(self.distances),
            statistics=self.calculate_statistics()
        )
    
    def optimize_robust_mean(self) -> OptimizationResult:
        """鲁棒平均值优化（去除异常值）"""
        if not self.distances:
            return None
        
        distances_array = np.array(self.distances)
        q1 = np.percentile(distances_array, 25)
        q3 = np.percentile(distances_array, 75)
        iqr = q3 - q1
        
        # 定义异常值范围
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # 过滤异常值
        filtered_distances = distances_array[(distances_array >= lower_bound) & (distances_array <= upper_bound)]
        
        if len(filtered_distances) == 0:
            filtered_distances = distances_array
        
        optimized_value = np.mean(filtered_distances)
        std_dev = np.std(filtered_distances)
        confidence = 1.0 / (1.0 + std_dev / optimized_value) if optimized_value > 0 else 0
        error_margin = 1.96 * std_dev / np.sqrt(len(filtered_distances))
        
        return OptimizationResult(
            method="鲁棒平均值",
            optimized_value=optimized_value,
            confidence=confidence,
            error_margin=error_margin,
            sample_count=len(filtered_distances),
            statistics=self.calculate_statistics()
        )
    
    def optimize_moving_average(self, window_size: int = 5) -> OptimizationResult:
        """移动平均值优化"""
        if not self.distances or len(self.distances) < window_size:
            return None
        
        # 计算移动平均值
        moving_averages = []
        for i in range(len(self.distances) - window_size + 1):
            window = self.distances[i:i + window_size]
            moving_averages.append(np.mean(window))
        
        optimized_value = np.mean(moving_averages)
        std_dev = np.std(moving_averages)
        confidence = 1.0 / (1.0 + std_dev / optimized_value) if optimized_value > 0 else 0
        error_margin = 1.96 * std_dev / np.sqrt(len(moving_averages))
        
        return OptimizationResult(
            method=f"移动平均值(窗口={window_size})",
            optimized_value=optimized_value,
            confidence=confidence,
            error_margin=error_margin,
            sample_count=len(moving_averages),
            statistics=self.calculate_statistics()
        )
    
    def optimize_kalman_filter(self) -> OptimizationResult:
        """卡尔曼滤波优化"""
        if not self.distances:
            return None
        
        # 简化的卡尔曼滤波实现
        distances_array = np.array(self.distances)
        
        # 初始状态
        x = distances_array[0]  # 初始估计
        P = 1.0  # 初始协方差
        Q = 0.1  # 过程噪声
        R = np.var(distances_array)  # 测量噪声
        
        filtered_values = [x]
        
        for measurement in distances_array[1:]:
            # 预测步骤
            x_pred = x
            P_pred = P + Q
            
            # 更新步骤
            K = P_pred / (P_pred + R)  # 卡尔曼增益
            x = x_pred + K * (measurement - x_pred)
            P = (1 - K) * P_pred
            
            filtered_values.append(x)
        
        optimized_value = x  # 最终估计值
        confidence = 1.0 / (1.0 + np.sqrt(P) / optimized_value) if optimized_value > 0 else 0
        error_margin = 1.96 * np.sqrt(P)
        
        return OptimizationResult(
            method="卡尔曼滤波",
            optimized_value=optimized_value,
            confidence=confidence,
            error_margin=error_margin,
            sample_count=len(self.distances),
            statistics=self.calculate_statistics()
        )
    
    def run_all_optimizations(self):
        """运行所有优化算法"""
        print("开始运行距离数据优化算法...")
        
        optimizations = [
            self.optimize_arithmetic_mean,
            self.optimize_median,
            self.optimize_weighted_mean,
            self.optimize_robust_mean,
            self.optimize_moving_average,
            self.optimize_kalman_filter
        ]
        
        for optimization_func in optimizations:
            try:
                result = optimization_func()
                if result:
                    self.optimization_results.append(result)
                    print(f"OK {result.method}: {result.optimized_value:.2f} ± {result.error_margin:.2f}")
            except Exception as e:
                print(f"ERROR 优化算法执行失败: {e}")
        
        print(f"\n完成 {len(self.optimization_results)} 种优化算法")
    
    def find_best_optimization(self) -> OptimizationResult:
        """找到最佳优化结果"""
        if not self.optimization_results:
            return None
        
        # 基于置信度和误差范围选择最佳结果
        best_result = max(self.optimization_results, 
                         key=lambda x: x.confidence / (1 + x.error_margin / x.optimized_value))
        
        return best_result
    
    def plot_optimization_results(self, output_file: str = "optimization_results.png"):
        """绘制优化结果图表"""
        if not self.optimization_results:
            print("没有优化结果可绘制")
            return
        
        print("绘制优化结果图表...")
        
        # 创建图形和子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 准备数据
        methods = [result.method for result in self.optimization_results]
        values = [result.optimized_value for result in self.optimization_results]
        confidences = [result.confidence for result in self.optimization_results]
        error_margins = [result.error_margin for result in self.optimization_results]
        
        # 1. 优化值对比
        bars1 = ax1.bar(range(len(methods)), values, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_title('各优化算法的距离值', fontsize=14, fontweight='bold')
        ax1.set_xlabel('优化算法')
        ax1.set_ylabel('距离值')
        ax1.set_xticks(range(len(methods)))
        ax1.set_xticklabels(methods, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, (bar, value) in enumerate(zip(bars1, values)):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}', ha='center', va='bottom', fontsize=10)
        
        # 2. 置信度对比
        bars2 = ax2.bar(range(len(methods)), confidences, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_title('各优化算法的置信度', fontsize=14, fontweight='bold')
        ax2.set_xlabel('优化算法')
        ax2.set_ylabel('置信度')
        ax2.set_xticks(range(len(methods)))
        ax2.set_xticklabels(methods, rotation=45, ha='right')
        ax2.set_ylim(0, 1)
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, (bar, conf) in enumerate(zip(bars2, confidences)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{conf:.3f}', ha='center', va='bottom', fontsize=10)
        
        # 3. 误差范围对比
        bars3 = ax3.bar(range(len(methods)), error_margins, alpha=0.7, color='lightcoral', edgecolor='black')
        ax3.set_title('各优化算法的误差范围', fontsize=14, fontweight='bold')
        ax3.set_xlabel('优化算法')
        ax3.set_ylabel('误差范围')
        ax3.set_xticks(range(len(methods)))
        ax3.set_xticklabels(methods, rotation=45, ha='right')
        ax3.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, (bar, error) in enumerate(zip(bars3, error_margins)):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{error:.1f}', ha='center', va='bottom', fontsize=10)
        
        # 4. 原始数据分布和优化结果
        ax4.hist(self.distances, bins=30, alpha=0.7, color='lightblue', edgecolor='black', label='原始数据')
        
        # 标记各优化结果
        colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown']
        for i, (result, color) in enumerate(zip(self.optimization_results, colors)):
            ax4.axvline(result.optimized_value, color=color, linestyle='--', linewidth=2, 
                       label=f'{result.method}: {result.optimized_value:.1f}')
        
        ax4.set_title('原始数据分布与优化结果对比', fontsize=14, fontweight='bold')
        ax4.set_xlabel('距离值')
        ax4.set_ylabel('频次')
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"OK 优化结果图表已保存: {output_file}")
        
        # 关闭图形以释放内存
        plt.close()
        
        return output_file
    
    def generate_optimization_report(self, output_file: str = "optimization_report.html"):
        """生成优化报告"""
        print("生成优化报告...")
        
        best_result = self.find_best_optimization()
        stats = self.calculate_statistics()
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>UWB距离数据优化报告</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                h2 {{
                    color: #555;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                }}
                .summary {{
                    display: flex;
                    justify-content: space-around;
                    margin: 20px 0;
                }}
                .summary-item {{
                    text-align: center;
                    padding: 15px;
                    background-color: #e9ecef;
                    border-radius: 5px;
                    min-width: 150px;
                }}
                .summary-number {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #007bff;
                }}
                .summary-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .best-result {{
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 12px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                }}
                th {{
                    background-color: #007bff;
                    color: white;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                tr:hover {{
                    background-color: #e6f3ff;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 15px;
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #007bff;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>UWB距离数据优化报告</h1>
                
                <div class="summary">
                    <div class="summary-item">
                        <div class="summary-number">{len(self.distances)}</div>
                        <div class="summary-label">测量次数</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number">{len(self.optimization_results)}</div>
                        <div class="summary-label">优化算法</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number">{datetime.now().strftime("%H:%M:%S")}</div>
                        <div class="summary-label">分析时间</div>
                    </div>
                </div>
                
                {f'''
                <div class="best-result">
                    <h3>🏆 最佳优化结果</h3>
                    <p><strong>算法:</strong> {best_result.method}</p>
                    <p><strong>优化距离值:</strong> {best_result.optimized_value:.2f}</p>
                    <p><strong>置信度:</strong> {best_result.confidence:.3f}</p>
                    <p><strong>误差范围:</strong> ±{best_result.error_margin:.2f}</p>
                    <p><strong>样本数量:</strong> {best_result.sample_count}</p>
                </div>
                ''' if best_result else ''}
                
                <h2>优化算法结果对比</h2>
                <table>
                    <thead>
                        <tr>
                            <th>算法</th>
                            <th>优化值</th>
                            <th>置信度</th>
                            <th>误差范围</th>
                            <th>样本数</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # 添加优化结果
        for result in self.optimization_results:
            html_content += f"""
                        <tr>
                            <td>{result.method}</td>
                            <td>{result.optimized_value:.2f}</td>
                            <td>{result.confidence:.3f}</td>
                            <td>±{result.error_margin:.2f}</td>
                            <td>{result.sample_count}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
                
                <h2>原始数据统计信息</h2>
                <div class="stats-grid">
        """
        
        # 添加统计信息
        for key, value in stats.items():
            html_content += f"""
                    <div class="stat-card">
                        <div class="stat-value">{value:.2f}</div>
                        <div class="stat-label">{key}</div>
                    </div>
            """
        
        html_content += f"""
                </div>
                
                <h2>数据分布信息</h2>
                <table>
                    <thead>
                        <tr>
                            <th>统计量</th>
                            <th>数值</th>
                            <th>说明</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>数据范围</td>
                            <td>{stats.get('min', 0):.0f} - {stats.get('max', 0):.0f}</td>
                            <td>最小值和最大值</td>
                        </tr>
                        <tr>
                            <td>四分位距</td>
                            <td>{stats.get('iqr', 0):.2f}</td>
                            <td>Q3 - Q1</td>
                        </tr>
                        <tr>
                            <td>偏度</td>
                            <td>{stats.get('skewness', 0):.3f}</td>
                            <td>数据分布对称性</td>
                        </tr>
                        <tr>
                            <td>峰度</td>
                            <td>{stats.get('kurtosis', 0):.3f}</td>
                            <td>数据分布尖锐度</td>
                        </tr>
                    </tbody>
                </table>
                
                <p style="text-align: center; color: #666; margin-top: 30px;">
                    共分析 {len(self.distances)} 个距离测量值，使用 {len(self.optimization_results)} 种优化算法
                </p>
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"OK 优化报告已生成: {output_file}")
        return output_file
    
    def run_optimization_analysis(self):
        """运行完整的优化分析流程"""
        print("UWB距离数据优化分析程序")
        print("=" * 50)
        
        # 检查文件是否存在
        if not os.path.exists(self.file_path):
            print(f"错误：文件 {self.file_path} 不存在")
            return
        
        try:
            # 1. 解析数据
            self.parse_data()
            
            if not self.distances:
                print("未找到任何距离数据")
                return
            
            # 2. 运行所有优化算法
            self.run_all_optimizations()
            
            # 3. 找到最佳结果
            best_result = self.find_best_optimization()
            if best_result:
                print(f"\n最佳优化结果:")
                print(f"   算法: {best_result.method}")
                print(f"   距离值: {best_result.optimized_value:.2f}")
                print(f"   置信度: {best_result.confidence:.3f}")
                print(f"   误差范围: ±{best_result.error_margin:.2f}")
            
            # 4. 生成图表
            chart_file = self.plot_optimization_results()
            
            # 5. 生成报告
            report_file = self.generate_optimization_report()
            
            print("\n" + "=" * 50)
            print("优化分析完成！生成的文件：")
            print(f"优化结果图表: {chart_file}")
            print(f"优化分析报告: {report_file}")
            print("\n使用方法：")
            print("- 双击HTML文件用浏览器打开查看详细报告")
            print("- 查看PNG图片了解各算法对比结果")
            
        except Exception as e:
            print(f"优化分析过程中发生错误: {e}")

def main():
    """主函数"""
    optimizer = UWBDistanceOptimizer(LOCATION)
    optimizer.run_optimization_analysis()

if __name__ == "__main__":
    main()
