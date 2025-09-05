import os
from pathlib import Path

# 根据实际目录结构修正的路径
dwg_path_str = "D:/Data/1/订单其他附件/2025/9/2025-09-02/82503dfe-87ac-4182-8aff-b56a38367d21/三亚店面9-2下单图纸.dwg"

print("=== 测试修正后的路径是否存在 ===")
print(f"修正后的路径: {dwg_path_str}")

# 检查路径是否存在
print(f"Path.exists(): {Path(dwg_path_str).exists()}")
print(f"os.path.exists(): {os.path.exists(dwg_path_str)}")

# 检查路径中的每个部分
print(f"\n=== 检查修正后路径的各部分 ===")
parts = Path(dwg_path_str).parts
current_path = parts[0]  # 驱动器号
print(f"检查驱动器: {current_path} - 是否存在: {os.path.exists(current_path)}")

for part in parts[1:]:
    current_path = os.path.join(current_path, part)
    exists = os.path.exists(current_path)
    is_dir = os.path.isdir(current_path) if exists else False
    is_file = os.path.isfile(current_path) if exists else False
    
    if part == parts[-1]:  # 文件名
        print(f"检查文件: {current_path} - 是否存在: {exists}, 是否为文件: {is_file}")
    else:  # 目录
        print(f"检查目录: {current_path} - 是否存在: {exists}, 是否为目录: {is_dir}")

# 提供解决方案建议
print(f"\n=== 解决方案建议 ===")
print("1. 在main.py中修改路径处理逻辑，添加对'D:/Data/1/'前缀的支持")
print("2. 可以通过以下方式实现：")
print("   a. 修改环境变量DWG_FILE_PREFIX为'D:/Data/1/'")
print("   b. 或者在代码中检测路径并自动添加缺失的'1'目录")
print("   c. 或者修改数据库查询逻辑，确保返回的路径包含正确的前缀")
print("3. 推荐的解决方案是通过环境变量配置，这样不需要修改代码就能适应不同环境")