import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import win32gui, win32ui, win32con
from PIL import Image, ImageStat
import threading
import time
import pygame
import os
import winsound

pygame.mixer.init()

class MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏房间满员检测工具 v2.0")
        self.root.geometry("700x550")
        
        self.monitors = []
        self.is_running = False
        self.setup_ui()

    def setup_ui(self):
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill="x", padx=15)
        
        self.btn_main = tk.Button(top_frame, text="▶ 总启动", bg="#2ecc71", fg="white", 
                                  font=("微软雅黑", 10, "bold"), width=15, command=self.toggle_main)
        self.btn_main.pack(side="left")
        
        tk.Button(top_frame, text="➕ 添加窗口位置", command=self.add_task).pack(side="left", padx=20)
        tk.Label(top_frame, text="(最多3个窗口)", fg="gray").pack(side="left")

        list_frame = tk.LabelFrame(self.root, text=" 监控列表 (右键项目可修改/删除/导入声音) ", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        columns = ("name", "status", "sound", "active")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=5)
        self.tree.heading("name", text="窗口备注")
        self.tree.heading("status", text="实时状态")
        self.tree.heading("sound", text="提示音文件")
        self.tree.heading("active", text="运行开关")
        self.tree.column("active", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.bind("<Double-1>", self.toggle_single_task)
        self.tree.bind("<Button-3>", self.show_context_menu)

        log_frame = tk.LabelFrame(self.root, text=" 运行日志 (24h) ", padx=10, pady=5)
        log_frame.pack(fill="x", padx=15, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, bg="#2c3e50", fg="#ecf0f1", font=("Consolas", 9))
        self.log_text.pack(fill="x")

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="修改备注", command=self.rename_task)
        self.menu.add_command(label="导入提示音(.wav/.mp3)", command=self.import_sound)
        self.menu.add_separator()
        self.menu.add_command(label="❌ 删除此任务", command=self.delete_task)

    def log(self, msg):
        now = time.strftime("%H:%M:%S")
        self.log_text.insert("1.0", f"[{now}] {msg}\n")

    def add_task(self):
        if len(self.monitors) >= 3:
            messagebox.showwarning("限制", "目前仅支持最多添加3个窗口")
            return
        
        messagebox.showinfo("操作指引", "请先切换到游戏窗口使其置顶，然后点确定。\n之后会进入截屏模式，请框选[满员时显示绿色]的区域。")
        hwnd = win32gui.GetForegroundWindow()
        win_title = win32gui.GetWindowText(hwnd)
        
        selector = AreaSelector()
        self.root.wait_window(selector.overlay)
        
        if selector.rect:
            task = {
                'hwnd': hwnd,
                'rect': selector.rect,
                'name': f"窗口 {len(self.monitors)+1}",
                'sound': "",
                'active': True,
                'last_status': "待测"
            }
            self.monitors.append(task)
            self.refresh_table()
            self.log(f"已添加: {win_title}")

    def capture_backend(self, hwnd, rect):
        try:
            x1, y1, x2, y2 = rect
            w_rect = win32gui.GetWindowRect(hwnd)
            rx1, ry1 = x1 - w_rect[0], y1 - w_rect[1]
            w, h = abs(x2 - x1), abs(y2 - y1)
            
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
            saveDC.SelectObject(saveBitMap)
            
            saveDC.BitBlt((0, 0), (w, h), mfcDC, (rx1, ry1), win32con.SRCCOPY)
            
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), 
                                  bmpstr, 'raw', 'BGRX', 0, 1)
            
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            return img
        except:
            return None

    def monitor_engine(self):
        while self.is_running:
            for task in self.monitors:
                if not task['active']:
                    continue
                
                img = self.capture_backend(task['hwnd'], task['rect'])
                if img:
                    stat = ImageStat.Stat(img)
                    avg = stat.mean
                    is_full = avg[1] > 130 and avg[1] > avg[0] + 40
                    current_status = "满员" if is_full else "有空缺"
                    
                    if current_status != task['last_status']:
                        task['last_status'] = current_status
                        self.log(f"状态更变 -> {task['name']}: {current_status}")
                        if not is_full:
                            self.play_alert(task['sound'])
                    
                    self.root.after(0, self.refresh_table)
            time.sleep(2)

    def play_alert(self, path):
        if path and os.path.exists(path):
            try:
                pygame.mixer.Sound(path).play()
            except:
                winsound.Beep(800, 500)
        else:
            winsound.Beep(800, 500)

    def toggle_main(self):
        if not self.monitors:
            messagebox.showwarning("提示", "请先添加窗口")
            return
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_main.config(text="■ 停止监控", bg="#e74c3c")
            threading.Thread(target=self.monitor_engine, daemon=True).start()
            self.log(">>> 系统总启动")
        else:
            self.btn_main.config(text="▶ 总启动", bg="#2ecc71")
            self.log(">>> 系统已停止")

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, t in enumerate(self.monitors):
            switch = "ON" if t['active'] else "OFF"
            sound_name = os.path.basename(t['sound']) if t['sound'] else "系统默认"
            self.tree.insert("", "end", iid=i, values=(t['name'], t['last_status'], sound_name, switch))

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def rename_task(self):
        if not self.tree.selection():
            return
        idx = int(self.tree.selection()[0])
        name = simpledialog.askstring("重命名", "输入备注名:")
        if name:
            self.monitors[idx]['name'] = name
            self.refresh_table()

    def import_sound(self):
        if not self.tree.selection():
            return
        idx = int(self.tree.selection()[0])
        path = filedialog.askopenfilename(filetypes=[("音频", "*.wav *.mp3")])
        if path:
            self.monitors[idx]['sound'] = path
            self.refresh_table()

    def delete_task(self):
        if not self.tree.selection():
            return
        idx = int(self.tree.selection()[0])
        del self.monitors[idx]
        self.refresh_table()

    def toggle_single_task(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            idx = int(item)
            self.monitors[idx]['active'] = not self.monitors[idx]['active']
            self.refresh_table()

class AreaSelector:
    def __init__(self):
        self.overlay = tk.Toplevel()
        self.overlay.attributes("-alpha", 0.3)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.overlay, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        self.rect = None
        self.start_x = self.start_y = 0
        self.temp_rect = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.temp_rect = self.canvas.create_rectangle(0, 0, 0, 0, outline="red", width=2)
    
    def on_drag(self, event):
        self.canvas.coords(self.temp_rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_release(self, event):
        self.rect = (self.start_x, self.start_y, event.x, event.y)
        self.overlay.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure("Treeview", rowheight=30)
    app = MonitorApp(root)
    root.mainloop()
