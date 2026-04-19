"""交互式圆形区域选择功能"""
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import win32gui
import win32con
from window_capture import capture_window

class RegionSelector:
    def __init__(self, hwnd, callback):
        self.hwnd = hwnd
        self.callback = callback
        self.center_x = None
        self.center_y = None
        self.radius = 50  # 初始半径
        self.circle = None
        self.dragging = False
        self.countdown = 15
        
        # 创建全屏遮罩
        self.root = tk.Toplevel()
        self.root.attributes('-alpha', 0.4)
        self.root.attributes('-topmost', True)
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        
        self.canvas = tk.Canvas(self.root, cursor="cross", highlightthickness=0, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", lambda e: self.cancel())
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Escape>", lambda e: self.cancel())
        self.canvas.bind("<Return>", lambda e: self.confirm())
        
        # 显示提示
        self.hint_text = self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 30,
            text=f"左键拖动圆形 | 滚轮调整大小 | 回车确认 | 右键/ESC取消 - {self.countdown}秒后自动关闭",
            fill="yellow", font=("Arial", 14)
        )
        
        # 启动倒计时
        self.update_countdown()
    
    def on_click(self, event):
        if self.circle is None:
            # 首次点击，创建圆形
            self.center_x = event.x
            self.center_y = event.y
            self.draw_circle()
        else:
            # 检查是否点击在圆内
            dx = event.x - self.center_x
            dy = event.y - self.center_y
            if dx*dx + dy*dy <= self.radius*self.radius:
                self.dragging = True
    
    def on_drag(self, event):
        if self.dragging:
            self.center_x = event.x
            self.center_y = event.y
            self.draw_circle()
    
    def on_release(self, event):
        self.dragging = False
    
    def on_scroll(self, event):
        if self.circle is not None:
            # 滚轮调整半径
            delta = 5 if event.delta > 0 else -5
            self.radius = max(20, min(200, self.radius + delta))
            self.draw_circle()
    
    def draw_circle(self):
        if self.circle:
            self.canvas.delete(self.circle)
        x1 = self.center_x - self.radius
        y1 = self.center_y - self.radius
        x2 = self.center_x + self.radius
        y2 = self.center_y + self.radius
        self.circle = self.canvas.create_oval(x1, y1, x2, y2, 
                                               outline='red', width=3)
        # 显示半径
        if hasattr(self, 'radius_text'):
            self.canvas.delete(self.radius_text)
        self.radius_text = self.canvas.create_text(
            self.center_x, self.center_y + self.radius + 20,
            text=f"半径: {self.radius}px", fill="white", font=("Arial", 12)
        )
    
    def confirm(self):
        if self.circle is None:
            return
        
        # 转换为相对于窗口的坐标
        left, top, _, _ = win32gui.GetWindowRect(self.hwnd)
        # 存储圆心和半径（相对坐标）
        region = (self.center_x - left, self.center_y - top, self.radius)
        
        # 取消窗口置顶
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
        self.root.destroy()
        self.callback(region)
    
    def cancel(self):
        # 取消置顶
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        self.root.destroy()
    
    def update_countdown(self):
        if self.countdown > 0:
            self.canvas.itemconfig(self.hint_text, 
                text=f"左键拖动圆形 | 滚轮调整大小 | 回车确认 | 右键/ESC取消 - {self.countdown}秒后自动关闭")
            self.countdown -= 1
            self.root.after(1000, self.update_countdown)
        else:
            # 倒计时结束，取消置顶并关闭遮罩
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.root.destroy()
