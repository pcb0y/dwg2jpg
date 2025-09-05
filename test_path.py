import os
from pathlib import Path

# 原始文件路径
dwg_path_str = "D:/Data/订单其他附件/2025/9/2025-09-02/82503dfe-87ac-4182-8aff-b56a38367d21/三亚店面9-2下单图纸.dwg"

# 方法1: 使用Path对象的原始路径
print("=== 测试路径是否存在 ===")
dwg_file_path = Path(dwg_path_str)
print(f"原始路径: {dwg_path_str}")
print(f"Path.exists(): {dwg_file_path.exists()}")

# 方法2: 使用os.path模块
print(f"\nos.path.exists(): {os.path.exists(dwg_path_str)}")
print(f"os.path.isfile(): {os.path.isfile(dwg_path_str) if os.path.exists(dwg_path_str) else 'N/A'}")

# 方法3: 规范化路径（处理混合斜杠）
normalized_path = os.path.normpath(dwg_path_str)
print(f"\n=== 规范化路径测试 ===")
print(f"规范化路径: {normalized_path}")
print(f"规范化后是否存在: {os.path.exists(normalized_path)}")

# 方法4: 转换为Windows风格路径（全部使用反斜杠）
windows_style_path = dwg_path_str.replace('/', '\\')
print(f"\n=== Windows风格路径测试 ===")
print(f"Windows风格路径: {windows_style_path}")
print(f"Windows风格路径是否存在: {os.path.exists(windows_style_path)}")

# 检查路径中的每个部分是否存在
def check_path_parts(path):
    """检查路径中的每个部分是否存在"""
    print(f"\n=== 路径各部分检查 ===")
    parts = Path(path).parts
    current_path = parts[0]  # 驱动器号
    print(f"检查驱动器: {current_path} - 是否存在: {os.path.exists(current_path)}")
    
    # 检查每个子目录
    for part in parts[1:-1]:  # 排除文件名
        current_path = os.path.join(current_path, part)
        exists = os.path.exists(current_path)
        is_dir = os.path.isdir(current_path) if exists else False
        print(f"检查目录: {current_path} - 是否存在: {exists}, 是否为目录: {is_dir}")
    
    # 检查完整路径
    full_path = os.path.join(current_path, parts[-1])
    exists = os.path.exists(full_path)
    is_file = os.path.isfile(full_path) if exists else False
    print(f"检查完整文件路径: {full_path} - 是否存在: {exists}, 是否为文件: {is_file}")

# 执行路径各部分检查
check_path_parts(dwg_path_str)

# 提供可能的解决方案建议
print(f"\n=== 可能的解决方案 ===")
if not os.path.exists('D:'):
    print("1. 确认D盘是否存在或可访问")
elif not os.path.exists('D:/Data'):
    print("1. 确认D:/Data目录是否存在")
    print("2. 检查路径中的目录结构是否正确")
    print("3. 验证路径中的GUID和日期目录是否存在")
else:
    print("1. 检查完整路径中的文件名拼写是否正确")
    print("2. 确认文件扩展名是.dwg而不是.DWG或其他大小写变体")
    print("3. 检查文件权限是否允许访问")
    print("4. 尝试手动创建测试文件到相似路径，验证代码是否能正确识别")

# 添加环境变量检查建议
print(f"\n=== 环境变量建议 ===")
print("如果使用环境变量设置路径前缀，请确保:")
print("1. 环境变量正确设置（如DWG_FILE_PREFIX）")
print("2. 路径前缀与数据库中的路径拼接正确")
print("3. 路径中不包含多余的斜杠或缺失必要的斜杠")