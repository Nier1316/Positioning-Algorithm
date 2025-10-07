#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卡尔曼滤波演示脚本
展示卡尔曼滤波对UWB数据的处理效果
"""

import os
import sys
from uwb_kalman_analyzer import UWBKalmanAnalyzer

def show_demo():
    """显示演示信息"""
    print("UWB数据卡尔曼滤波演示")
    print("=" * 50)
    
    print("本演示将展示卡尔曼滤波对UWB距离数据的处理效果。")
    print("卡尔曼滤波是一种最优估计算法，能够有效减少测量噪声。")
    print()
    
    print("演示内容：")
    print("1. 解析UWB数据文件")
    print("2. 应用卡尔曼滤波算法")
    print("3. 生成对比分析图表")
    print("4. 输出综合HTML报告")
    print()
    
    # 检查数据文件
    data_files = [f for f in os.listdir('.') if f.endswith('.txt')]
    if not data_files:
        print("❌ 未找到数据文件 (.txt)")
        return
    
    print(f"找到 {len(data_files)} 个数据文件:")
    for file in data_files[:5]:
        print(f"  📄 {file}")
    if len(data_files) > 5:
        print(f"  ... 还有 {len(data_files) - 5} 个文件")
    print()
    
    # 运行分析
    print("开始分析...")
    analyzer = UWBKalmanAnalyzer()
    analyzer.run_analysis()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print()
    print("生成的文件：")
    if os.path.exists("kalman_output"):
        for file in os.listdir("kalman_output"):
            file_path = os.path.join("kalman_output", file)
            size = os.path.getsize(file_path)
            print(f"  📊 {file} ({size} 字节)")
    
    print("\n使用方法：")
    print("• 双击 kalman_analysis_report.html 查看完整报告")
    print("• 查看 kalman_analysis.png 了解可视化效果")
    print("• 查看 kalman_analysis_data.json 获取原始数据")
    
    print("\n卡尔曼滤波效果说明：")
    print("• 噪声减少百分比 > 50%：滤波效果优秀")
    print("• 噪声减少百分比 30-50%：滤波效果良好")
    print("• 噪声减少百分比 10-30%：滤波效果一般")
    print("• 噪声减少百分比 < 10%：滤波效果有限")

def show_kalman_info():
    """显示卡尔曼滤波信息"""
    print("\n卡尔曼滤波算法说明：")
    print("-" * 30)
    print("卡尔曼滤波是一种最优估计算法，通过以下步骤工作：")
    print()
    print("1. 预测步骤：")
    print("   - 基于历史数据预测当前状态")
    print("   - 考虑系统模型的不确定性")
    print()
    print("2. 更新步骤：")
    print("   - 结合新的测量数据")
    print("   - 计算最优估计值")
    print("   - 更新不确定性估计")
    print()
    print("3. 噪声减少：")
    print("   - 有效减少测量噪声")
    print("   - 保持数据的真实趋势")
    print("   - 提供不确定性量化")
    print()
    print("对于UWB距离数据，卡尔曼滤波能够：")
    print("• 减少由于多径效应引起的噪声")
    print("• 平滑由于环境干扰造成的跳变")
    print("• 提供更稳定的距离估计")
    print("• 量化估计的不确定性")

def main():
    """主函数"""
    show_demo()
    show_kalman_info()

if __name__ == "__main__":
    main()
