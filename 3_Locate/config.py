#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB数据分析配置文件
定义各种分析参数和配置选项
"""

import os
from typing import Dict, List, Any

class AnalysisConfig:
    """分析配置类"""
    
    # 文件处理配置
    DEFAULT_FILE_PATTERN = "*.txt"
    SUPPORTED_EXTENSIONS = [".txt", ".hex", ".dat"]
    
    # 数据包配置
    UWB_PACKET_CONFIG = {
        'header': [0xDD, 0x66],
        'tail': [0xAA, 0xBB],
        'min_length': 12,
        'fields': {
            'host_id': {'offset': 2, 'size': 4, 'type': 'uint32', 'endian': 'big'},
            'slave_id': {'offset': 6, 'size': 4, 'type': 'uint32', 'endian': 'big'},
            'distance': {'offset': 10, 'size': 2, 'type': 'uint16', 'endian': 'big'}
        }
    }
    
    ACCEL_PACKET_CONFIG = {
        'header': [0xAA, 0xCC, 0xFF, 0x1C],
        'tail': [0xDD, 0xCC],
        'min_length': 26,
        'fields': {
            'device_id': {'offset': 4, 'size': 4, 'type': 'uint32', 'endian': 'big'},
            'x_acc': {'offset': 8, 'size': 2, 'type': 'int16', 'endian': 'big'},
            'y_acc': {'offset': 10, 'size': 2, 'type': 'int16', 'endian': 'big'},
            'z_acc': {'offset': 12, 'size': 2, 'type': 'int16', 'endian': 'big'},
            'x_gyro': {'offset': 14, 'size': 2, 'type': 'int16', 'endian': 'big'},
            'y_gyro': {'offset': 16, 'size': 2, 'type': 'int16', 'endian': 'big'},
            'z_gyro': {'offset': 18, 'size': 2, 'type': 'int16', 'endian': 'big'},
            'altitude': {'offset': 20, 'size': 4, 'type': 'uint32', 'endian': 'big'},
            'crc16': {'offset': 24, 'size': 2, 'type': 'uint16', 'endian': 'big'}
        }
    }
    
    # 数据验证配置
    VALIDATION_CONFIG = {
        'uwb': {
            'distance_range': (0, 65535),
            'host_id_range': (0, 0xFFFFFFFF),
            'slave_id_range': (0, 0xFFFFFFFF)
        },
        'accel': {
            'accel_range': (-32767, 32767),
            'gyro_range': (-32767, 32767),
            'altitude_range': (0, 0xFFFFFFFF),
            'device_id_range': (0, 0xFFFFFFFF)
        }
    }
    
    # 输出配置
    OUTPUT_CONFIG = {
        'html': {
            'max_display_records': 100,
            'include_charts': True,
            'chart_dpi': 300,
            'chart_format': 'png'
        },
        'json': {
            'indent': 2,
            'ensure_ascii': False,
            'include_timestamps': True
        },
        'csv': {
            'delimiter': ',',
            'include_headers': True,
            'encoding': 'utf-8'
        }
    }
    
    # 图表配置
    CHART_CONFIG = {
        'figure_size': (15, 8),
        'dpi': 300,
        'colors': {
            'primary': '#007bff',
            'secondary': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        },
        'styles': {
            'line_width': 1.5,
            'alpha': 0.8,
            'grid_alpha': 0.3
        }
    }
    
    # 分析配置
    ANALYSIS_CONFIG = {
        'statistics': {
            'calculate_std': True,
            'calculate_median': True,
            'calculate_percentiles': [25, 50, 75, 90, 95, 99],
            'outlier_detection': True,
            'outlier_method': 'iqr'  # 'iqr' or 'zscore'
        },
        'filtering': {
            'enable_distance_filter': True,
            'distance_threshold': (0, 10000),  # 合理距离范围
            'enable_accel_filter': True,
            'accel_threshold': (-1000, 1000),  # 合理加速度范围
            'enable_gyro_filter': True,
            'gyro_threshold': (-1000, 1000)   # 合理陀螺仪范围
        },
        'smoothing': {
            'enable_smoothing': False,
            'smoothing_window': 5,
            'smoothing_method': 'moving_average'  # 'moving_average' or 'savgol'
        }
    }
    
    @classmethod
    def get_file_patterns(cls) -> List[str]:
        """获取支持的文件模式"""
        return [f"*{ext}" for ext in cls.SUPPORTED_EXTENSIONS]
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置的有效性"""
        try:
            # 检查UWB配置
            uwb_config = cls.UWB_PACKET_CONFIG
            assert len(uwb_config['header']) == 2
            assert len(uwb_config['tail']) == 2
            assert uwb_config['min_length'] > 0
            
            # 检查加速度配置
            accel_config = cls.ACCEL_PACKET_CONFIG
            assert len(accel_config['header']) == 4
            assert len(accel_config['tail']) == 2
            assert accel_config['min_length'] > 0
            
            return True
        except (AssertionError, KeyError):
            return False
    
    @classmethod
    def get_output_directory(cls, base_dir: str = ".") -> str:
        """获取输出目录路径"""
        output_dir = os.path.join(base_dir, "analysis_output")
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

# 预定义的设备ID映射（可根据实际情况修改）
DEVICE_ID_MAP = {
    0x21A688DB: "设备1",
    0x3543C42E: "设备2",
    # 可以根据实际设备添加更多映射
}

# 预定义的分析模板
ANALYSIS_TEMPLATES = {
    'basic': {
        'description': '基础分析',
        'include_charts': True,
        'include_statistics': True,
        'include_html_report': True
    },
    'detailed': {
        'description': '详细分析',
        'include_charts': True,
        'include_statistics': True,
        'include_html_report': True,
        'include_json_export': True,
        'include_csv_export': True,
        'include_outlier_analysis': True
    },
    'performance': {
        'description': '性能分析',
        'include_charts': True,
        'include_statistics': True,
        'include_html_report': True,
        'include_performance_metrics': True,
        'include_timing_analysis': True
    }
}

def get_config() -> AnalysisConfig:
    """获取配置实例"""
    return AnalysisConfig()

def load_custom_config(config_file: str) -> Dict[str, Any]:
    """从文件加载自定义配置"""
    import json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {config_file} 不存在，使用默认配置")
        return {}
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        return {}

def save_config(config: Dict[str, Any], config_file: str):
    """保存配置到文件"""
    import json
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"配置已保存到: {config_file}")
    except Exception as e:
        print(f"保存配置时发生错误: {e}")

if __name__ == "__main__":
    # 测试配置
    config = get_config()
    print("配置验证:", config.validate_config())
    print("支持的文件模式:", config.get_file_patterns())
    print("输出目录:", config.get_output_directory())
