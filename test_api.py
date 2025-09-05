import requests
import os
from pathlib import Path
import time

# API服务器地址
API_URL = "http://localhost:8000"

print("测试API服务...")
print(f"API服务器地址: {API_URL}")

# 1. 测试根端点
try:
    print("\n1. 测试根端点 /")
    response = requests.get(f"{API_URL}/")
    if response.status_code == 200:
        print(f"✅ 根端点访问成功")
        print(f"响应内容: {response.json()}")
    else:
        print(f"❌ 根端点访问失败: 状态码 {response.status_code}")
except Exception as e:
    print(f"❌ 根端点访问出错: {str(e)}")

# 2. 检查是否存在测试DWG文件
test_dwg_path = Path('test_output/test_drawing.dxf')
if not test_dwg_path.exists():
    print("\n⚠️ 未找到测试DWG/DXF文件，无法测试文件上传转换功能")
else:
    # 3. 测试DWG到JPG转换端点
    try:
        print("\n3. 测试DWG到JPG转换端点 /convert/dwg-to-jpg")
        files = {'file': open(test_dwg_path, 'rb')}
        response = requests.post(f"{API_URL}/convert/dwg-to-jpg", files=files)
        
        if response.status_code == 200:
            print(f"✅ 文件转换API调用成功")
            result = response.json()
            print(f"转换结果: {result}")
        else:
            print(f"❌ 文件转换API调用失败: 状态码 {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 文件转换API调用出错: {str(e)}")

# 4. 测试转换历史记录端点
try:
    print("\n4. 测试转换历史记录端点 /convert/history")
    response = requests.get(f"{API_URL}/convert/history")
    if response.status_code == 200:
        print(f"✅ 转换历史记录访问成功")
        history = response.json()
        print(f"历史记录数量: {len(history)}")
        if len(history) > 0:
            print(f"最近一条记录: {history[0]}")
    else:
        print(f"❌ 转换历史记录访问失败: 状态码 {response.status_code}")
except Exception as e:
    print(f"❌ 转换历史记录访问出错: {str(e)}")

print("\nAPI测试完成！")