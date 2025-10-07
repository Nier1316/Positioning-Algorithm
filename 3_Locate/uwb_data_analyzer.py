#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB测距数据和加速度数据解析分析程序
解析数据并生成HTML表格文件
"""

import os
import struct
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

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
    
    def __str__(self):
        return f"Accel: Device={self.device_id:08X}, X={self.x_acc}, Y={self.y_acc}, Z={self.z_acc}"

class UWBDataAnalyzer:
    """UWB数据解析分析器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.uwb_packets: List[UWBPacket] = []
        self.accel_packets: List[AccelPacket] = []
        
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
    
    def parse_data(self):
        """解析所有数据包"""
        print("开始解析数据...")
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
                pos = new_pos
                packet_count += 1
                
                if packet_count <= 5:  # 只显示前5个数据包
                    print(f"找到UWB数据包 {packet_count}: {uwb_packet}")
                elif packet_count == 6:
                    print("...")
                
                # 检查UWB数据包后是否有AA CC
                if pos < len(data) - 1 and data[pos] == 0xAA and data[pos+1] == 0xCC:
                    # 查找加速度数据包
                    accel_result = self.find_accel_packet(data, pos)
                    if accel_result:
                        accel_packet, new_pos = accel_result
                        self.accel_packets.append(accel_packet)
                        pos = new_pos
                        if packet_count <= 5:
                            print(f"找到加速度数据包: {accel_packet}")
                continue
            
            # 如果没找到UWB数据包，继续搜索
            pos += 1
        
        print(f"\n解析完成！")
        print(f"UWB数据包数量: {len(self.uwb_packets)}")
        print(f"加速度数据包数量: {len(self.accel_packets)}")
    
    
    
    def generate_html(self, output_file: str = "data_table.html"):
        """生成HTML表格文件"""
        print("生成HTML表格...")
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>UWB测距和加速度数据分析</title>
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
                .stats {{
                    display: flex;
                    justify-content: space-around;
                    margin: 20px 0;
                }}
                .stat-item {{
                    text-align: center;
                    padding: 15px;
                    background-color: #e9ecef;
                    border-radius: 5px;
                    min-width: 150px;
                }}
                .stat-number {{
                    font-size: 24px;
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
                <h1>UWB测距和加速度数据分析报告</h1>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">{len(self.uwb_packets)}</div>
                        <div class="stat-label">UWB数据包</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len(self.accel_packets)}</div>
                        <div class="stat-label">加速度数据包</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{datetime.now().strftime("%H:%M:%S")}</div>
                        <div class="stat-label">解析时间</div>
                    </div>
                </div>
                
                <h2>UWB测距数据 (共{len(self.uwb_packets)}条)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>包头</th>
                            <th>主机ID</th>
                            <th>从机ID</th>
                            <th>测距数据</th>
                            <th>包尾</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # 添加UWB数据 (显示所有数据)
        for i, packet in enumerate(self.uwb_packets):
            html_content += f"""
                        <tr>
                            <td>{i + 1}</td>
                            <td>{packet.header.hex().upper()}</td>
                            <td>0x{packet.host_id:08X}</td>
                            <td>0x{packet.slave_id:08X}</td>
                            <td>{packet.distance}</td>
                            <td>{packet.tail.hex().upper()}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
                
                <h2>加速度数据 (共{len(self.accel_packets)}条)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>包头</th>
                            <th>设备ID</th>
                            <th>X轴加速度</th>
                            <th>Y轴加速度</th>
                            <th>Z轴加速度</th>
                            <th>X轴陀螺仪</th>
                            <th>Y轴陀螺仪</th>
                            <th>Z轴陀螺仪</th>
                            <th>高度</th>
                            <th>包尾</th>
                            <th>CRC16校验</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # 添加加速度数据 (显示所有数据)
        for i, packet in enumerate(self.accel_packets):
            html_content += f"""
                        <tr>
                            <td>{i + 1}</td>
                            <td>{packet.header.hex().upper()}</td>
                            <td>0x{packet.device_id:08X}</td>
                            <td>{packet.x_acc}</td>
                            <td>{packet.y_acc}</td>
                            <td>{packet.z_acc}</td>
                            <td>{packet.x_gyro}</td>
                            <td>{packet.y_gyro}</td>
                            <td>{packet.z_gyro}</td>
                            <td>{packet.altitude}</td>
                            <td>{packet.tail.hex().upper()}</td>
                            <td>0x{packet.crc16:04X}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
                
                <p style="text-align: center; color: #666; margin-top: 30px;">
                    共解析 {len(self.uwb_packets)} 个UWB数据包和 {len(self.accel_packets)} 个加速度数据包
                </p>
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML表格已生成: {output_file}")
        return output_file
    
    def run_analysis(self):
        """运行完整的数据分析流程"""
        print("UWB测距数据和加速度数据解析分析程序")
        print("=" * 50)
        
        # 检查文件是否存在
        if not os.path.exists(self.file_path):
            print(f"错误：文件 {self.file_path} 不存在")
            return
        
        try:
            # 1. 解析数据
            self.parse_data()
            
            if not self.uwb_packets and not self.accel_packets:
                print("未找到任何数据包")
                return
            
            # 2. 生成HTML文件
            html_file = self.generate_html()
            
            print("\n" + "=" * 50)
            print("分析完成！生成的文件：")
            print(f"🌐 HTML表格文件: {html_file}")
            print("\n使用方法：")
            print("• 双击HTML文件用浏览器打开查看网页表格")
            
        except Exception as e:
            print(f"分析过程中发生错误: {e}")

def main():
    """主函数"""
    analyzer = UWBDataAnalyzer(LOCATION)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
