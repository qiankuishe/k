"""交互式矩形区域选择功能 - 用于文字识别"""
import tkinter as tk
import win32gui
import win32con

class RegionSelector:
    def __init__(self, hwnd, callback):
        self.hwnd = hwnd
        self.callback = callback
        self.dragging = False
        self.resizing = False
        self.countdown = 15
        
        # 获取目标窗口位置和大小
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        # 初始矩形在窗口中心，适合 "4/4" 文字的比例
        self.rect_width = 60
        self.rect_height = 25
        self.rect_x = width // 2 - self.rect_width // 2
        self.rect_y = height // 2 - self.rect_height // 2
        
        # 创建透明覆盖窗口
        self.root = tk.Toplevel()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.5)
        self.root.geometry(f"{width}x{height}+{left}+{top}")
        
        self.canvas = tk.Canvas(self.root, width=width, height=height, 
                               bg='black', highlightthickness=0, cursor="cross")
        self.canvas.pack()
        
        # 绑定事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", lambda e: self.cancel())
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        
        # 键盘事件
        self.root.bind("<Escape>", lambda e: self.cancel())
        self.root.bind("<Return>", lambda e: self.confirm())
        self.root.bind("<KP_Enter>", lambda e: self.confirm())
        self.root.focus_force()
        
        # 绘制矩形
        self.draw_rect()
        
        # 显示提示
        self.hint_text = self.canvas.create_text(
            width // 2, 30,
            text=f"拖动矩形 | 滚轮调大小 | 回车确认 | 右键取消 - {self.countdown}秒",
            fill="yellow", font=("Arial", 12, "bold")
        )
        
        # 启动倒计时
        self.update_countdown()
    
    def on_click(self, event):
        # 检查是否点击在矩形内
        if (self.rect_x <= event.x <= self.rect_x + self.rect_width and
            self.rect_y <= event.y <= self.rect_y + self.rect_height):
            self.dragging = True
            self.drag_offset_x = event.x - self.rect_x
            self.drag_offset_y = event.y - self.rect_y
    
    def on_drag(self, event):
        if self.dragging:
            self.rect_x = event.x - self.drag_offset_x
            self.rect_y = event.y - self.drag_offset_y
            self.draw_rect()
    
    def on_release(self, event):
        self.dragging = False
    
    def on_scroll(self, event):
        # 滚轮调整大小，保持宽高比约 2.4:1
        delta = 5 if event.delta > 0 else -5
        self.rect_width = max(30, min(200, self.rect_width + delta))
        self.rect_height = int(self.rect_width / 2.4)
        self.draw_rect()
    
    def draw_rect(self):
        self.canvas.delete("rect")
        
        # 绘制虚线矩形
        self.canvas.create_rectangle(
            self.rect_x, self.rect_y,
            self.rect_x + self.rect_width, self.rect_y + self.rect_height,
            outline='red', width=2, dash=(5, 3), tags="rect"
        )
        
        # 绘制十字中心线
        center_x = self.rect_x + self.rect_width // 2
        center_y = self.rect_y + self.rect_height // 2
        self.canvas.create_line(center_x - 10, center_y, center_x + 10, center_y,
                               fill='red', width=2, tags="rect")
        self.canvas.create_line(center_x, center_y - 10, center_x, center_y + 10,
                               fill='red', width=2, tags="rect")
        
        # 显示尺寸
        self.canvas.create_text(
            center_x, self.rect_y + self.rect_height + 20,
            text=f"{self.rect_width}×{self.rect_height}px", fill="white", 
            font=("Arial", 11, "bold"), tags="rect"
        )
    
    def confirm(self):
        # 存储矩形区域（x, y, width, height）
        region = (self.rect_x, self.rect_y, self.rect_width, self.rect_height)
        
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
                text=f"拖动矩形 | 滚轮调大小 | 回车确认 | 右键取消 - {self.countdown}秒")
            self.countdown -= 1
            self.root.after(1000, self.update_countdown)
        else:
            # 倒计时结束
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.root.destroy()
