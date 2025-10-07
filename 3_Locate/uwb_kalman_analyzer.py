#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB数据卡尔曼滤波分析器
集成卡尔曼滤波功能的UWB数据分析工具
"""

import os
import struct
import glob
import json
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

@dataclass
class UWBPacket:
    """UWB测距数据包结构体"""
    header: bytes
    host_id: int
    slave_id: int
    distance: int
    tail: bytes
    source_file: str = ""
    
    def __str__(self):
        return f"UWB: Host={self.host_id:08X}, Slave={self.slave_id:08X}, Distance={self.distance}"

class KalmanFilter:
    """简化的卡尔曼滤波器"""
    
    def __init__(self, process_noise=1.0, measurement_noise=50.0):
        self.Q = process_noise  # 过程噪声
        self.R = measurement_noise  # 测量噪声
        self.x = 0.0  # 状态估计
        self.P = 100.0  # 状态协方差
        self.filtered_values = []
    
    def filter_sequence(self, measurements: List[float]) -> List[float]:
        """对测量序列进行滤波"""
        self.filtered_values = []
        
        for z in measurements:
            # 预测步骤
            self.P = self.P + self.Q
            
            # 更新步骤
            K = self.P / (self.P + self.R)  # 卡尔曼增益
            self.x = self.x + K * (z - self.x)
            self.P = (1 - K) * self.P
            
            self.filtered_values.append(self.x)
        
        return self.filtered_values

class UWBKalmanAnalyzer:
    """UWB卡尔曼滤波分析器"""
    
    def __init__(self):
        self.uwb_packets: List[UWBPacket] = []
        self.file_stats: Dict[str, Any] = {}
        self.kalman_results: Dict[str, Any] = {}
    
    def read_hex_file(self, file_path: str) -> bytes:
        """读取十六进制文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            hex_string = content.replace(' ', '').replace('\n', '')
            return bytes.fromhex(hex_string)
        except Exception as e:
            print(f"读取文件错误: {e}")
            return b''
    
    def find_uwb_packets(self, data: bytes, source_file: str) -> List[UWBPacket]:
        """查找UWB数据包"""
        packets = []
        pos = 0
        
        while pos < len(data) - 11:
            if data[pos] == 0xDD and data[pos+1] == 0x66:
                # 查找AA BB结尾
                for j in range(pos + 2, len(data) - 1):
                    if data[j] == 0xAA and data[j+1] == 0xBB:
                        try:
                            host_id = struct.unpack('>I', data[pos+2:pos+6])[0]
                            slave_id = struct.unpack('>I', data[pos+6:pos+10])[0]
                            distance = struct.unpack('>H', data[pos+10:pos+12])[0]
                            
                            packet = UWBPacket(
                                header=data[pos:pos+2],
                                host_id=host_id,
                                slave_id=slave_id,
                                distance=distance,
                                tail=data[j:j+2],
                                source_file=source_file
                            )
                            packets.append(packet)
                            pos = j + 2
                            break
                        except struct.error:
                            break
            pos += 1
        
        return packets
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析单个文件"""
        print(f"解析文件: {os.path.basename(file_path)}")
        
        data = self.read_hex_file(file_path)
        if not data:
            return {'error': '无法读取文件'}
        
        packets = self.find_uwb_packets(data, file_path)
        self.uwb_packets.extend(packets)
        
        if packets:
            distances = [p.distance for p in packets]
            stats = {
                'file_path': file_path,
                'packet_count': len(packets),
                'distance_stats': {
                    'min': min(distances),
                    'max': max(distances),
                    'avg': sum(distances) / len(distances),
                    'std': np.std(distances)
                }
            }
            self.file_stats[file_path] = stats
            print(f"  ✓ 找到 {len(packets)} 个UWB数据包")
            print(f"  ✓ 距离范围: {min(distances)} - {max(distances)}")
            return stats
        else:
            print(f"  ❌ 未找到UWB数据包")
            return {'error': '未找到数据包'}
    
    def apply_kalman_filtering(self):
        """应用卡尔曼滤波"""
        print("\n应用卡尔曼滤波...")
        
        if not self.uwb_packets:
            print("没有UWB数据包可处理")
            return {}
        
        # 按文件分组处理
        file_distances = {}
        for packet in self.uwb_packets:
            if packet.source_file not in file_distances:
                file_distances[packet.source_file] = []
            file_distances[packet.source_file].append(packet.distance)
        
        # 对每个文件应用卡尔曼滤波
        for file_path, distances in file_distances.items():
            if len(distances) > 1:
                print(f"  处理 {os.path.basename(file_path)}: {len(distances)} 个数据点")
                
                # 创建卡尔曼滤波器
                kalman = KalmanFilter(process_noise=1.0, measurement_noise=50.0)
                filtered_distances = kalman.filter_sequence([float(d) for d in distances])
                
                # 计算统计信息
                raw_std = np.std(distances)
                filtered_std = np.std(filtered_distances)
                noise_reduction = (raw_std - filtered_std) / raw_std * 100
                
                result = {
                    'file_path': file_path,
                    'raw_distances': distances,
                    'filtered_distances': [round(d, 2) for d in filtered_distances],
                    'statistics': {
                        'raw_std': raw_std,
                        'filtered_std': filtered_std,
                        'noise_reduction_percent': noise_reduction,
                        'data_points': len(distances)
                    }
                }
                
                self.kalman_results[file_path] = result
                print(f"    ✓ 噪声减少: {noise_reduction:.2f}%")
        
        print(f"✓ 卡尔曼滤波完成，处理了 {len(self.kalman_results)} 个文件")
        return self.kalman_results
    
    def generate_kalman_charts(self, output_dir: str = ".") -> str:
        """生成卡尔曼滤波图表"""
        if not self.kalman_results:
            return ""
        
        print("生成卡尔曼滤波图表...")
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('UWB距离数据卡尔曼滤波分析', fontsize=16, fontweight='bold')
        
        # 选择第一个文件的数据进行展示
        first_file = list(self.kalman_results.keys())[0]
        result = self.kalman_results[first_file]
        
        distances = result['raw_distances']
        filtered = result['filtered_distances']
        x_values = list(range(len(distances)))
        
        # 1. 原始数据 vs 滤波后数据
        ax1 = axes[0, 0]
        ax1.plot(x_values, distances, 'b-', alpha=0.7, label='原始数据', linewidth=1)
        ax1.plot(x_values, filtered, 'r-', label='卡尔曼滤波', linewidth=2)
        ax1.set_title(f'原始数据 vs 滤波后数据\n({os.path.basename(first_file)})')
        ax1.set_xlabel('数据点序号')
        ax1.set_ylabel('距离值')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 噪声减少效果对比
        ax2 = axes[0, 1]
        file_names = []
        noise_reductions = []
        
        for file_path, result in self.kalman_results.items():
            file_names.append(os.path.basename(file_path))
            noise_reductions.append(result['statistics']['noise_reduction_percent'])
        
        bars = ax2.bar(file_names, noise_reductions, color='skyblue', alpha=0.7)
        ax2.set_title('各文件噪声减少效果')
        ax2.set_xlabel('文件')
        ax2.set_ylabel('噪声减少 (%)')
        ax2.grid(True, alpha=0.3)
        
        # 在柱状图上添加数值标签
        for bar, value in zip(bars, noise_reductions):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{value:.1f}%', ha='center', va='bottom')
        
        # 3. 数据分布对比
        ax3 = axes[1, 0]
        ax3.hist(distances, bins=20, alpha=0.5, label='原始数据', color='blue')
        ax3.hist(filtered, bins=20, alpha=0.5, label='滤波后数据', color='red')
        ax3.set_title('数据分布对比')
        ax3.set_xlabel('距离值')
        ax3.set_ylabel('频次')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 滤波效果统计
        ax4 = axes[1, 1]
        stats_data = []
        stats_labels = []
        
        for file_path, result in self.kalman_results.items():
            stats = result['statistics']
            stats_data.extend([stats['raw_std'], stats['filtered_std']])
            stats_labels.extend([f'{os.path.basename(file_path)}\n原始', 
                               f'{os.path.basename(file_path)}\n滤波'])
        
        bars = ax4.bar(range(len(stats_data)), stats_data, 
                      color=['lightblue', 'lightcoral'] * len(self.kalman_results), alpha=0.7)
        ax4.set_title('标准差对比')
        ax4.set_xlabel('文件')
        ax4.set_ylabel('标准差')
        ax4.set_xticks(range(len(stats_labels)))
        ax4.set_xticklabels(stats_labels, rotation=45, ha='right')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        chart_file = os.path.join(output_dir, "kalman_analysis.png")
        plt.savefig(chart_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✓ 图表已保存: {chart_file}")
        return chart_file
    
    def generate_html_report(self, output_file: str):
        """生成HTML报告"""
        print("生成HTML报告...")
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>UWB数据卡尔曼滤波分析报告</title>
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
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .stat-label {{
                    font-size: 0.9em;
                    opacity: 0.9;
                }}
                .kalman-section {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #28a745;
                }}
                .file-section {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                }}
                th {{
                    background-color: #007bff;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .chart-container {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>UWB数据卡尔曼滤波分析报告</h1>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{len(self.uwb_packets)}</div>
                        <div class="stat-label">UWB数据包总数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(self.file_stats)}</div>
                        <div class="stat-label">分析文件数量</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(self.kalman_results)}</div>
                        <div class="stat-label">滤波处理文件</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{datetime.now().strftime("%H:%M:%S")}</div>
                        <div class="stat-label">生成时间</div>
                    </div>
                </div>
        """
        
        # 添加卡尔曼滤波结果
        if self.kalman_results:
            html_content += """
                <div class="kalman-section">
                    <h2>卡尔曼滤波分析结果</h2>
                    <p>卡尔曼滤波是一种最优估计算法，用于减少测量噪声并提高数据质量。</p>
            """
            
            for file_path, result in self.kalman_results.items():
                stats = result['statistics']
                html_content += f"""
                    <div class="file-section">
                        <h3>文件: {os.path.basename(file_path)}</h3>
                        <p><strong>数据点数量:</strong> {stats['data_points']}</p>
                        <p><strong>原始数据标准差:</strong> {stats['raw_std']:.2f}</p>
                        <p><strong>滤波后标准差:</strong> {stats['filtered_std']:.2f}</p>
                        <p><strong>噪声减少:</strong> {stats['noise_reduction_percent']:.2f}%</p>
                    </div>
                """
            
            html_content += """
                </div>
            """
        
        # 添加图表
        if self.kalman_results:
            html_content += """
                <div class="chart-container">
                    <h2>卡尔曼滤波可视化分析</h2>
                    <img src="kalman_analysis.png" alt="卡尔曼滤波分析图表">
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML报告已生成: {output_file}")
    
    def run_analysis(self, file_pattern: str = "*.txt", output_dir: str = "kalman_output"):
        """运行完整分析"""
        print("UWB数据卡尔曼滤波分析程序")
        print("=" * 50)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 查找文件
        files = glob.glob(file_pattern)
        if not files:
            print(f"未找到匹配模式 '{file_pattern}' 的文件")
            return
        
        print(f"找到 {len(files)} 个文件:")
        for file in files:
            print(f"  - {file}")
        print()
        
        # 解析文件
        for file_path in files:
            self.parse_file(file_path)
        
        if not self.uwb_packets:
            print("未找到任何UWB数据包")
            return
        
        # 应用卡尔曼滤波
        self.apply_kalman_filtering()
        
        # 生成图表
        chart_file = self.generate_kalman_charts(output_dir)
        
        # 生成HTML报告
        html_file = os.path.join(output_dir, "kalman_analysis_report.html")
        self.generate_html_report(html_file)
        
        # 生成JSON数据
        json_file = os.path.join(output_dir, "kalman_analysis_data.json")
        data = {
            'analysis_time': datetime.now().isoformat(),
            'summary': {
                'total_uwb_packets': len(self.uwb_packets),
                'files_analyzed': len(self.file_stats),
                'files_filtered': len(self.kalman_results)
            },
            'file_stats': self.file_stats,
            'kalman_results': self.kalman_results
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON数据已生成: {json_file}")
        
        print("\n" + "=" * 50)
        print("分析完成！生成的文件：")
        print(f"📊 HTML报告: {html_file}")
        print(f"📄 JSON数据: {json_file}")
        if chart_file:
            print(f"📈 分析图表: {chart_file}")
        
        print("\n使用方法：")
        print("• 双击HTML文件用浏览器打开查看分析报告")
        print("• 查看PNG文件了解数据可视化结果")
        print("• 查看JSON文件获取原始数据")

def main():
    """主函数"""
    analyzer = UWBKalmanAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
