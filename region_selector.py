"""交互式圆形区域选择功能 - 直接在目标窗口上显示"""
import tkinter as tk
import win32gui
import win32con

class RegionSelector:
    def __init__(self, hwnd, callback):
        self.hwnd = hwnd
        self.callback = callback
        self.dragging = False
        self.countdown = 15
        
        # 获取目标窗口位置和大小
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        # 初始圆心在窗口中心
        self.center_x = width // 2
        self.center_y = height // 2
        self.radius = 50
        
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
        
        # 键盘事件绑定到窗口
        self.root.bind("<Escape>", lambda e: self.cancel())
        self.root.bind("<Return>", lambda e: self.confirm())
        self.root.bind("<KP_Enter>", lambda e: self.confirm())  # 小键盘回车
        self.root.focus_force()  # 确保窗口获得焦点
        
        # 绘制圆形
        self.draw_circle()
        
        # 显示提示
        self.hint_text = self.canvas.create_text(
            width // 2, 30,
            text=f"拖动圆形 | 滚轮调大小 | 回车确认 | 右键取消 - {self.countdown}秒",
            fill="yellow", font=("Arial", 12, "bold")
        )
        
        # 启动倒计时
        self.update_countdown()
    
    def on_click(self, event):
        # 检查是否点击在圆内
        dx = event.x - self.center_x
        dy = event.y - self.center_y
        if dx*dx + dy*dy <= self.radius*self.radius:
            self.dragging = True
            self.drag_offset_x = event.x - self.center_x
            self.drag_offset_y = event.y - self.center_y
    
    def on_drag(self, event):
        if self.dragging:
            self.center_x = event.x - self.drag_offset_x
            self.center_y = event.y - self.drag_offset_y
            self.draw_circle()
    
    def on_release(self, event):
        self.dragging = False
    
    def on_scroll(self, event):
        # 滚轮调整半径
        delta = 5 if event.delta > 0 else -5
        self.radius = max(8, min(150, self.radius + delta))
        self.draw_circle()
    
    def draw_circle(self):
        self.canvas.delete("circle")
        self.canvas.delete("radius_text")
        self.canvas.delete("magnifier")
        
        x1 = self.center_x - self.radius
        y1 = self.center_y - self.radius
        x2 = self.center_x + self.radius
        y2 = self.center_y + self.radius
        
        # 绘制虚线圆形
        self.canvas.create_oval(x1, y1, x2, y2, 
                               outline='red', width=2, dash=(5, 3), tags="circle")
        # 绘制十字中心线
        self.canvas.create_line(self.center_x - 10, self.center_y,
                               self.center_x + 10, self.center_y,
                               fill='red', width=2, tags="circle")
        self.canvas.create_line(self.center_x, self.center_y - 10,
                               self.center_x, self.center_y + 10,
                               fill='red', width=2, tags="circle")
        
        # 显示半径
        self.canvas.create_text(
            self.center_x, self.center_y + self.radius + 20,
            text=f"半径: {self.radius}px", fill="white", 
            font=("Arial", 11, "bold"), tags="radius_text"
        )
        
        # 半径小于15px时显示放大镜
        if self.radius < 15:
            mag_size = 80  # 放大镜尺寸
            mag_x = self.center_x + 60
            mag_y = self.center_y - 60
            
            # 放大镜背景
            self.canvas.create_rectangle(mag_x - mag_size//2, mag_y - mag_size//2,
                                         mag_x + mag_size//2, mag_y + mag_size//2,
                                         fill='black', outline='yellow', width=2, tags="magnifier")
            
            # 放大3倍的圆形
            scale = 3
            mag_radius = self.radius * scale
            self.canvas.create_oval(mag_x - mag_radius, mag_y - mag_radius,
                                   mag_x + mag_radius, mag_y + mag_radius,
                                   outline='red', width=2, dash=(3, 2), tags="magnifier")
            
            # 放大的十字线
            self.canvas.create_line(mag_x - 8, mag_y, mag_x + 8, mag_y,
                                   fill='red', width=1, tags="magnifier")
            self.canvas.create_line(mag_x, mag_y - 8, mag_x, mag_y + 8,
                                   fill='red', width=1, tags="magnifier")
            
            # 标注
            self.canvas.create_text(mag_x, mag_y + mag_size//2 + 12,
                                   text="3x放大", fill="yellow", 
                                   font=("Arial", 9), tags="magnifier")
    
    def confirm(self):
        # 存储圆心和半径（相对坐标）
        region = (self.center_x, self.center_y, self.radius)
        
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
                text=f"拖动圆形 | 滚轮调大小 | 回车确认 | 右键取消 - {self.countdown}秒")
            self.countdown -= 1
            self.root.after(1000, self.update_countdown)
        else:
            # 倒计时结束
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.root.destroy()
