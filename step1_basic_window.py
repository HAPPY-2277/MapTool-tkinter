"""
空间数据质量检查工具 - 第一步：创建基本窗口
===========================================
学习目标：
1. 创建一个tkinter窗口
2. 添加菜单栏
3. 添加状态栏
"""

import tkinter as tk
from tkinter import ttk, messagebox

# 创建主窗口
root = tk.Tk()

# 设置窗口标题
root.title("空间数据质量检查工具")

# 设置窗口大小（宽x高）
root.geometry("800x600")

# 设置窗口最小尺寸
root.minsize(600, 400)


# ========== 创建菜单栏 ==========
# 创建菜单栏对象
menubar = tk.Menu(root)

# 创建"文件"菜单
file_menu = tk.Menu(menubar, tearoff=0)  # tearoff=0 表示不能撕下来
file_menu.add_command(label="打开文件", command=lambda: messagebox.showinfo("提示", "打开文件功能待实现"))
file_menu.add_command(label="保存", command=lambda: messagebox.showinfo("提示", "保存功能待实现"))
file_menu.add_separator()  # 添加分隔线
file_menu.add_command(label="退出", command=root.quit)

# 把"文件"菜单添加到菜单栏
menubar.add_cascade(label="文件", menu=file_menu)

# 创建"帮助"菜单
help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="关于", command=lambda: messagebox.showinfo("关于", "空间数据质量检查工具 v1.0"))
menubar.add_cascade(label="帮助", menu=help_menu)

# 把菜单栏设置到窗口
root.config(menu=menubar)


# ========== 创建状态栏 ==========
# 状态栏就是一个Label，放在窗口底部
status_bar = tk.Label(root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
# bd=1 边框宽度, relief=tk.SUNKEN 凹陷效果, anchor=tk.W 文字左对齐
status_bar.pack(side=tk.BOTTOM, fill=tk.X)  # 放在底部，横向填充


# ========== 创建中心区域 ==========
# 先创建一个Frame作为容器
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)  # 填充整个空间

# 左侧：图片显示区域
left_frame = tk.Frame(main_frame, bg="white")
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 添加一个Label显示提示文字
label_hint = tk.Label(left_frame, text="请打开地图数据文件", font=("Arial", 14), bg="white")
label_hint.pack(expand=True)

# 右侧：错误列表面板
right_frame = tk.Frame(main_frame, width=250, bg="#f0f0f0")
right_frame.pack(side=tk.RIGHT, fill=tk.Y)
right_frame.pack_propagate(False)  # 固定宽度，不被内容撑开

# 错误列表标题
label_title = tk.Label(right_frame, text="错误记录列表", font=("Arial", 11, "bold"), bg="#f0f0f0")
label_title.pack(pady=10)

# 错误列表（使用Listbox）
error_listbox = tk.Listbox(right_frame, font=("Arial", 10))
error_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


# ========== 运行主循环 ==========
# 这是tkinter程序必须的最后一行，让窗口保持显示
root.mainloop()
