# -*- coding: utf-8 -*-
"""
简单的Python脚本，专门用于测试win32com和pythoncom模块是否正确安装
直接使用Python运行，避免批处理脚本的编码问题
"""

import sys

print("===== win32com模块测试 ======")
print(f"使用Python版本: {sys.version}")
print(f"Python解释器路径: {sys.executable}")

# 测试win32com.client导入
try:
    import win32com.client
    print("✅ win32com.client 模块已成功导入！")
except ImportError as e:
    print(f"❌ 导入win32com.client失败: {e}")
    print("\n可能的解决方案:")
    print("1. 确保已安装pywin32包")
    print("   运行: pip install pywin32")
    print("2. 检查Python版本与AutoCAD版本是否兼容")
    print("   (32位Python适用于32位AutoCAD，64位Python适用于64位AutoCAD)")

# 测试pythoncom导入
try:
    import pythoncom
    print("✅ pythoncom 模块已成功导入！")
except ImportError as e:
    print(f"❌ 导入pythoncom失败: {e}")
    print("\n可能的解决方案:")
    print("1. 重新安装pywin32包")
    print("   运行: pip uninstall pywin32 && pip install pywin32")

print("\n===== 测试完成 ======")
if 'win32com.client' in sys.modules and 'pythoncom' in sys.modules:
    print("恭喜！所有必需的模块都已成功安装。")
    print("您现在可以运行start_server.bat启动API服务器了。")
else:
    print("请先解决上述问题，然后再次运行此脚本检查。")
    print("或者运行install_basic_deps.bat自动修复依赖问题。")