import os

# 检查D:\Data目录下的内容
def check_data_directory_structure():
    """检查D:\Data目录下的实际内容，确认正确的目录结构"""
    base_dir = "D:\\Data"
    
    print(f"=== 检查D:\\Data目录结构 ===")
    
    # 检查D盘是否存在
    if not os.path.exists("D:"):
        print("错误: D盘不存在或无法访问")
        return
    
    # 检查Data目录是否存在
    if not os.path.exists(base_dir):
        print(f"错误: {base_dir} 目录不存在")
        return
    
    # 列出D:\Data目录下的所有子目录和文件
    print(f"\nD:\\Data目录下的内容:")
    try:
        items = os.listdir(base_dir)
        if not items:
            print(f"  {base_dir} 目录为空")
        else:
            for item in items:
                item_path = os.path.join(base_dir, item)
                is_dir = os.path.isdir(item_path)
                item_type = "目录" if is_dir else "文件"
                print(f"  [{item_type}] {item}")
    except PermissionError:
        print(f"错误: 没有权限访问 {base_dir} 目录")
    except Exception as e:
        print(f"错误: 读取 {base_dir} 目录内容时出错: {str(e)}")
    
    # 搜索可能与"订单"相关的目录
    print(f"\n=== 搜索D:\\Data目录下与'订单'相关的目录 ===")
    try:
        order_dirs = []
        for root, dirs, files in os.walk(base_dir):
            # 限制搜索深度为2层，避免搜索整个磁盘
            if root.count(os.sep) - base_dir.count(os.sep) < 3:
                for dir_name in dirs:
                    if "订单" in dir_name:
                        full_path = os.path.join(root, dir_name)
                        order_dirs.append(full_path)
        
        if not order_dirs:
            print("  未找到与'订单'相关的目录")
        else:
            for dir_path in order_dirs:
                print(f"  找到: {dir_path}")
    except PermissionError:
        print(f"错误: 没有权限遍历 {base_dir} 目录")
    except Exception as e:
        print(f"错误: 遍历时出错: {str(e)}")
    
    # 提供建议
    print(f"\n=== 解决DWG文件路径问题的建议 ===")
    print("1. 根据上面的检查结果，确认正确的目录名称")
    print("2. 如果实际目录名称与代码中使用的不同，请更新代码中的路径")
    print("3. 如果目录结构完全不同，请检查数据库中存储的文件路径是否正确")
    print("4. 考虑在系统中设置正确的DWG_FILE_PREFIX环境变量")
    print("5. 如果文件确实存在但路径无法识别，请尝试使用绝对路径或UNC路径格式")

if __name__ == "__main__":
    check_data_directory_structure()