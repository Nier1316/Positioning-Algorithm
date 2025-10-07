#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版UWB测距数据和加速度数据解析分析程序
支持批量处理多个文件，提供更全面的数据分析功能
"""

import os
import struct
import glob
import json
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from kalman_filter import UWBKalmanProcessor

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

@dataclass
class UWBPacket:
    """UWB测距数据包结构体"""
    header: bytes  # DD 66 (2字节)
    host_id: int   # 主机ID (4字节)
    slave_id: int  # 从机ID (4字节)
    distance: int  # 测距数据 (2字节)
    tail: bytes    # AA BB (2字节)
    timestamp: float = 0.0  # 时间戳
    
    def __str__(self):
        return f"UWB: Host={self.host_id:08X}, Slave={self.slave_id:08X}, Distance={self.distance}"
    
    def to_dict(self):
        return {
            'header': self.header.hex().upper(),
            'host_id': f"0x{self.host_id:08X}",
            'slave_id': f"0x{self.slave_id:08X}",
            'distance': self.distance,
            'tail': self.tail.hex().upper(),
            'timestamp': self.timestamp
        }

@dataclass
class AccelPacket:
    """加速度数据包结构体"""
    header: bytes    # AA CC FF 1C (4字节)
    device_id: int   # 设备ID (4字节)
    x_acc: int       # X轴加速度 (2字节)
    y_acc: int       # Y轴加速度 (2字节)
    z_acc: int       # Z轴加速度 (2字节)
    x_gyro: int      # X轴陀螺仪 (2字节)
    y_gyro: int      # Y轴陀螺仪 (2字节)
    z_gyro: int      # Z轴陀螺仪 (2字节)
    altitude: int    # 高度 (4字节)
    tail: bytes      # 包尾 (2字节)
    crc16: int       # CRC16校验码 (2字节)
    timestamp: float = 0.0  # 时间戳
    
    def __str__(self):
        return f"Accel: Device={self.device_id:08X}, X={self.x_acc}, Y={self.y_acc}, Z={self.z_acc}"
    
    def to_dict(self):
        return {
            'header': self.header.hex().upper(),
            'device_id': f"0x{self.device_id:08X}",
            'x_acc': self.x_acc,
            'y_acc': self.y_acc,
            'z_acc': self.z_acc,
            'x_gyro': self.x_gyro,
            'y_gyro': self.y_gyro,
            'z_gyro': self.z_gyro,
            'altitude': self.altitude,
            'tail': self.tail.hex().upper(),
            'crc16': f"0x{self.crc16:04X}",
            'timestamp': self.timestamp
        }

class EnhancedUWBAnalyzer:
    """增强版UWB数据解析分析器"""
    
    def __init__(self):
        self.uwb_packets: List[UWBPacket] = []
        self.accel_packets: List[AccelPacket] = []
        self.file_stats: Dict[str, Any] = {}
        self.kalman_processor = UWBKalmanProcessor()
        self.kalman_results: Dict[str, Any] = {}
        
    def read_hex_file(self, file_path: str) -> bytes:
        """读取十六进制文件并转换为字节数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 移除空格和换行符
            hex_string = content.replace(' ', '').replace('\n', '')
            
            # 将十六进制字符串转换为字节
            return bytes.fromhex(hex_string)
        except FileNotFoundError:
            print(f"错误：找不到文件 {file_path}")
            return b''
        except Exception as e:
            print(f"错误：读取文件 {file_path} 时发生异常 - {e}")
            return b''
    
    def find_uwb_packet(self, data: bytes, start_pos: int, source_file: str = "") -> Optional[Tuple[UWBPacket, int]]:
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
                            
                            # 数据验证
                            if distance > 65535 or distance < 0:
                                continue
                                
                            packet = UWBPacket(
                                header=data[i:i+2],
                                host_id=host_id,
                                slave_id=slave_id,
                                distance=distance,
                                tail=data[j:j+2]
                            )
                            # 添加源文件信息
                            packet.source_file = source_file
                            return packet, j + 2
                        except struct.error:
                            continue
        return None
    
    def find_accel_packet(self, data: bytes, start_pos: int) -> Optional[Tuple[AccelPacket, int]]:
        """查找加速度数据包"""
        # 查找AA CC FF 1C开头的数据包
        for i in range(start_pos, len(data) - 25):  # 至少需要26字节
            if (data[i] == 0xAA and data[i+1] == 0xCC and 
                data[i+2] == 0xFF and data[i+3] == 0x1C):
                
                # 查找DD CC结尾
                for j in range(i + 4, len(data) - 3):
                    if data[j] == 0xDD and data[j+1] == 0xCC:
                        # 解析加速度数据包
                        try:
                            device_id = struct.unpack('>I', data[i+4:i+8])[0]  # 大端序4字节
                            x_acc = struct.unpack('>h', data[i+8:i+10])[0]     # 大端序2字节有符号
                            y_acc = struct.unpack('>h', data[i+10:i+12])[0]    # 大端序2字节有符号
                            z_acc = struct.unpack('>h', data[i+12:i+14])[0]    # 大端序2字节有符号
                            x_gyro = struct.unpack('>h', data[i+14:i+16])[0]   # 大端序2字节有符号
                            y_gyro = struct.unpack('>h', data[i+16:i+18])[0]   # 大端序2字节有符号
                            z_gyro = struct.unpack('>h', data[i+18:i+20])[0]   # 大端序2字节有符号
                            altitude = struct.unpack('>I', data[i+20:i+24])[0] # 大端序4字节
                            tail = data[j:j+2]
                            crc16 = struct.unpack('>H', data[j+2:j+4])[0]      # 大端序2字节
                            
                            # 数据验证
                            if (abs(x_acc) > 32767 or abs(y_acc) > 32767 or abs(z_acc) > 32767 or
                                abs(x_gyro) > 32767 or abs(y_gyro) > 32767 or abs(z_gyro) > 32767):
                                continue
                            
                            packet = AccelPacket(
                                header=data[i:i+4],
                                device_id=device_id,
                                x_acc=x_acc,
                                y_acc=y_acc,
                                z_acc=z_acc,
                                x_gyro=x_gyro,
                                y_gyro=y_gyro,
                                z_gyro=z_gyro,
                                altitude=altitude,
                                tail=tail,
                                crc16=crc16
                            )
                            return packet, j + 4
                        except struct.error:
                            continue
        return None
    
    def parse_single_file(self, file_path: str) -> Dict[str, Any]:
        """解析单个文件"""
        print(f"正在解析文件: {file_path}")
        
        data = self.read_hex_file(file_path)
        if not data:
            return {'error': f'无法读取文件 {file_path}'}
        
        file_uwb_packets = []
        file_accel_packets = []
        
        pos = 0
        packet_count = 0
        start_time = datetime.now()
        
        while pos < len(data):
            # 查找UWB数据包
            uwb_result = self.find_uwb_packet(data, pos, file_path)
            if uwb_result:
                uwb_packet, new_pos = uwb_result
                uwb_packet.timestamp = (datetime.now() - start_time).total_seconds()
                file_uwb_packets.append(uwb_packet)
                self.uwb_packets.append(uwb_packet)
                pos = new_pos
                packet_count += 1
                
                # 检查UWB数据包后是否有加速度数据
                if pos < len(data) - 1 and data[pos] == 0xAA and data[pos+1] == 0xCC:
                    accel_result = self.find_accel_packet(data, pos)
                    if accel_result:
                        accel_packet, new_pos = accel_result
                        accel_packet.timestamp = (datetime.now() - start_time).total_seconds()
                        file_accel_packets.append(accel_packet)
                        self.accel_packets.append(accel_packet)
                        pos = new_pos
                continue
            
            # 如果没找到UWB数据包，继续搜索
            pos += 1
        
        # 计算文件统计信息
        distances = [p.distance for p in file_uwb_packets]
        file_stats = {
            'file_path': file_path,
            'uwb_count': len(file_uwb_packets),
            'accel_count': len(file_accel_packets),
            'distance_stats': {
                'min': min(distances) if distances else 0,
                'max': max(distances) if distances else 0,
                'avg': sum(distances) / len(distances) if distances else 0,
                'std': np.std(distances) if distances else 0
            } if distances else None
        }
        
        self.file_stats[file_path] = file_stats
        
        print(f"  ✓ UWB数据包: {len(file_uwb_packets)} 个")
        print(f"  ✓ 加速度数据包: {len(file_accel_packets)} 个")
        if distances:
            print(f"  ✓ 距离范围: {min(distances)} - {max(distances)}")
        
        return file_stats
    
    def parse_multiple_files(self, pattern: str = "*.txt") -> Dict[str, Any]:
        """批量解析多个文件"""
        print("开始批量解析文件...")
        print("=" * 50)
        
        # 查找匹配的文件
        files = glob.glob(pattern)
        if not files:
            print(f"未找到匹配模式 '{pattern}' 的文件")
            return {}
        
        print(f"找到 {len(files)} 个文件:")
        for file in files:
            print(f"  - {file}")
        print()
        
        # 解析每个文件
        results = {}
        for file_path in files:
            try:
                result = self.parse_single_file(file_path)
                results[file_path] = result
            except Exception as e:
                print(f"解析文件 {file_path} 时发生错误: {e}")
                results[file_path] = {'error': str(e)}
        
        return results
    
    def apply_kalman_filtering(self) -> Dict[str, Any]:
        """对所有UWB距离数据应用卡尔曼滤波"""
        print("应用卡尔曼滤波处理...")
        
        if not self.uwb_packets:
            print("没有UWB数据包可处理")
            return {}
        
        # 按文件分组处理距离数据
        file_distances = {}
        for packet in self.uwb_packets:
            # 从文件统计中找到对应的文件
            for file_path, stats in self.file_stats.items():
                if hasattr(packet, 'source_file'):
                    if packet.source_file == file_path:
                        if file_path not in file_distances:
                            file_distances[file_path] = []
                        file_distances[file_path].append(packet.distance)
                        break
        
        # 如果没有按文件分组，则处理所有数据
        if not file_distances:
            all_distances = [packet.distance for packet in self.uwb_packets]
            kalman_result = self.kalman_processor.generate_kalman_report_data(all_distances)
            self.kalman_results['all_data'] = kalman_result
            return self.kalman_results
        
        # 对每个文件的数据进行卡尔曼滤波
        for file_path, distances in file_distances.items():
            if len(distances) > 1:  # 至少需要2个数据点
                print(f"  处理文件 {os.path.basename(file_path)}: {len(distances)} 个数据点")
                kalman_result = self.kalman_processor.generate_kalman_report_data(distances)
                self.kalman_results[file_path] = kalman_result
            else:
                print(f"  跳过文件 {os.path.basename(file_path)}: 数据点太少")
        
        print(f"✓ 卡尔曼滤波处理完成，共处理 {len(self.kalman_results)} 个数据集")
        return self.kalman_results
    
    def generate_comprehensive_report(self, output_dir: str = ".") -> Dict[str, str]:
        """生成综合分析报告"""
        print("生成综合分析报告...")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成HTML报告
        html_file = os.path.join(output_dir, "comprehensive_analysis.html")
        self._generate_html_report(html_file)
        
        # 生成JSON数据
        json_file = os.path.join(output_dir, "analysis_data.json")
        self._generate_json_data(json_file)
        
        # 生成图表
        chart_files = self._generate_charts(output_dir)
        
        # 应用卡尔曼滤波
        kalman_results = self.apply_kalman_filtering()
        
        return {
            'html_report': html_file,
            'json_data': json_file,
            'charts': chart_files,
            'kalman_results': kalman_results
        }
    
    def _generate_html_report(self, output_file: str):
        """生成HTML报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>UWB数据分析综合报告</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1400px;
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
                .kalman-dataset {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .kalman-stats {{
                    display: flex;
                    justify-content: space-around;
                    margin: 15px 0;
                }}
                .kalman-table {{
                    margin: 15px 0;
                }}
                .best-filter-details {{
                    background-color: #e8f5e8;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .kalman-charts {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .kalman-charts img {{
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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
                .file-section {{
                    margin: 30px 0;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>UWB数据分析综合报告</h1>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{len(self.uwb_packets)}</div>
                        <div class="stat-label">UWB数据包总数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(self.accel_packets)}</div>
                        <div class="stat-label">加速度数据包总数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(self.file_stats)}</div>
                        <div class="stat-label">分析文件数量</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{datetime.now().strftime("%H:%M:%S")}</div>
                        <div class="stat-label">生成时间</div>
                    </div>
                </div>
        """
        
        # 添加文件统计信息
        for file_path, stats in self.file_stats.items():
            if 'error' in stats:
                continue
                
            html_content += f"""
                <div class="file-section">
                    <h2>文件: {os.path.basename(file_path)}</h2>
                    <p><strong>路径:</strong> {file_path}</p>
                    <p><strong>UWB数据包:</strong> {stats['uwb_count']} 个</p>
                    <p><strong>加速度数据包:</strong> {stats['accel_count']} 个</p>
            """
            
            if stats['distance_stats']:
                ds = stats['distance_stats']
                html_content += f"""
                    <p><strong>距离统计:</strong></p>
                    <ul>
                        <li>最小值: {ds['min']}</li>
                        <li>最大值: {ds['max']}</li>
                        <li>平均值: {ds['avg']:.2f}</li>
                        <li>标准差: {ds['std']:.2f}</li>
                    </ul>
                """
            
            html_content += "</div>"
        
        # 添加数据表格
        if self.uwb_packets:
            html_content += f"""
                <h2>UWB测距数据 (共{len(self.uwb_packets)}条)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>主机ID</th>
                            <th>从机ID</th>
                            <th>距离值</th>
                            <th>时间戳</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for i, packet in enumerate(self.uwb_packets[:100]):  # 只显示前100条
                html_content += f"""
                    <tr>
                        <td>{i + 1}</td>
                        <td>0x{packet.host_id:08X}</td>
                        <td>0x{packet.slave_id:08X}</td>
                        <td>{packet.distance}</td>
                        <td>{packet.timestamp:.3f}</td>
                    </tr>
                """
            
            html_content += "</tbody></table>"
            
            if len(self.uwb_packets) > 100:
                html_content += f"<p><em>注：仅显示前100条记录，共{len(self.uwb_packets)}条</em></p>"
        
        # 添加卡尔曼滤波分析部分
        if self.kalman_results:
            html_content += self._generate_kalman_html_section()
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML报告已生成: {output_file}")
    
    def _generate_kalman_html_section(self) -> str:
        """生成卡尔曼滤波HTML部分"""
        html_content = f"""
                <h2>卡尔曼滤波分析</h2>
                <div class="kalman-section">
                    <p>卡尔曼滤波是一种最优估计算法，用于减少测量噪声并提高数据质量。</p>
        """
        
        # 为每个数据集生成分析结果
        for dataset_name, kalman_result in self.kalman_results.items():
            if dataset_name == 'all_data':
                display_name = "全部数据"
            else:
                display_name = os.path.basename(dataset_name)
            
            comparison = kalman_result['comparison_results']
            summary = kalman_result['summary']
            
            html_content += f"""
                    <div class="kalman-dataset">
                        <h3>数据集: {display_name}</h3>
                        <div class="kalman-summary">
                            <div class="kalman-stats">
                                <div class="stat-item">
                                    <div class="stat-number">{summary['total_data_points']}</div>
                                    <div class="stat-label">数据点总数</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-number">{summary['best_filter']}</div>
                                    <div class="stat-label">最佳滤波器</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-number">{summary['best_noise_reduction']:.1f}%</div>
                                    <div class="stat-label">噪声减少</div>
                                </div>
                            </div>
                        </div>
                        
                        <h4>滤波器性能对比</h4>
                        <table class="kalman-table">
                            <thead>
                                <tr>
                                    <th>滤波器类型</th>
                                    <th>噪声减少 (%)</th>
                                    <th>均方误差</th>
                                    <th>信噪比改善 (dB)</th>
                                    <th>最终协方差</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            # 添加每个滤波器的结果
            for filter_type, result in comparison['comparison_results'].items():
                stats = result['statistics']
                html_content += f"""
                                <tr>
                                    <td>{filter_type}</td>
                                    <td>{stats.get('noise_reduction_percent', 0):.2f}</td>
                                    <td>{stats.get('mse', 0):.2f}</td>
                                    <td>{stats.get('snr_improvement_db', 0):.2f}</td>
                                    <td>{stats.get('final_covariance', 0):.2f}</td>
                                </tr>
                """
            
            html_content += """
                            </tbody>
                        </table>
                        
                        <h4>最佳滤波器详细分析</h4>
            """
            
            # 显示最佳滤波器的详细信息
            best_filter_type = summary['best_filter']
            if best_filter_type and best_filter_type in comparison['comparison_results']:
                best_result = comparison['comparison_results'][best_filter_type]
                best_stats = best_result['statistics']
                
                html_content += f"""
                        <div class="best-filter-details">
                            <p><strong>滤波器类型:</strong> {best_filter_type}</p>
                            <p><strong>原始数据标准差:</strong> {best_stats.get('raw_std', 0):.2f}</p>
                            <p><strong>滤波后标准差:</strong> {best_stats.get('filtered_std', 0):.2f}</p>
                            <p><strong>噪声减少:</strong> {best_stats.get('noise_reduction_percent', 0):.2f}%</p>
                            <p><strong>均方误差:</strong> {best_stats.get('mse', 0):.2f}</p>
                            <p><strong>平均创新值:</strong> {best_stats.get('average_innovation', 0):.2f}</p>
                            <p><strong>创新标准差:</strong> {best_stats.get('innovation_std', 0):.2f}</p>
                        </div>
                """
            
            html_content += """
                    </div>
            """
        
        # 添加卡尔曼滤波图表
        html_content += f"""
                    <h3>卡尔曼滤波可视化分析</h3>
                    <div class="kalman-charts">
                        <img src="{os.path.basename(self.kalman_results[list(self.kalman_results.keys())[0]]['chart_file'])}" 
                             alt="卡尔曼滤波分析图表" style="max-width: 100%; height: auto;">
                    </div>
                </div>
        """
        
        return html_content
    
    def _generate_json_data(self, output_file: str):
        """生成JSON数据文件"""
        data = {
            'analysis_time': datetime.now().isoformat(),
            'summary': {
                'total_uwb_packets': len(self.uwb_packets),
                'total_accel_packets': len(self.accel_packets),
                'files_analyzed': len(self.file_stats),
                'kalman_datasets': len(self.kalman_results)
            },
            'file_stats': self.file_stats,
            'uwb_packets': [packet.to_dict() for packet in self.uwb_packets],
            'accel_packets': [packet.to_dict() for packet in self.accel_packets],
            'kalman_results': self.kalman_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON数据已生成: {output_file}")
    
    def _generate_charts(self, output_dir: str) -> List[str]:
        """生成图表"""
        chart_files = []
        
        if not self.uwb_packets:
            return chart_files
        
        # 距离数据图表
        distances = [p.distance for p in self.uwb_packets]
        
        # 1. 距离趋势图
        plt.figure(figsize=(15, 8))
        plt.subplot(2, 2, 1)
        plt.plot(distances, 'b-', linewidth=1, alpha=0.8)
        plt.title('UWB距离数据趋势图', fontsize=14, fontweight='bold')
        plt.xlabel('数据包序号')
        plt.ylabel('距离值')
        plt.grid(True, alpha=0.3)
        
        # 2. 距离分布直方图
        plt.subplot(2, 2, 2)
        plt.hist(distances, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('距离数据分布直方图', fontsize=14, fontweight='bold')
        plt.xlabel('距离值')
        plt.ylabel('频次')
        plt.grid(True, alpha=0.3)
        
        # 3. 距离统计箱线图
        plt.subplot(2, 2, 3)
        plt.boxplot(distances, vert=True, patch_artist=True, 
                   boxprops=dict(facecolor='lightblue', alpha=0.7))
        plt.title('距离数据统计箱线图', fontsize=14, fontweight='bold')
        plt.ylabel('距离值')
        plt.grid(True, alpha=0.3)
        
        # 4. 距离变化率
        plt.subplot(2, 2, 4)
        if len(distances) > 1:
            changes = [distances[i] - distances[i-1] for i in range(1, len(distances))]
            plt.plot(changes, 'g-', linewidth=1, alpha=0.8)
            plt.title('距离变化率', fontsize=14, fontweight='bold')
            plt.xlabel('数据包序号')
            plt.ylabel('距离变化')
            plt.grid(True, alpha=0.3)
            plt.axhline(y=0, color='r', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        chart_file = os.path.join(output_dir, "uwb_analysis_charts.png")
        plt.savefig(chart_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        chart_files.append(chart_file)
        
        print(f"✓ 图表已生成: {chart_file}")
        
        return chart_files

def main():
    """主函数"""
    print("增强版UWB数据分析程序")
    print("=" * 50)
    
    analyzer = EnhancedUWBAnalyzer()
    
    # 批量解析所有txt文件
    results = analyzer.parse_multiple_files("*.txt")
    
    if not results:
        print("未找到任何数据文件")
        return
    
    print("\n" + "=" * 50)
    print("解析完成！")
    
    # 生成综合报告
    output_files = analyzer.generate_comprehensive_report("analysis_output")
    
    print("\n生成的文件：")
    for file_type, file_path in output_files.items():
        if isinstance(file_path, list):
            for f in file_path:
                print(f"  📊 {file_type}: {f}")
        else:
            print(f"  📊 {file_type}: {file_path}")
    
    print("\n使用方法：")
    print("• 双击HTML文件用浏览器打开查看综合报告")
    print("• 查看PNG文件了解数据可视化结果")
    print("• 查看JSON文件获取原始数据")

if __name__ == "__main__":
    main()
