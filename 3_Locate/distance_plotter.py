#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB距离数据折线图绘制程序
从解析的数据中提取距离信息并绘制折线图
"""

import os
import struct
import matplotlib.pyplot as plt
import matplotlib
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 宏定义：数据文件相对路径
LOCATION = "19-24_1-2_1.txt"

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

class DistancePlotter:
    """距离数据绘制器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.uwb_packets: List[UWBPacket] = []
        self.distances: List[int] = []
        
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
    
    def plot_distance_chart(self, output_file: str = "distance_chart.png"):
        """绘制距离数据折线图"""
        if not self.distances:
            print("没有距离数据可绘制")
            return
        
        print("绘制距离折线图...")
        
        # 创建图形和子图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # 准备数据
        x_values = list(range(1, len(self.distances) + 1))
        
        # 第一个子图：完整距离数据
        ax1.plot(x_values, self.distances, 'b-', linewidth=1.5, alpha=0.8)
        ax1.set_title('UWB测距数据折线图', fontsize=16, fontweight='bold')
        ax1.set_xlabel('数据包序号', fontsize=12)
        ax1.set_ylabel('距离值', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.set_facecolor('#f8f9fa')
        
        # 添加统计信息
        mean_distance = sum(self.distances) / len(self.distances)
        ax1.axhline(y=mean_distance, color='r', linestyle='--', alpha=0.7, 
                   label=f'平均值: {mean_distance:.1f}')
        ax1.legend()
        
        # 第二个子图：距离数据分布直方图
        ax2.hist(self.distances, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.set_title('距离数据分布直方图', fontsize=16, fontweight='bold')
        ax2.set_xlabel('距离值', fontsize=12)
        ax2.set_ylabel('频次', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_facecolor('#f8f9fa')
        
        # 添加统计信息到直方图
        ax2.axvline(x=mean_distance, color='r', linestyle='--', alpha=0.7, 
                   label=f'平均值: {mean_distance:.1f}')
        ax2.legend()
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"✓ 距离折线图已保存: {output_file}")
        
        # 关闭图形以释放内存
        plt.close()
        
        return output_file
    
    def plot_detailed_chart(self, output_file: str = "distance_detailed.png"):
        """绘制详细的距离分析图"""
        if not self.distances:
            print("没有距离数据可绘制")
            return
        
        print("绘制详细距离分析图...")
        
        # 创建图形和子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 准备数据
        x_values = list(range(1, len(self.distances) + 1))
        
        # 1. 距离趋势图
        ax1.plot(x_values, self.distances, 'b-', linewidth=1, alpha=0.8)
        ax1.set_title('距离数据趋势图', fontsize=14, fontweight='bold')
        ax1.set_xlabel('数据包序号')
        ax1.set_ylabel('距离值')
        ax1.grid(True, alpha=0.3)
        
        # 2. 距离变化率
        if len(self.distances) > 1:
            changes = [self.distances[i] - self.distances[i-1] for i in range(1, len(self.distances))]
            ax2.plot(x_values[1:], changes, 'g-', linewidth=1, alpha=0.8)
            ax2.set_title('距离变化率', fontsize=14, fontweight='bold')
            ax2.set_xlabel('数据包序号')
            ax2.set_ylabel('距离变化')
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=0, color='r', linestyle='-', alpha=0.5)
        
        # 3. 距离分布直方图
        ax3.hist(self.distances, bins=25, alpha=0.7, color='orange', edgecolor='black')
        ax3.set_title('距离数据分布', fontsize=14, fontweight='bold')
        ax3.set_xlabel('距离值')
        ax3.set_ylabel('频次')
        ax3.grid(True, alpha=0.3)
        
        # 4. 距离统计箱线图
        ax4.boxplot(self.distances, vert=True, patch_artist=True, 
                   boxprops=dict(facecolor='lightblue', alpha=0.7))
        ax4.set_title('距离数据统计', fontsize=14, fontweight='bold')
        ax4.set_ylabel('距离值')
        ax4.grid(True, alpha=0.3)
        
        # 添加统计信息
        mean_val = sum(self.distances) / len(self.distances)
        min_val = min(self.distances)
        max_val = max(self.distances)
        std_val = (sum((x - mean_val) ** 2 for x in self.distances) / len(self.distances)) ** 0.5
        
        stats_text = f"""统计信息:
数据包数量: {len(self.distances)}
平均值: {mean_val:.1f}
最小值: {min_val}
最大值: {max_val}
标准差: {std_val:.1f}"""
        
        ax4.text(0.02, 0.98, stats_text, transform=ax4.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"✓ 详细分析图已保存: {output_file}")
        
        # 关闭图形以释放内存
        plt.close()
        
        return output_file
    
    def run_analysis(self):
        """运行完整的距离数据分析流程"""
        print("UWB距离数据折线图绘制程序")
        print("=" * 40)
        
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
            
            # 2. 绘制基础折线图
            chart_file = self.plot_distance_chart()
            
            # 3. 绘制详细分析图
            detailed_file = self.plot_detailed_chart()
            
            print("\n" + "=" * 40)
            print("分析完成！生成的文件：")
            print(f"📊 基础折线图: {chart_file}")
            print(f"📈 详细分析图: {detailed_file}")
            print("\n图表说明：")
            print("• 基础折线图：显示距离数据的变化趋势")
            print("• 详细分析图：包含趋势、变化率、分布和统计信息")
            
        except Exception as e:
            print(f"分析过程中发生错误: {e}")

def main():
    """主函数"""
    plotter = DistancePlotter(LOCATION)
    plotter.run_analysis()

if __name__ == "__main__":
    main()
