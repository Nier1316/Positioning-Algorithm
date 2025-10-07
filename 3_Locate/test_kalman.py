#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试卡尔曼滤波功能
"""

import numpy as np
from kalman_filter import UWBKalmanProcessor

def test_kalman_filter():
    """测试卡尔曼滤波器"""
    print("测试卡尔曼滤波器...")
    
    # 创建测试数据
    np.random.seed(42)
    true_signal = np.sin(np.linspace(0, 4*np.pi, 50)) * 20 + 1000
    noise = np.random.normal(0, 10, 50)
    test_data = (true_signal + noise).astype(int).tolist()
    
    print(f"测试数据: {test_data[:10]}...")
    
    # 创建处理器
    processor = UWBKalmanProcessor()
    
    # 测试标准滤波器
    result = processor.process_distance_data(test_data, 'standard')
    print(f"滤波后数据: {result['filtered_distances'][:10]}")
    print(f"噪声减少: {result['statistics']['noise_reduction_percent']:.2f}%")
    
    # 测试比较功能
    comparison = processor.compare_filters(test_data)
    print(f"最佳滤波器: {comparison['best_filter']}")
    print(f"最佳噪声减少: {comparison['best_noise_reduction']:.2f}%")
    
    # 生成图表
    chart_file = processor.generate_kalman_charts(test_data, "test_kalman_chart.png")
    print(f"图表已生成: {chart_file}")
    
    print("测试完成！")

if __name__ == "__main__":
    test_kalman_filter()
