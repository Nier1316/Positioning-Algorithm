#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB数据分析工具演示脚本
展示新功能和使用方法
"""

import os
import sys
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title):
    """打印章节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)

def demo_basic_usage():
    """演示基本使用方法"""
    print_section("基本使用方法演示")
    
    print("1. 使用增强版分析器分析所有文件:")
    print("   python uwb_analyzer_enhanced.py")
    
    print("\n2. 使用批处理脚本:")
    print("   python run_analysis.py")
    print("   python run_analysis.py -v  # 显示详细信息")
    
    print("\n3. 分析特定文件模式:")
    print("   python run_analysis.py -p '19-24_1-*.txt'")
    
    print("\n4. 使用不同分析模板:")
    print("   python run_analysis.py -t basic      # 基础分析")
    print("   python run_analysis.py -t detailed   # 详细分析")
    print("   python run_analysis.py -t performance # 性能分析")

def demo_file_operations():
    """演示文件操作功能"""
    print_section("文件操作功能演示")
    
    print("1. 列出匹配的文件:")
    print("   python run_analysis.py --list")
    
    print("\n2. 查看文件信息:")
    print("   python run_analysis.py --info 19-24_1-2_1.txt")
    
    print("\n3. 查看可用模板:")
    print("   python run_analysis.py --templates")

def demo_output_files():
    """演示输出文件"""
    print_section("输出文件说明")
    
    output_dir = "analysis_output"
    if os.path.exists(output_dir):
        print("生成的文件:")
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            print(f"  📄 {file} ({size} 字节)")
        
        print("\n文件用途:")
        print("  📊 comprehensive_analysis.html - 综合HTML报告")
        print("  📄 analysis_data.json - JSON格式数据")
        print("  📈 uwb_analysis_charts.png - 数据可视化图表")
    else:
        print("输出目录不存在，请先运行分析程序")

def demo_data_analysis():
    """演示数据分析功能"""
    print_section("数据分析功能")
    
    print("支持的数据类型:")
    print("  🔍 UWB测距数据包 (DD 66 ... AA BB)")
    print("  📱 加速度数据包 (AA CC FF 1C ... DD CC)")
    
    print("\n分析功能:")
    print("  📊 统计分析 (平均值、标准差、最值等)")
    print("  📈 数据可视化 (趋势图、直方图、箱线图)")
    print("  🔍 异常检测和数据验证")
    print("  📋 多文件对比分析")
    
    print("\n输出格式:")
    print("  🌐 HTML综合报告")
    print("  📄 JSON数据导出")
    print("  📊 高质量图表")

def demo_configuration():
    """演示配置功能"""
    print_section("配置功能")
    
    print("配置文件: config.py")
    print("可配置项:")
    print("  ⚙️  数据包格式定义")
    print("  ✅ 数据验证规则")
    print("  🎨 图表样式设置")
    print("  📊 分析参数配置")
    
    print("\n自定义配置示例:")
    print("  from config import AnalysisConfig")
    print("  config = AnalysisConfig()")
    print("  config.VALIDATION_CONFIG['uwb']['distance_range'] = (0, 10000)")

def demo_programmatic_usage():
    """演示程序化调用"""
    print_section("程序化调用示例")
    
    print("基本用法:")
    print("""
from uwb_analyzer_enhanced import EnhancedUWBAnalyzer

# 创建分析器
analyzer = EnhancedUWBAnalyzer()

# 解析文件
results = analyzer.parse_multiple_files("*.txt")

# 生成报告
output_files = analyzer.generate_comprehensive_report("output")
""")
    
    print("高级用法:")
    print("""
from config import AnalysisConfig, ANALYSIS_TEMPLATES

# 获取配置
config = AnalysisConfig()

# 查看模板
for name, template in ANALYSIS_TEMPLATES.items():
    print(f"{name}: {template['description']}")
""")

def show_current_status():
    """显示当前状态"""
    print_section("当前状态")
    
    # 检查文件
    files = [
        "uwb_analyzer_enhanced.py",
        "config.py", 
        "run_analysis.py",
        "README.md"
    ]
    
    print("核心文件:")
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✅ {file} ({size} 字节)")
        else:
            print(f"  ❌ {file} (缺失)")
    
    # 检查数据文件
    data_files = [f for f in os.listdir('.') if f.endswith('.txt')]
    print(f"\n数据文件: {len(data_files)} 个")
    for file in data_files[:5]:  # 只显示前5个
        print(f"  📄 {file}")
    if len(data_files) > 5:
        print(f"  ... 还有 {len(data_files) - 5} 个文件")
    
    # 检查输出目录
    if os.path.exists("analysis_output"):
        output_files = os.listdir("analysis_output")
        print(f"\n输出文件: {len(output_files)} 个")
        for file in output_files:
            print(f"  📊 {file}")

def main():
    """主函数"""
    print_header("UWB数据分析工具演示")
    
    print("欢迎使用UWB数据分析工具集！")
    print("本工具集提供了强大的UWB测距数据和加速度数据分析功能。")
    
    # 显示当前状态
    show_current_status()
    
    # 演示各种功能
    demo_basic_usage()
    demo_file_operations()
    demo_output_files()
    demo_data_analysis()
    demo_configuration()
    demo_programmatic_usage()
    
    print_header("快速开始")
    print("要开始分析您的数据，请运行:")
    print("  python uwb_analyzer_enhanced.py")
    print("或者:")
    print("  python run_analysis.py -v")
    
    print("\n更多信息请查看 README.md 文件。")
    print("如有问题，请检查配置文件 config.py。")

if __name__ == "__main__":
    main()
