"""
空间数据质量检查工具 - 第三步：点击标记错误
===========================================
学习目标：
1. 绑定鼠标点击事件
2. 在Canvas上绘制标记点
3. 记录错误信息到列表
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import json
import os
from datetime import datetime


class ErrorRecord:
    """错误记录类 - 存储单条错误信息"""
    
    def __init__(self, error_id, error_type, description, x, y, created_time=None):
        self.error_id = error_id          # 错误编号
        self.error_type = error_type      # 错误类型
        self.description = description    # 错误描述
        self.x = x                        # X坐标
        self.y = y                        # Y坐标
        self.created_time = created_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self):
        """转换为字典，用于保存为JSON"""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "description": self.description,
            "x": self.x,
            "y": self.y,
            "created_time": self.created_time
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            error_id=data["error_id"],
            error_type=data["error_type"],
            description=data["description"],
            x=data["x"],
            y=data["y"],
            created_time=data.get("created_time")
        )


class MapQCApp:
    """主应用程序类"""
    
    # 错误类型对应的颜色
    ERROR_COLORS = {
        "几何错误": "#FF0000",    # 红色
        "属性错误": "#00AA00",    # 绿色
        "拓扑错误": "#0000FF",    # 蓝色
        "坐标错误": "#FFAA00",    # 橙色
        "其他": "#888888"         # 灰色
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("空间数据质量检查工具")
        self.root.geometry("900x600")
        self.root.minsize(300, 200)
        
        # 数据存储
        self.current_image = None
        self.current_image_path = None
        self.photo = None
        self.errors = []           # 存储所有错误记录
        self.error_counter = 0     # 错误编号计数器
        self.is_marking_mode = False  # 是否处于标记模式
        self.mouse_x, self.mouse_y = 0,0
        self.img_x, self.img_y = 0,0
        self.img_id = None
        self.width, self.height = 0,0
        
        # 创建界面
        self._create_menu()
        self._create_toolbar()
        self._create_status_bar()
        self._create_main_area()
        self._bind_events()
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开图片", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="保存错误记录", command=self.save_errors, accelerator="Ctrl+S")
        file_menu.add_command(label="加载错误记录", command=self.load_errors)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="清除所有标记", command=self.clear_all_errors)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
        self.root.bind("<Control-o>", lambda e: self.open_image())
        self.root.bind("<Control-s>", lambda e: self.save_errors())
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # 打开文件按钮
        tk.Button(toolbar, text="📁 打开", command=self.open_file,bg="#f4c542").pack(side=tk.LEFT, padx=2, pady=2)
        
        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # 标记模式按钮
        self.mark_btn = tk.Button(toolbar, text="🔴 开始标记", command=self.toggle_marking_mode, bg="#4caf50")
        self.mark_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # 保存按钮
        tk.Button(toolbar, text="💾 保存", command=self.save_errors).pack(side=tk.LEFT, padx=2, pady=2)
        
        # 清除按钮
        tk.Button(toolbar, text="🗑️ 清除全部", command=self.clear_all_errors).pack(side=tk.LEFT, padx=2, pady=2)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = tk.Label(self.root, text="就绪 | 点击'开始标记'按钮进入标记模式", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_main_area(self):
        """创建主区域"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：显示区域
        self.display_frame = tk.Frame(self.main_frame)
        self.display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建Canvas用于显示图片
        self.canvas = tk.Canvas(self.display_frame, bg="#e0e0e0", cursor="arrow")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 提示文字
        self.hint_text = self.canvas.create_text(
            400, 300,
            text="请打开地图数据文件\n\n支持格式: JPG, PNG, BMP, TIF, TXT, CSV",
            font=("Arial", 14),
            fill="gray",
            tags="hint"
        )
        
        # 文本显示区域
        self.text_frame = tk.Frame(self.display_frame)
        self.text_widget = tk.Text(self.text_frame, wrap=tk.NONE, font=("Consolas", 10))
        scroll_y = tk.Scrollbar(self.text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        scroll_x = tk.Scrollbar(self.text_frame, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        self.text_widget.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 右侧：错误列表
        self._create_error_panel()
    
    def _create_error_panel(self):
        """创建错误列表面板"""
        self.right_frame = tk.Frame(self.main_frame, width=300, bg="#f5f5f5")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False)
        
        # 标题和计数
        title_frame = tk.Frame(self.right_frame, bg="#f5f5f5")
        title_frame.pack(fill=tk.X, pady=10, padx=5)
        
        tk.Label(title_frame, text="错误记录列表", font=("Arial", 12, "bold"), bg="#f5f5f5").pack(side=tk.LEFT)
        self.count_label = tk.Label(title_frame, text="(0)", font=("Arial", 12), bg="#f5f5f5", fg="gray")
        self.count_label.pack(side=tk.LEFT, padx=5)
        
        # 筛选区域
        filter_frame = tk.Frame(self.right_frame, bg="#f5f5f5")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(filter_frame, text="类型:", bg="#f5f5f5").pack(side=tk.LEFT)
        self.filter_type = ttk.Combobox(filter_frame, values=["全部", "几何错误", "属性错误", "拓扑错误", "坐标错误", "其他"], width=10)
        self.filter_type.set("全部")
        self.filter_type.pack(side=tk.LEFT, padx=5)
        self.filter_type.bind("<<ComboboxSelected>>", self._filter_errors)
        
        # 错误列表
        list_frame = tk.Frame(self.right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.error_listbox = tk.Listbox(list_frame, font=("Arial", 10), selectmode=tk.SINGLE)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.error_listbox.yview)
        self.error_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.error_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 绑定列表点击事件
        self.error_listbox.bind("<<ListboxSelect>>", self._on_error_select)
        self.error_listbox.bind("<Double-Button-1>", self._on_error_double_click)
        
        # 按钮区域
        btn_frame = tk.Frame(self.right_frame, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, padx=5, pady=10)
        
        tk.Button(btn_frame, text="删除", command=self.delete_selected_error, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="定位", command=self.locate_selected_error, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="导出", command=self.export_errors, width=8).pack(side=tk.LEFT, padx=2)
    
    def _bind_events(self):
        """绑定事件"""
        # 绑定Canvas鼠标点击事件
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        
        # 绑定窗口大小变化事件
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        #绑定鼠标滚轮滚动事件
        self.canvas.bind("<MouseWheel>", self._on_resize_image)

        self.canvas.bind("<Button-3>", self._on_get_mouse_pos)
        self.canvas.bind("<B3-Motion>", self._on_move_image)
    
    # ========== 核心功能方法 ==========
    
    def toggle_marking_mode(self):
        """切换标记模式"""
        self.is_marking_mode = not self.is_marking_mode
        
        if self.is_marking_mode:
            self.mark_btn.config(text="⭕ 停止标记", bg="#ff9999")
            self.canvas.config(cursor="crosshair")  # 十字光标
            self.status_bar.config(text="标记模式已开启 | 点击图片上的位置标记错误")
        else:
            self.mark_btn.config(text="🔴 开始标记", bg="#4caf50")
            self.canvas.config(cursor="arrow")
            self.status_bar.config(text="标记模式已关闭")
    
    def _on_canvas_click(self, event):
        """Canvas点击事件处理"""
        if not self.is_marking_mode:
            return
        
        if not self.current_image:
            messagebox.showwarning("提示", "请先打开图片文件")
            return
        
        # 获取点击位置
        x, y = event.x, event.y
        
        # 弹出对话框输入错误信息
        self._show_error_dialog(x, y)
    
    def _show_error_dialog(self, x, y):
        """显示错误输入对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加错误记录")
        dialog.geometry("450x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.geometry(f"+{self.root.winfo_x() + 200}+{self.root.winfo_y() + 150}")
        
        # 坐标显示
        coord_frame = tk.Frame(dialog)
        coord_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(coord_frame, text=f"点击位置: X={x}, Y={y}", font=("Arial", 10, "bold")).pack()
        
        # 错误类型
        type_frame = tk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(type_frame, text="错误类型:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        type_var = tk.StringVar(value="几何错误")
        type_combo = ttk.Combobox(type_frame, textvariable=type_var, values=[
            "几何错误", "属性错误", "拓扑错误", "坐标错误", "其他"
        ], width=20)
        type_combo.pack(side=tk.LEFT)
        
        # 错误描述
        desc_frame = tk.Frame(dialog)
        desc_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(desc_frame, text="错误描述:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        desc_entry = tk.Entry(desc_frame, width=30)
        desc_entry.pack(side=tk.LEFT)
        desc_entry.focus_set()
        
        def save():
            error_type = type_var.get()
            description = desc_entry.get().strip()
            
            if not description:
                messagebox.showwarning("警告", "请输入错误描述", parent=dialog)
                return
            
            # 生成错误编号
            self.error_counter += 1
            date_str = datetime.now().strftime("%Y%m%d")
            error_id = f"ERR-{date_str}-{self.error_counter:04d}"
            
            # 创建错误记录
            error = ErrorRecord(error_id, error_type, description, x, y)
            self.errors.append(error)
            
            # 在Canvas上绘制标记
            self._draw_error_marker(error)
            
            # 更新列表
            self._update_error_list()
            
            # 更新状态
            self.status_bar.config(text=f"已添加错误: {error_id}")
            
            dialog.destroy()
        
        # 按钮
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="确定", command=save, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=10)
        
        # 回车键确认
        dialog.bind("<Return>", lambda e: save())
    
    def _draw_error_marker(self, error, highlight=False):
        """在Canvas上绘制错误标记"""
        color = self.ERROR_COLORS.get(error.error_type, "#FF0000")
        size = 12 if not highlight else 16
        
        # 绘制圆形标记
        marker_id = self.canvas.create_oval(
            error.x - size, error.y - size,
            error.x + size, error.y + size,
            fill=color, outline="white" if highlight else "black",
            width=2 if highlight else 1,
            tags=(f"error_{error.error_id}", "error_marker")
        )
        
        # 绘制错误编号
        text_id = self.canvas.create_text(
            error.x, error.y,
            text=str(self.errors.index(error) + 1),
            fill="white",
            font=("Arial", 8, "bold"),
            tags=(f"error_{error.error_id}", "error_marker")
        )
        
        return marker_id, text_id
    
    def _update_error_list(self):
        """更新错误列表显示"""
        self.error_listbox.delete(0, tk.END)
        
        filter_type = self.filter_type.get()
        
        for i, error in enumerate(self.errors):
            if filter_type != "全部" and error.error_type != filter_type:
                continue
            
            # 格式化显示
            display_text = f"{i+1}. [{error.error_type}] {error.description[:20]}"
            if len(error.description) > 20:
                display_text += "..."
            
            self.error_listbox.insert(tk.END, display_text)
        
        # 更新计数
        self.count_label.config(text=f"({len(self.errors)})")
    
    def _filter_errors(self, event=None):
        """筛选错误"""
        self._update_error_list()
    
    def _on_error_select(self, event):
        """错误列表选中事件"""
        selection = self.error_listbox.curselection()
        if not selection:
            return
        
        # 获取选中的索引
        idx = selection[0]
        
        # 找到对应的错误记录
        filter_type = self.filter_type.get()
        visible_errors = [e for e in self.errors if filter_type == "全部" or e.error_type == filter_type]
        
        if idx < len(visible_errors):
            error = visible_errors[idx]
            self._highlight_error(error)
    
    def _on_error_double_click(self, event):
        """双击错误列表项"""
        self.locate_selected_error()
    
    def _highlight_error(self, error):
        """高亮显示选中的错误"""
        # 清除之前的高亮
        self.canvas.delete("highlight")
        
        # 重绘所有标记
        self.canvas.delete("error_marker")
        for e in self.errors:
            is_highlight = (e.error_id == error.error_id)
            self._draw_error_marker(e, highlight=is_highlight)
        
        # 更新状态栏
        self.status_bar.config(text=f"错误: {error.error_id} | 类型: {error.error_type} | 位置: ({error.x}, {error.y})")
    
    def locate_selected_error(self):
        """定位到选中的错误"""
        selection = self.error_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条错误记录")
            return
        
        idx = selection[0]
        filter_type = self.filter_type.get()
        visible_errors = [e for e in self.errors if filter_type == "全部" or e.error_type == filter_type]
        
        if idx < len(visible_errors):
            error = visible_errors[idx]
            self._highlight_error(error)
    
    def delete_selected_error(self):
        """删除选中的错误"""
        selection = self.error_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条错误记录")
            return
        
        idx = selection[0]
        filter_type = self.filter_type.get()
        visible_errors = [e for e in self.errors if filter_type == "全部" or e.error_type == filter_type]
        
        if idx < len(visible_errors):
            error = visible_errors[idx]
            
            # 确认删除
            if messagebox.askyesno("确认", f"确定要删除错误记录 {error.error_id} 吗？"):
                self.errors.remove(error)
                
                # 重绘所有标记
                self.canvas.delete("error_marker")
                for e in self.errors:
                    self._draw_error_marker(e)
                
                # 更新列表
                self._update_error_list()
    
    def clear_all_errors(self):
        """清除所有错误标记"""
        if not self.errors:
            return
        
        if messagebox.askyesno("确认", "确定要清除所有错误标记吗？"):
            self.errors.clear()
            self.error_counter = 0
            self.canvas.delete("error_marker")
            self._update_error_list()
            self.status_bar.config(text="已清除所有错误标记")
    
    # ========== 文件操作 ==========

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Choose File",
            filetypes=[
                ("Picture or Text", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.txt *.csv"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']:
            self.open_image(file_path)
        else:
            self.open_text(file_path)

    def open_image(self, file_path):
        try:
            # 使用PIL打开图片
            img = Image.open(file_path)

            # 获取Canvas大小
            self.canvas.update()
            self.canvas.update()
            self.width, self.height = self.canvas.winfo_width(), self.canvas.winfo_height()

            # 如果图片太大，按比例缩小
            img_width, img_height = img.size
            scale = min(self.width / img_width, self.height / img_height, 1.0)

            if scale < 1.0:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            # 转换为tkinter可用的格式
            self.photo = ImageTk.PhotoImage(img)

            # 清除提示文字
            self.canvas.delete(self.hint_text)

            # 在Canvas中心显示图片
            self.img_id=self.canvas.create_image(
                self.width // 2, self.height // 2,
                image=self.photo,
                anchor=tk.CENTER,
                tags="image"
            )

            # 保存当前图片信息
            self.current_image = img
            self.current_image_path = file_path
            self.img_x, self.img_y = self.width // 2, self.height // 2

            # 更新状态栏
            self.status_bar.config(text=f"Already open: {file_path} | Size: {img_width}x{img_height}")

            # 隐藏文本区域，显示Canvas
            self.text_frame.pack_forget()
            self.canvas.pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"Can't open the file:\n{str(e)}")

    def open_text(self, file_path):
        try:
            self.get_text(file_path, 'utf-8')
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                self.get_text(file_path, 'gbk')
            except Exception as e:
                messagebox.showerror("Error", f"Can't open the file:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Can't open the file:\n{str(e)}")

    def get_text(self, file_path, codemode):
        with open(file_path, 'r', encoding=codemode) as f:
            content = f.read()
        # 添加行号
        lines = content.split('\n')
        numbered_content = ''
        for i, line in enumerate(lines, 1):
            numbered_content += f"{i:5d} | {line}\n"

        # 显示文本
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, numbered_content)

        # 隐藏Canvas，显示文本区域
        self.canvas.pack_forget()
        self.text_frame.pack(fill=tk.BOTH, expand=True)

        # 更新状态栏
        self.status_bar.config(text=f"Already open: {file_path} | lines: {len(lines)}")

    def save_errors(self):
        """保存错误记录到JSON文件"""
        if not self.errors:
            messagebox.showwarning("提示", "没有错误记录可保存")
            return
        
        # 默认文件名
        default_name = "error_records.json"
        if self.current_image_path:
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            default_name = f"{base_name}_errors.json"
        
        file_path = filedialog.asksaveasfilename(
            title="保存错误记录",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            data = {
                "version": "1.0",
                "saved_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source_file": self.current_image_path,
                "errors": [e.to_dict() for e in self.errors]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.status_bar.config(text=f"已保存: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", f"错误记录已保存到:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{str(e)}")
    
    def load_errors(self):
        """从JSON文件加载错误记录"""
        file_path = filedialog.askopenfilename(
            title="加载错误记录",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清除现有错误
            self.errors.clear()
            self.canvas.delete("error_marker")
            
            # 加载错误记录
            for error_data in data.get("errors", []):
                error = ErrorRecord.from_dict(error_data)
                self.errors.append(error)
                
                # 提取编号中的计数器值
                if error.error_id.startswith("ERR-"):
                    try:
                        counter = int(error.error_id.split("-")[-1])
                        self.error_counter = max(self.error_counter, counter)
                    except:
                        pass
            
            # 重绘所有标记
            for error in self.errors:
                self._draw_error_marker(error)
            
            self._update_error_list()
            self.status_bar.config(text=f"已加载 {len(self.errors)} 条错误记录")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载失败:\n{str(e)}")
    
    def export_errors(self):
        """导出错误记录为文本文件"""
        if not self.errors:
            messagebox.showwarning("提示", "没有错误记录可导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="导出错误记录",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("空间数据质量检查报告\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"源文件: {self.current_image_path or '未知'}\n")
                f.write(f"错误总数: {len(self.errors)}\n\n")
                f.write("-" * 60 + "\n")
                f.write("错误详情:\n")
                f.write("-" * 60 + "\n\n")
                
                for i, error in enumerate(self.errors, 1):
                    f.write(f"【错误 {i}】\n")
                    f.write(f"  编号: {error.error_id}\n")
                    f.write(f"  类型: {error.error_type}\n")
                    f.write(f"  描述: {error.description}\n")
                    f.write(f"  位置: ({error.x}, {error.y})\n")
                    f.write(f"  时间: {error.created_time}\n\n")
            
            self.status_bar.config(text=f"已导出: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", f"错误报告已导出到:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败:\n{str(e)}")
    
    def _on_canvas_resize(self, event):
        if self.photo and self.current_image:
            dx=self.img_x-self.width//2
            dy=self.img_y-self.height//2

            self.canvas.update()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            scale_x = canvas_width / self.width
            scale_y = canvas_height / self.height

            self.img_x=(int)(canvas_width//2 + scale_x * dx)
            self.img_y=(int)(canvas_height//2 + scale_y * dy)

            self.photo = ImageTk.PhotoImage(self.current_image)
            self.img_id=self.canvas.create_image(
                self.img_x,self.img_y,
                image=self.photo,
                anchor=tk.CENTER,
                tags="image"
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.canvas.update()
            self.width, self.height = self.canvas.winfo_width(), self.canvas.winfo_height()

    def _on_resize_image(self, event):
        delta = event.delta
        scale = 1

        if delta < 0:
            scale /= 1.1
        else:
            scale *= 1.1

        img_width, img_height = self.current_image.size
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        self.current_image = self.current_image.resize((new_width, new_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.current_image)

        self.canvas.delete(self.hint_text)
        self.img_id=self.canvas.create_image(
            self.img_x, self.img_y,
            image=self.photo,
            anchor=tk.CENTER,
            tags="image"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _on_get_mouse_pos(self, event):
        self.mouse_x, self.mouse_y = event.x, event.y

    def _on_move_image(self, event):
        dx, dy = event.x - self.mouse_x, event.y - self.mouse_y

        self.canvas.move(self.img_id, dx, dy)
        self.mouse_x, self.mouse_y = event.x, event.y
        self.img_x, self.img_y = self.img_x+dx, self.img_y+dy
        pass

    def show_help(self):
        """显示使用说明"""
        help_text = """
空间数据质量检查工具 - 使用说明

【基本操作】
1. 点击"打开"按钮或菜单"文件→打开图片"加载地图
2. 点击"开始标记"进入标记模式
3. 在图片上点击要标记的位置
4. 在弹出的对话框中输入错误类型和描述
5. 点击"保存"保存错误记录

【错误类型】
- 几何错误：图形形状问题（红色标记）
- 属性错误：属性值问题（绿色标记）
- 拓扑错误：空间关系问题（蓝色标记）
- 坐标错误：坐标值问题（橙色标记）
- 其他：其他类型问题（灰色标记）

【快捷键】
Ctrl+O：打开文件
Ctrl+S：保存错误记录

【提示】
- 双击错误列表项可定位到该错误
- 点击"导出"可生成文本格式的检查报告
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("500x450")
        
        text = tk.Text(help_window, wrap=tk.WORD, font=("Arial", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
    
    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("关于", "空间数据质量检查工具 v3.0\n\n使用 tkinter 构建\n\n功能:\n- 加载图片和文本数据\n- 点击标记错误位置\n- 保存/加载错误记录\n- 导出检查报告")


# ========== 程序入口 ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = MapQCApp(root)
    root.mainloop()
