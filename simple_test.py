import os
import sys
from pathlib import Path
from converter import converter_dwg_to_jpg

# 检查是否存在测试DWG文件
TEST_DWG_PATH = Path('test_output/test_drawing.dxf')  # 使用DXF文件作为测试
if not TEST_DWG_PATH.exists():
    print(f"错误：未找到测试文件 {TEST_DWG_PATH}")
    print("请确保测试文件存在或修改脚本中的文件路径")
    sys.exit(1)

# 创建输出目录
OUTPUT_DIR = Path('test_output')
OUTPUT_DIR.mkdir(exist_ok=True)

# 设置输出JPG文件路径
OUTPUT_JPG = OUTPUT_DIR / 'test_result.jpg'

print(f"测试DWG到JPG转换功能")
print(f"输入文件: {TEST_DWG_PATH}")
print(f"输出文件: {OUTPUT_JPG}")

# 执行转换
try:
    success = converter_dwg_to_jpg(str(TEST_DWG_PATH), str(OUTPUT_JPG))
    
    if success and OUTPUT_JPG.exists():
        file_size = OUTPUT_JPG.stat().st_size
        print(f"✅ 转换成功! 生成的JPG文件大小: {file_size} 字节")
        print(f"生成的文件路径: {OUTPUT_JPG}")
    else:
        print(f"❌ 转换失败或文件未生成")
        if not OUTPUT_JPG.exists():
            print(f"文件不存在: {OUTPUT_JPG}")
        sys.exit(1)

except Exception as e:
    print(f"❌ 转换过程中发生错误: {str(e)}")
    sys.exit(1)

print("\n测试完成！")