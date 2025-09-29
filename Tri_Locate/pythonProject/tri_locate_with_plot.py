import math
import matplotlib.pyplot as plt

# 1 宏定义三个距离值
D01 = 400  # 节点0到节点1的距离
D02 = 300  # 节点0到节点2的距离
D12 = 600  # 节点1到节点2的距离

def triangulate_position():
    """
    使用三角形定位算法计算节点1和节点2的坐标
    节点0作为坐标原点(0, 0)
    """
    # 节点1的坐标计算
    x1 = D01
    y1 = 0
    
    # 节点2的坐标计算 - 使用余弦定理
    cos_angle_at_origin = (D01**2 + D02**2 - D12**2) / (2 * D01 * D02)
    angle_at_origin = math.acos(cos_angle_at_origin)
    
    # 节点2的坐标
    x2 = D02 * math.cos(angle_at_origin)
    y2 = D02 * math.sin(angle_at_origin)
    
    return (x1, y1), (x2, y2)

def plot_triangulation():
    """
    绘制三角形定位结果图
    """
    # 计算节点坐标
    pos1, pos2 = triangulate_position()
    x1, y1 = pos1
    x2, y2 = pos2
    
    # 创建图形
    plt.figure(figsize=(12, 10))
    
    # 绘制节点
    plt.plot(0,  0, 'ro', markersize=15, label=f'节点0 (原点) ({0}, {0})', markeredgecolor='black', linewidth=1)
    plt.plot(x1, y1, 'bo', markersize=15, label=f'节点1 ({x1:.1f}, {y1:.1f})', markeredgecolor='black', linewidth=1)
    plt.plot(x2, y2, 'go', markersize=15, label=f'节点2 ({x2:.1f}, {y2:.1f})', markeredgecolor='black', linewidth=1)
    
    # 绘制三角形边
    triangle_x = [0, x1, x2, 0]
    triangle_y = [0, y1, y2, 0]
    plt.plot(triangle_x, triangle_y, 'k-', linewidth=3, alpha=0.8)
    
    # 标注距离 - 位置调整
    mid01_x, mid01_y = (0 + x1)/2, (0 + y1)/2
    mid02_x, mid02_y = (0 + x2)/2, (0 + y2)/2
    mid12_x, mid12_y = (x1 + x2)/2, (y1 + y2)/2
    
    plt.annotate(f'D01={D01}', 
                xy=(mid01_x, mid01_y), 
                xytext=(20, 20), textcoords='offset points',
                fontsize=12, ha='left', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.annotate(f'D02={D02}', 
                xy=(mid02_x, mid02_y), 
                xytext=(20, 20), textcoords='offset points',
                fontsize=12, ha='left',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.annotate(f'D12={D12}', 
                xy=(mid12_x, mid12_y), 
                xytext=(20, 20), textcoords='offset points',
                fontsize=12, ha='left',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    # 绘制坐标轴
    plt.arrow(x2-50, 0, 50, 0, head_width=20, head_length=15, fc='red', ec='red')
    plt.arrow(x2, -20, 0, 20, head_width=20, head_length=15, fc='red', ec='red')
    
    # 设置图形属性
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.axis('equal')
    plt.xlabel('X 坐标', fontsize=14)
    plt.ylabel('Y 坐标', fontsize=14)
    plt.title('三角形定位算法结果\n' + 
              f'D01={D01}, D02={D02}, D12={D12}', fontsize=16)
    plt.legend(fontsize=12, loc='upper right')
    
    # 调整坐标轴范围
    all_x = [0, x1, x2]
    all_y = [0, y1, y2]
    
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    
    x_range = x_max - x_min
    y_range = y_max - y_min
    
    margin_x = x_range * 0.15
    margin_y = y_range * 0.15
    
    plt.xlim(x_min - margin_x, x_max + margin_x)
    plt.ylim(y_min - margin_y, y_max + margin_y + 50)
    
    # 添加文本说明
    plt.text(0.02, 0.98, f'计算结果:\n节点0: (0, 0)\n节点1: ({x1:.1f}, {y1:.1f})\n节点2: ({x2:.1f}, {y2:.1f})', 
             transform=plt.gca().transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.9))
    
    plt.tight_layout()
    
    # 保存图形
    plt.savefig('triangulation_result.png', dpi=300, bbox_inches='tight')
    plt.savefig('triangulation_result.pdf', bbox_inches='tight')
    
    print("图形已保存为:")
    print("  - triangulation_result.png")
    print("  - triangulation_result.pdf")
    
    # 显示图形
    plt.show()

def print_results():
    """
    输出计算结果
    """
    pos1, pos2 = triangulate_position()
    x1, y1 = pos1
    x2, y2 = pos2
    
    print("=" * 60)
    print("三角形定位算法计算结果")
    print("=" * 60)
    print(f"距离定义:")
    print(f"  D01 (节点0到节点1) = {D01}")
    print(f"  D02 (节点0到节点2) = {D02}")
    print(f"  D12 (节点1到节点2) = {D12}")
    print()
    print("坐标结果:")
    print(f"  节点0 = (0.00, 0.00)  [坐标原点]")
    print(f"  节点1 = ({x1:.2f}, {y1:.1f})")
    print(f"  节点2 = ({x2:.2f}, {y2:.1f})")
    print()
    
    # 验证计算结果的准确性
    calc_d01 = math.sqrt((0 - x1)**2 + (0 - y1)**2)
    calc_d02 = math.sqrt((0 - x2)**2 + (0 - y2)**2)
    calc_d12 = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    print("距离验证:")
    print(f"  计算D01 = {calc_d01:.2f} (期望: {D01})")
    print(f"  计算D02 = {calc_d02:.2f} (期望: {D02})")
    print(f"  计算D12 = {calc_d12:.2f} (期望: {D12})")
    
    # 计算角度
    cos_A = (D01**2 + D02**2 - D12**2) / (2 * D01 * D02)
    cos_B = (D01**2 + D12**2 - D02**2) / (2 * D01 * D12)
    cos_C = (D02**2 + D12**2 - D01**2) / (2 * D02 * D12)
    
    angle_A = math.degrees(math.acos(cos_A))
    angle_B = math.degrees(math.acos(cos_B))
    angle_C = math.degrees(math.acos(cos_C))
    
    print()
    print("角度信息:")
    print(f"  角度A (在节点0处) = {angle_A:.2f}°")
    print(f"  角度B (在节点1处) = {angle_B:.2f}°")
    print(f"  角度C (在节点2处) = {angle_C:.2f}°")
    print(f"  角度和 = {angle_A + angle_B + angle_C:.2f}°")
    print("=" * 60)

if __name__ == "__main__":
    # 先输出计算结果
    print_results()
    
    # 然后生成图形
    print("\n正在生成图形...")
    plot_triangulation()
