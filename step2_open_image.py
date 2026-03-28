"""
空间数据质量检查工具 - 第二步：打开并显示图片
===========================================
学习目标：
1. 使用filedialog选择文件
2. 使用PIL库打开图片
3. 在Canvas上显示图片
"""
import os.path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk  # 需要安装: pip install Pillow


class MapQCApp:
    """主应用程序类"""
    
    def __init__(self, root):
        """初始化方法 - 创建界面"""
        self.root = root
        self.root.title("MapToolApp")
        self.root.geometry("900x600")
        
        # 用于存储当前图片
        self.current_image = None
        self.current_image_path = None
        self.photo = None  # ImageTk.PhotoImage对象，必须保持引用
        
        # 创建界面
        self._create_menu()
        self._create_status_bar()
        self._create_main_area()
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=lambda:messagebox.showinfo("Message", "Function is under development"), accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        
        # 绑定快捷键
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-S>", lambda:messagebox.showinfo("Message", "Function is under development"))
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_main_area(self):
        """创建主区域"""
        # 主容器
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：显示区域
        self.display_frame = tk.Frame(self.main_frame)
        self.display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建Canvas用于显示图片
        self.canvas = tk.Canvas(self.display_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 提示文字
        self.hint_text = self.canvas.create_text(
            400, 300,  # 位置
            text="Open map data file\nSupport: JPG, PNG, BMP, TIF",
            font=("Arial", 14),
            fill="gray"
        )
        
        # 文本显示区域（初始隐藏）
        self.text_frame = tk.Frame(self.display_frame)
        self.text_widget = tk.Text(self.text_frame, wrap=tk.NONE, font=("Consolas", 10))
        
        # 添加滚动条
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
        self.right_frame = tk.Frame(self.main_frame, width=280, bg="#f0f0f0")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False)
        
        # 标题
        tk.Label(self.right_frame, text="Error List", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=10)
        
        # 错误列表
        self.error_listbox = tk.Listbox(self.right_frame, font=("Arial", 10), height=20)
        self.error_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按钮
        btn_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(btn_frame, text="Mark", command=self.add_error).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete", command=self.delete_error).pack(side=tk.LEFT, padx=2)
    
    # ========== 功能方法 ==========

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
        if ext in ['.jpg','.jpeg','.png' ,'.bmp' ,'.tif' ,'.tiff']:
            self.open_image(file_path)
        else:
            self.open_text(file_path)

    #分别实现文本和图片
    def open_image(self,file_path):
        try:
            # 使用PIL打开图片
            img = Image.open(file_path)
            
            # 获取Canvas大小
            self.canvas.update()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # 如果图片太大，按比例缩小
            img_width, img_height = img.size
            scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
            
            if scale < 1.0:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # 转换为tkinter可用的格式
            self.photo = ImageTk.PhotoImage(img)
            
            # 清除提示文字
            self.canvas.delete(self.hint_text)
            
            # 在Canvas中心显示图片
            self.canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.photo,
                anchor=tk.CENTER,
                tags="image"
            )
            
            # 保存当前图片信息
            self.current_image = img
            self.current_image_path = file_path
            
            # 更新状态栏
            self.status_bar.config(text=f"Already open: {file_path} | Size: {img_width}x{img_height}")
            
            # 隐藏文本区域，显示Canvas
            self.text_frame.pack_forget()
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Can't open the file:\n{str(e)}")
    
    def open_text(self,file_path):
        try:
            self.get_text(file_path,'utf-8')
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                self.get_text(file_path,'gbk')
            except Exception as e:
                messagebox.showerror("Error", f"Can't open the file:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Can't open the file:\n{str(e)}")

    # open_text()的一个部分
    def get_text(self,file_path,codemode):
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
    
    def add_error(self):
        """添加错误记录"""
        # 创建一个简单的对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Error")
        dialog.geometry("400x200")
        dialog.transient(self.root)  # 设置为父窗口的子窗口
        dialog.grab_set()  # 模态对话框
        
        # 错误类型
        tk.Label(dialog, text="Error type:").pack(pady=5)
        type_var = tk.StringVar(value="Geometric Error")
        type_combo = ttk.Combobox(dialog, textvariable=type_var, values=[
            "Geometric Error", "Attribute Error", "Topological Error", "Coordinate Error", "Other"
        ])
        type_combo.pack(pady=5)
        
        # 错误描述
        tk.Label(dialog, text="Error Description:").pack(pady=5)
        desc_entry = tk.Entry(dialog, width=40)
        desc_entry.pack(pady=5)
        
        def save_error():
            error_type = type_var.get()
            description = desc_entry.get()
            if description:
                self.error_listbox.insert(tk.END, f"[{error_type}] {description}")
                messagebox.showinfo("Success", "Error log has been added")
                dialog.destroy()
            else:
                messagebox.showwarning("Warning", "Missing error description")
        
        # 按钮
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Yes", command=save_error).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="No", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_error(self):
        """删除选中的错误记录"""
        selection = self.error_listbox.curselection()
        if selection:
            self.error_listbox.delete(selection[0])
        else:
            messagebox.showwarning("Warning", "Please select an error log first")
    
    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("About", "MapTool v1.0\n\nBuilding with tkinter")


# ========== 程序入口 ==========
if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    
    # 创建应用程序
    app = MapQCApp(root)
    
    # 运行主循环
    root.mainloop()
