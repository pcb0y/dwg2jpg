import win32com.client
import pythoncom
import win32com.client
import os
import time

"""
AutoCAD COM接口测试脚本
用于诊断AutoCAD COM操作问题
"""

print("===== AutoCAD COM接口测试开始 =====")

# 初始化COM
pythoncom.CoInitialize()

try:
    print("1. 尝试创建AutoCAD应用实例...")
    acad = win32com.client.Dispatch("AutoCAD.Application")
    print("   ✓ 成功创建AutoCAD应用实例")
    
    # 设置AutoCAD可见，便于调试
    acad.Visible = True
    print("   ✓ 设置AutoCAD为可见模式")
    
    # 获取当前文档数量
    doc_count = acad.Documents.Count
    print(f"   ✓ 当前打开的文档数量: {doc_count}")
    
    # 尝试获取应用版本信息
    try:
        version = acad.Version
        print(f"   ✓ AutoCAD版本: {version}")
    except Exception as version_error:
        print(f"   ✗ 获取版本信息失败: {str(version_error)}")
    
    # 尝试获取支持的打印设备列表
    print("\n2. 尝试获取打印设备列表...")
    try:
        # 创建一个临时文档来获取打印设备
        temp_doc = acad.Documents.Add("acad.dwt")
        plot_configs = temp_doc.PlotConfigurations
        print(f"   ✓ 成功获取打印配置集合，包含 {plot_configs.Count} 个配置")
        
        # 尝试列出前5个配置名称
        print("   ✓ 前5个打印配置名称:")
        for i in range(min(5, plot_configs.Count)):
            try:
                config_name = plot_configs.Item(i).ConfigName
                print(f"     - {config_name}")
            except:
                print("     - [无法获取名称]")
                continue
        
        # 尝试检查特定的PDF打印设备
        pdf_devices = ["DWG To PDF.pc3", "AutoCAD PDF (General Documentation).pc3"]
        print("\n3. 检查常见的PDF打印设备...")
        for device in pdf_devices:
            try:
                # 尝试设置设备名（不实际打印）
                layout = temp_doc.ActiveLayout
                layout.ConfigName = device
                print(f"   ✓ 设备 '{device}' 可用")
            except Exception as dev_error:
                print(f"   ✗ 设备 '{device}' 不可用: {str(dev_error)}")
        
        # 关闭临时文档不保存
        temp_doc.Close(False)
        print("   ✓ 关闭临时文档")
        
    except Exception as plot_error:
        print(f"   ✗ 获取打印设备失败: {str(plot_error)}")
    
    # 尝试打开测试DWG文件（如果存在）
    print("\n4. 尝试打开测试DWG文件...")
    test_dwg_path = os.path.join("temp", "3svjk5zd.dwg")
    if os.path.exists(test_dwg_path):
        test_dwg_path = os.path.abspath(test_dwg_path)
        print(f"   ✓ 测试文件存在: {test_dwg_path}")
        try:
            # 尝试多种方式打开文件
            doc = None
            
            # 方式1: 直接打开
            try:
                doc = acad.Documents.Open(test_dwg_path)
                print("   ✓ 成功打开DWG文件")
            except Exception as direct_error:
                print(f"   ✗ 直接打开失败: {str(direct_error)}")
                
                # 方式2: 尝试使用SendCommand
                try:
                    print("   ✓ 尝试使用SendCommand打开文件")
                    # 先确保有一个活动文档
                    if acad.Documents.Count == 0:
                        temp_doc = acad.Documents.Add("acad.dwt")
                        
                    # 准备路径，需要特别处理反斜杠
                    send_path = test_dwg_path.replace('\\', '\\\\')
                    command = f'_.OPEN "{send_path}"\n'
                    print(f"   ✓ 发送命令: {command}")
                    acad.ActiveDocument.SendCommand(command)
                    time.sleep(2)  # 等待文件打开
                    
                    # 检查是否成功打开
                    if acad.ActiveDocument.Name.lower() == os.path.basename(test_dwg_path).lower():
                        doc = acad.ActiveDocument
                        print("   ✓ 通过SendCommand成功打开DWG文件")
                    else:
                        raise Exception("SendCommand打开失败，文档名称不匹配")
                except Exception as send_cmd_error:
                    print(f"   ✗ SendCommand打开失败: {str(send_cmd_error)}")
                    raise Exception(f"所有打开方式均失败: {str(direct_error)}; {str(send_cmd_error)}")
            
            if doc:
                # 增强ModelSpace访问的错误处理
                try:
                    # 先检查文档是否完全加载
                    doc_name = doc.Name
                    print(f"   ✓ 当前文档: {doc_name}")
                    
                    # 尝试获取模型空间信息
                    model_space = doc.ModelSpace
                    print(f"   ✓ 成功访问ModelSpace")
                    
                    # 检查模型空间中的对象数量
                    try:
                        obj_count = model_space.Count
                        print(f"   ✓ 模型空间对象数量: {obj_count}")
                    except Exception as count_error:
                        print(f"   ✗ 无法获取模型空间对象数量: {str(count_error)}")
                        
                    # 尝试访问模型空间的其他属性
                    try:
                        model_space_name = model_space.Name
                        print(f"   ✓ 模型空间名称: {model_space_name}")
                    except Exception:
                        print(f"   ✓ 无法获取模型空间名称（这是正常的）")
                    
                except Exception as model_space_error:
                    print(f"   ✗ 访问ModelSpace失败: {str(model_space_error)}")
                    print("   ⚠️  错误分析: 这可能是因为文件格式不兼容、文件损坏或AutoCAD版本不匹配")
                    print("   ⚠️  请检查DWG文件是否损坏，尝试用AutoCAD手动打开验证")
                
                # 关闭文档不保存
                try:
                    doc.Close(False)
                    print("   ✓ 关闭DWG文档")
                except Exception as close_error:
                    print(f"   ✗ 关闭DWG文档失败: {str(close_error)}")
        except Exception as open_error:
            print(f"   ✗ 打开DWG文件失败: {str(open_error)}")
            print("   ⚠️  错误分析: Open.ModelSpace错误通常表示AutoCAD无法正确解析该DWG文件")
            print("   ⚠️  可能的解决方法: ")
            print("   ⚠️  1. 确认DWG文件格式与AutoCAD版本兼容")
            print("   ⚠️  2. 检查DWG文件是否损坏")
            print("   ⚠️  3. 尝试用AutoCAD手动打开并另存为兼容性更好的版本")
            print("   ⚠️  4. 确认AutoCAD安装完整")
    else:
        print(f"   ✗ 测试文件不存在: {test_dwg_path}")
        print("   ⚠️  请将测试DWG文件放入temp目录")
    
    print("\n===== AutoCAD COM接口测试完成 =====")
    
finally:
    # 释放COM资源
    pythoncom.CoUninitialize()
    print("\nCOM资源已释放")