#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卡尔曼滤波器实现
用于UWB距离数据的噪声滤波和平滑处理
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import json

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

@dataclass
class KalmanConfig:
    """卡尔曼滤波器配置"""
    # 过程噪声协方差 (Q)
    process_noise: float = 1.0
    # 测量噪声协方差 (R)
    measurement_noise: float = 10.0
    # 初始状态协方差 (P)
    initial_covariance: float = 100.0
    # 初始状态估计
    initial_state: float = 0.0
    # 状态转移矩阵 (F)
    state_transition: float = 1.0
    # 观测矩阵 (H)
    observation_matrix: float = 1.0
    # 控制输入矩阵 (B) - 对于距离数据通常为0
    control_matrix: float = 0.0

class KalmanFilter:
    """一维卡尔曼滤波器"""
    
    def __init__(self, config: KalmanConfig):
        self.config = config
        
        # 初始化状态
        self.x = config.initial_state  # 状态估计
        self.P = config.initial_covariance  # 状态协方差
        self.Q = config.process_noise  # 过程噪声协方差
        self.R = config.measurement_noise  # 测量噪声协方差
        self.F = config.state_transition  # 状态转移矩阵
        self.H = config.observation_matrix  # 观测矩阵
        self.B = config.control_matrix  # 控制输入矩阵
        
        # 存储历史数据
        self.filtered_values: List[float] = []
        self.raw_values: List[float] = []
        self.predicted_values: List[float] = []
        self.innovation_values: List[float] = []
        self.covariance_values: List[float] = []
        
    def predict(self, u: float = 0.0) -> float:
        """预测步骤"""
        # 状态预测: x = F*x + B*u
        self.x = self.F * self.x + self.B * u
        
        # 协方差预测: P = F*P*F^T + Q
        self.P = self.F * self.P * self.F + self.Q
        
        return self.x
    
    def update(self, z: float) -> float:
        """更新步骤"""
        # 计算卡尔曼增益: K = P*H^T / (H*P*H^T + R)
        K = self.P * self.H / (self.H * self.P * self.H + self.R)
        
        # 计算创新 (残差): y = z - H*x
        innovation = z - self.H * self.x
        
        # 状态更新: x = x + K*y
        self.x = self.x + K * innovation
        
        # 协方差更新: P = (I - K*H)*P
        self.P = (1 - K * self.H) * self.P
        
        # 存储数据
        self.innovation_values.append(innovation)
        self.covariance_values.append(self.P)
        
        return self.x
    
    def filter_sequence(self, measurements: List[float]) -> List[float]:
        """对测量序列进行滤波"""
        self.filtered_values = []
        self.raw_values = measurements.copy()
        self.predicted_values = []
        
        for z in measurements:
            # 预测步骤
            predicted = self.predict()
            self.predicted_values.append(predicted)
            
            # 更新步骤
            filtered = self.update(z)
            self.filtered_values.append(filtered)
        
        return self.filtered_values
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取滤波统计信息"""
        if not self.raw_values or not self.filtered_values:
            return {}
        
        raw_values = np.array(self.raw_values)
        filtered_values = np.array(self.filtered_values)
        
        # 计算噪声减少
        raw_std = np.std(raw_values)
        filtered_std = np.std(filtered_values)
        noise_reduction = (raw_std - filtered_std) / raw_std * 100
        
        # 计算均方误差
        mse = np.mean((raw_values - filtered_values) ** 2)
        
        # 计算信噪比改善
        signal_power = np.mean(filtered_values ** 2)
        noise_power = np.mean((raw_values - filtered_values) ** 2)
        snr_improvement = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')
        
        return {
            'raw_std': raw_std,
            'filtered_std': filtered_std,
            'noise_reduction_percent': noise_reduction,
            'mse': mse,
            'snr_improvement_db': snr_improvement,
            'final_covariance': self.P,
            'average_innovation': np.mean(self.innovation_values) if self.innovation_values else 0,
            'innovation_std': np.std(self.innovation_values) if self.innovation_values else 0
        }

class AdaptiveKalmanFilter(KalmanFilter):
    """自适应卡尔曼滤波器"""
    
    def __init__(self, config: KalmanConfig):
        super().__init__(config)
        self.adaptive_R = config.measurement_noise
        self.innovation_history = []
        self.window_size = 10
        
    def update_measurement_noise(self, innovation: float):
        """自适应更新测量噪声协方差"""
        self.innovation_history.append(innovation)
        
        if len(self.innovation_history) > self.window_size:
            self.innovation_history.pop(0)
        
        if len(self.innovation_history) >= 3:
            # 使用创新序列的方差来估计测量噪声
            innovation_var = np.var(self.innovation_history)
            # 限制R的变化范围
            self.R = max(0.1, min(100.0, innovation_var))
    
    def update(self, z: float) -> float:
        """自适应更新步骤"""
        # 预测步骤
        predicted = self.predict()
        
        # 计算创新
        innovation = z - self.H * predicted
        
        # 自适应更新测量噪声
        self.update_measurement_noise(innovation)
        
        # 计算卡尔曼增益
        K = self.P * self.H / (self.H * self.P * self.H + self.R)
        
        # 状态更新
        self.x = self.x + K * innovation
        
        # 协方差更新
        self.P = (1 - K * self.H) * self.P
        
        # 存储数据
        self.innovation_values.append(innovation)
        self.covariance_values.append(self.P)
        
        return self.x

class UWBKalmanProcessor:
    """UWB数据卡尔曼滤波处理器"""
    
    def __init__(self):
        self.kalman_configs = {
            'standard': KalmanConfig(
                process_noise=1.0,
                measurement_noise=50.0,
                initial_covariance=100.0
            ),
            'smooth': KalmanConfig(
                process_noise=0.1,
                measurement_noise=100.0,
                initial_covariance=200.0
            ),
            'responsive': KalmanConfig(
                process_noise=5.0,
                measurement_noise=10.0,
                initial_covariance=50.0
            ),
            'adaptive': KalmanConfig(
                process_noise=1.0,
                measurement_noise=50.0,
                initial_covariance=100.0
            )
        }
        
        self.filters = {}
        self.results = {}
    
    def process_distance_data(self, distances: List[int], filter_type: str = 'standard') -> Dict[str, Any]:
        """处理距离数据"""
        if filter_type not in self.kalman_configs:
            raise ValueError(f"未知的滤波器类型: {filter_type}")
        
        # 初始化滤波器
        if filter_type == 'adaptive':
            filter_obj = AdaptiveKalmanFilter(self.kalman_configs[filter_type])
        else:
            filter_obj = KalmanFilter(self.kalman_configs[filter_type])
        
        # 设置初始状态为第一个测量值
        if distances:
            filter_obj.x = float(distances[0])
        
        # 执行滤波
        filtered_distances = filter_obj.filter_sequence([float(d) for d in distances])
        
        # 获取统计信息
        stats = filter_obj.get_statistics()
        
        # 存储结果
        result = {
            'filter_type': filter_type,
            'raw_distances': distances,
            'filtered_distances': [round(d, 2) for d in filtered_distances],
            'predicted_distances': [round(d, 2) for d in filter_obj.predicted_values],
            'innovations': [round(d, 2) for d in filter_obj.innovation_values],
            'covariances': [round(d, 2) for d in filter_obj.covariance_values],
            'statistics': stats,
            'filter_config': {
                'process_noise': filter_obj.Q,
                'measurement_noise': filter_obj.R,
                'initial_covariance': filter_obj.P
            }
        }
        
        self.filters[filter_type] = filter_obj
        self.results[filter_type] = result
        
        return result
    
    def compare_filters(self, distances: List[int]) -> Dict[str, Any]:
        """比较不同滤波器的效果"""
        comparison_results = {}
        
        for filter_type in self.kalman_configs.keys():
            try:
                result = self.process_distance_data(distances, filter_type)
                comparison_results[filter_type] = result
            except Exception as e:
                print(f"滤波器 {filter_type} 处理失败: {e}")
                continue
        
        # 选择最佳滤波器（基于噪声减少百分比）
        best_filter = None
        best_noise_reduction = -float('inf')
        
        for filter_type, result in comparison_results.items():
            noise_reduction = result['statistics'].get('noise_reduction_percent', 0)
            if noise_reduction > best_noise_reduction:
                best_noise_reduction = noise_reduction
                best_filter = filter_type
        
        return {
            'comparison_results': comparison_results,
            'best_filter': best_filter,
            'best_noise_reduction': best_noise_reduction
        }
    
    def generate_kalman_charts(self, distances: List[int], output_file: str = "kalman_analysis.png") -> str:
        """生成卡尔曼滤波分析图表"""
        # 比较所有滤波器
        comparison = self.compare_filters(distances)
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('UWB距离数据卡尔曼滤波分析', fontsize=16, fontweight='bold')
        
        # 1. 原始数据 vs 滤波后数据对比
        ax1 = axes[0, 0]
        x_values = list(range(len(distances)))
        
        ax1.plot(x_values, distances, 'b-', alpha=0.7, label='原始数据', linewidth=1)
        
        colors = ['red', 'green', 'orange', 'purple']
        for i, (filter_type, result) in enumerate(comparison['comparison_results'].items()):
            if i < len(colors):
                ax1.plot(x_values, result['filtered_distances'], 
                        color=colors[i], alpha=0.8, label=f'{filter_type}滤波', linewidth=1.5)
        
        ax1.set_title('原始数据 vs 滤波后数据对比')
        ax1.set_xlabel('数据点序号')
        ax1.set_ylabel('距离值')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 噪声减少效果对比
        ax2 = axes[0, 1]
        filter_names = []
        noise_reductions = []
        
        for filter_type, result in comparison['comparison_results'].items():
            filter_names.append(filter_type)
            noise_reductions.append(result['statistics'].get('noise_reduction_percent', 0))
        
        bars = ax2.bar(filter_names, noise_reductions, color=colors[:len(filter_names)], alpha=0.7)
        ax2.set_title('各滤波器噪声减少效果')
        ax2.set_xlabel('滤波器类型')
        ax2.set_ylabel('噪声减少百分比 (%)')
        ax2.grid(True, alpha=0.3)
        
        # 在柱状图上添加数值标签
        for bar, value in zip(bars, noise_reductions):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{value:.1f}%', ha='center', va='bottom')
        
        # 3. 最佳滤波器的详细分析
        best_filter_type = comparison['best_filter']
        if best_filter_type:
            best_result = comparison['comparison_results'][best_filter_type]
            
            ax3 = axes[1, 0]
            ax3.plot(x_values, distances, 'b-', alpha=0.5, label='原始数据', linewidth=1)
            ax3.plot(x_values, best_result['filtered_distances'], 'r-', 
                    label=f'{best_filter_type}滤波', linewidth=2)
            ax3.fill_between(x_values, 
                           [d - np.sqrt(c) for d, c in zip(best_result['filtered_distances'], best_result['covariances'])],
                           [d + np.sqrt(c) for d, c in zip(best_result['filtered_distances'], best_result['covariances'])],
                           alpha=0.2, color='red', label='置信区间')
            
            ax3.set_title(f'最佳滤波器 ({best_filter_type}) 详细分析')
            ax3.set_xlabel('数据点序号')
            ax3.set_ylabel('距离值')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 4. 创新序列（残差）
            ax4 = axes[1, 1]
            ax4.plot(x_values[1:], best_result['innovations'], 'g-', alpha=0.7, linewidth=1)
            ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax4.set_title('创新序列 (残差)')
            ax4.set_xlabel('数据点序号')
            ax4.set_ylabel('创新值')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return output_file
    
    def generate_kalman_report_data(self, distances: List[int]) -> Dict[str, Any]:
        """生成卡尔曼滤波报告数据"""
        comparison = self.compare_filters(distances)
        
        # 生成图表
        chart_file = self.generate_kalman_charts(distances)
        
        return {
            'comparison_results': comparison,
            'chart_file': chart_file,
            'summary': {
                'total_data_points': len(distances),
                'best_filter': comparison['best_filter'],
                'best_noise_reduction': comparison['best_noise_reduction'],
                'available_filters': list(self.kalman_configs.keys())
            }
        }

def main():
    """测试函数"""
    # 生成测试数据
    np.random.seed(42)
    true_signal = np.sin(np.linspace(0, 4*np.pi, 100)) * 50 + 1000
    noise = np.random.normal(0, 20, 100)
    test_data = (true_signal + noise).astype(int).tolist()
    
    # 创建处理器
    processor = UWBKalmanProcessor()
    
    # 处理数据
    result = processor.generate_kalman_report_data(test_data)
    
    print("卡尔曼滤波测试完成")
    print(f"最佳滤波器: {result['summary']['best_filter']}")
    print(f"噪声减少: {result['summary']['best_noise_reduction']:.2f}%")
    print(f"图表文件: {result['chart_file']}")

if __name__ == "__main__":
    main()
