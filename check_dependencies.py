#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单的依赖验证脚本，用于测试关键依赖是否正确安装"""

import sys

# 要检查的依赖列表
dependencies = [
    ('win32com.client', 'pywin32'),
    ('pythoncom', 'pywin32'),
    ('fastapi', 'fastapi'),
    ('uvicorn', 'uvicorn'),
    ('pyautocad', 'pyautocad'),
    ('reportlab', 'reportlab')
]

print("===== 依赖检查结果 =====")
all_installed = True

for module_name, package_name in dependencies:
    try:
        __import__(module_name)
        print(f"✅ {module_name} 已成功导入 (来自 {package_name} 包)")
    except ImportError:
        print(f"❌ {module_name} 未安装! 请运行: pip install {package_name}")
        all_installed = False

print("======================")

if all_installed:
    print("恭喜！所有关键依赖都已成功安装。")
    print("您现在可以运行 start_server.bat 启动API服务器了。")
else:
    print("请安装缺失的依赖，然后再次运行此脚本检查。")
    print("或者运行 fix_dependencies.bat 自动修复所有依赖问题。")

print("\n注意：如果遇到中文显示问题，请确保您的命令行使用UTF-8编码。")
print("在Windows命令提示符中，可以输入: chcp 65001 来切换到UTF-8编码。")