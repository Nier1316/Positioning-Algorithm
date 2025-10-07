#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from uwb_analyzer_enhanced import EnhancedUWBAnalyzer
    print("✓ 成功导入 EnhancedUWBAnalyzer")
    
    analyzer = EnhancedUWBAnalyzer()
    print("✓ 成功创建分析器实例")
    
    # 测试解析单个文件
    result = analyzer.parse_single_file('19-24_1-2_1.txt')
    print(f"✓ 解析结果: {result}")
    print(f"✓ UWB数据包数量: {len(analyzer.uwb_packets)}")
    
    if analyzer.uwb_packets:
        # 测试卡尔曼滤波
        distances = [p.distance for p in analyzer.uwb_packets]
        print(f"✓ 距离数据: {distances[:5]}...")
        
        kalman_result = analyzer.apply_kalman_filtering()
        print(f"✓ 卡尔曼滤波结果: {len(kalman_result)} 个数据集")
        
        # 生成报告
        output_files = analyzer.generate_comprehensive_report("test_output")
        print(f"✓ 生成的文件: {list(output_files.keys())}")
    else:
        print("❌ 没有找到UWB数据包")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
