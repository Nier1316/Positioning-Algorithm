#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB数据分析批处理脚本
提供命令行界面和自动化分析功能
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uwb_analyzer_enhanced import EnhancedUWBAnalyzer
from config import AnalysisConfig, ANALYSIS_TEMPLATES

class AnalysisRunner:
    """分析运行器"""
    
    def __init__(self):
        self.config = AnalysisConfig()
        self.analyzer = EnhancedUWBAnalyzer()
    
    def run_analysis(self, 
                    file_pattern: str = "*.txt",
                    output_dir: Optional[str] = None,
                    template: str = "basic",
                    verbose: bool = False) -> bool:
        """运行分析"""
        
        if verbose:
            print("UWB数据分析批处理程序")
            print("=" * 50)
            print(f"文件模式: {file_pattern}")
            print(f"输出目录: {output_dir or 'analysis_output'}")
            print(f"分析模板: {template}")
            print()
        
        # 检查模板
        if template not in ANALYSIS_TEMPLATES:
            print(f"错误: 未知的分析模板 '{template}'")
            print(f"可用的模板: {list(ANALYSIS_TEMPLATES.keys())}")
            return False
        
        template_config = ANALYSIS_TEMPLATES[template]
        if verbose:
            print(f"模板描述: {template_config['description']}")
            print()
        
        # 设置输出目录
        if output_dir is None:
            output_dir = self.config.get_output_directory()
        
        try:
            # 运行分析
            start_time = time.time()
            
            # 解析文件
            results = self.analyzer.parse_multiple_files(file_pattern)
            
            if not results:
                print("未找到任何数据文件")
                return False
            
            # 生成报告
            output_files = self.analyzer.generate_comprehensive_report(output_dir)
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            if verbose:
                print("\n" + "=" * 50)
                print("分析完成！")
                print(f"分析耗时: {analysis_time:.2f} 秒")
                print(f"处理文件数: {len(results)}")
                print(f"UWB数据包总数: {len(self.analyzer.uwb_packets)}")
                print(f"加速度数据包总数: {len(self.analyzer.accel_packets)}")
                
                print("\n生成的文件：")
                for file_type, file_path in output_files.items():
                    if isinstance(file_path, list):
                        for f in file_path:
                            print(f"  📊 {file_type}: {f}")
                    else:
                        print(f"  📊 {file_type}: {file_path}")
            
            return True
            
        except Exception as e:
            print(f"分析过程中发生错误: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def list_files(self, pattern: str = "*.txt") -> List[str]:
        """列出匹配的文件"""
        import glob
        files = glob.glob(pattern)
        return sorted(files)
    
    def show_file_info(self, file_path: str) -> bool:
        """显示文件信息"""
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
        
        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 读取文件内容预览
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # 读取前1000个字符
            
            print(f"文件信息: {file_path}")
            print(f"大小: {file_size} 字节")
            print(f"内容预览:")
            print("-" * 40)
            print(content)
            if len(content) == 1000:
                print("...")
            print("-" * 40)
            
            return True
            
        except Exception as e:
            print(f"读取文件时发生错误: {e}")
            return False

def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="UWB数据分析批处理程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_analysis.py                           # 使用默认设置分析所有txt文件
  python run_analysis.py -p "19-24_*.txt"         # 分析特定模式的文件
  python run_analysis.py -o results -t detailed    # 使用详细模板，输出到results目录
  python run_analysis.py --list                    # 列出所有匹配的文件
  python run_analysis.py --info file.txt           # 显示文件信息
        """
    )
    
    parser.add_argument(
        '-p', '--pattern',
        default='*.txt',
        help='文件匹配模式 (默认: *.txt)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='输出目录 (默认: analysis_output)'
    )
    
    parser.add_argument(
        '-t', '--template',
        choices=list(ANALYSIS_TEMPLATES.keys()),
        default='basic',
        help='分析模板 (默认: basic)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出匹配的文件'
    )
    
    parser.add_argument(
        '--info',
        metavar='FILE',
        help='显示指定文件的信息'
    )
    
    parser.add_argument(
        '--templates',
        action='store_true',
        help='显示可用的分析模板'
    )
    
    return parser

def show_templates():
    """显示可用的分析模板"""
    print("可用的分析模板:")
    print("=" * 50)
    for name, config in ANALYSIS_TEMPLATES.items():
        print(f"{name:12} - {config['description']}")
        for key, value in config.items():
            if key != 'description':
                print(f"  {key}: {value}")
        print()

def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    runner = AnalysisRunner()
    
    # 显示模板信息
    if args.templates:
        show_templates()
        return
    
    # 显示文件信息
    if args.info:
        runner.show_file_info(args.info)
        return
    
    # 列出文件
    if args.list:
        files = runner.list_files(args.pattern)
        if files:
            print(f"匹配模式 '{args.pattern}' 的文件:")
            for file in files:
                print(f"  - {file}")
        else:
            print(f"未找到匹配模式 '{args.pattern}' 的文件")
        return
    
    # 运行分析
    success = runner.run_analysis(
        file_pattern=args.pattern,
        output_dir=args.output,
        template=args.template,
        verbose=args.verbose
    )
    
    if success:
        print("\n✅ 分析完成！")
        sys.exit(0)
    else:
        print("\n❌ 分析失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
