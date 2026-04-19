"""交互式区域选择功能"""
import tkinter as tk
from PIL import Image, ImageTk
import win32gui
import win32con
from window_capture import capture_window

class RegionSelector:
    def __init__(self, hwnd, callback):
        self.hwnd = hwnd
        self.callback = callback
        self.start_x = self.start_y = 0
        self.rect = None
        
        # 置顶窗口
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                             win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
        # 创建全屏遮罩
        self.root = tk.Toplevel()
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        
        self.canvas = tk.Canvas(self.root, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # 显示提示
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 50,
            text="拖拽鼠标框选监测区域", fill="white", font=("Arial", 20)
        )
    
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
    
    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        if x2 - x1 > 10 and y2 - y1 > 10:
            # 转换为相对于窗口的坐标
            left, top, _, _ = win32gui.GetWindowRect(self.hwnd)
            region = (x1 - left, y1 - top, x2 - x1, y2 - y1)
            self.callback(region)
        
        self.root.destroy()
