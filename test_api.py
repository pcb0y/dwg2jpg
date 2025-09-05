import requests
import sys
import os
import requests
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8007"


def test_api_connection():
    """测试API连接是否正常"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ API连接成功！")
            print(f"API信息: {response.json()}")
            return True
        else:
            print(f"❌ API连接失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API连接失败: {str(e)}")
        print("请确认API服务器正在运行。")
        return False


def convert_dwg_to_pdf(dwg_file_path):
    """测试DWG到PDF转换功能"""
    if not os.path.exists(dwg_file_path):
        print(f"❌ 文件不存在: {dwg_file_path}")
        return False

    if not dwg_file_path.lower().endswith(".dwg"):
        print("❌ 不是DWG文件，请提供有效的DWG文件。")
        return False

    try:
        print(f"正在上传文件: {dwg_file_path}")
        with open(dwg_file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/convert/dwg-to-pdf", files=files)
            
        if response.status_code == 200:
            # 保存转换后的PDF文件
            pdf_file_path = Path(dwg_file_path).stem + ".pdf"
            with open(pdf_file_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ 转换成功！PDF文件已保存为: {pdf_file_path}")
            return True
        else:
            print(f"❌ 转换失败: 状态码 {response.status_code}")
            try:
                print(f"错误信息: {response.json()}")
            except:
                print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 转换过程中发生错误: {str(e)}")
        return False


def main():
    """主函数"""
    print("DWG to PDF Converter API 测试工具")
    print("=" * 50)
    
    # 测试API连接
    if not test_api_connection():
        print("请先启动API服务器，然后再运行此测试脚本。")
        print("可以使用以下命令启动服务器:")
        print("  1. python main.py")
        print("  2. uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("  3. 双击运行start_server.bat")
        sys.exit(1)
    
    print("=" * 50)
    print("注意：要测试转换功能，请提供DWG文件路径作为参数。")
    print("例如: python test_api.py path/to/your/file.dwg")
    print("=" * 50)
    
    # 检查是否提供了DWG文件路径
    if len(sys.argv) > 1:
        dwg_file_path = sys.argv[1]
        convert_dwg_to_pdf(dwg_file_path)
    else:
        print("未提供DWG文件路径，仅测试了API连接。")


if __name__ == "__main__":
    main()