"""GUI主界面"""
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from monitor_task import MonitorTask
from window_capture import list_windows
from region_selector import RegionSelector
import json
import os

VERSION = "037"

class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"K监控工具 v{VERSION}")
        self.root.geometry("420x320")
        self.root.resizable(False, False)
        self.tasks = []
        self.task_frames = []
        self.update_thread = None
        self.update_cancel_flag = False
        self.create_widgets()

    def create_widgets(self):
        # 顶部控制
        top = tk.Frame(self.root, pady=3)
        top.pack(fill=tk.X, padx=6)
        self.start_btn = tk.Button(top, text="启动", command=self.toggle_global,
                                   width=8, bg='green', fg='white', font=('Arial', 9))
        self.start_btn.pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="添加", command=self.add_task, width=8, font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="检查更新", command=self.check_update, width=8, font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        tk.Label(top, text="间隔(秒):", font=('Arial', 9)).pack(side=tk.LEFT, padx=(6, 2))
        self.interval_var = tk.StringVar(value="2")
        tk.Entry(top, textvariable=self.interval_var, width=3, font=('Arial', 9)).pack(side=tk.LEFT)
        
        tk.Label(top, text="音量:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(8, 2))
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_slider = tk.Scale(top, from_=0, to=100, orient=tk.HORIZONTAL, 
                                variable=self.volume_var, showvalue=False, length=60,
                                command=self.on_volume_change)
        volume_slider.set(100)
        volume_slider.pack(side=tk.LEFT)

        # 任务列表
        self.list_frame = tk.Frame(self.root)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)

        # 日志
        log_frame = tk.LabelFrame(self.root, text="日志", padx=3, pady=3, font=('Arial', 9))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)
        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED, font=('Consolas', 8))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def add_task(self):
        if len(self.task_frames) >= 4:
            messagebox.showwarning("警告", "最多4个任务")
            return
        windows = list_windows()
        if not windows:
            messagebox.showerror("错误", "未找到窗口")
            return

        # 窗口选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择窗口")
        dialog.geometry("480x320")
        dialog.grab_set()
        
        tk.Label(dialog, text="点击窗口查看并框选:", pady=6, font=('Arial', 10, 'bold')).pack()
        
        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        
        sb = tk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=sb.set, font=('Consolas', 9), activestyle='dotbox')
        listbox.pack(fill=tk.BOTH, expand=True)
        sb.config(command=listbox.yview)
        
        # 显示窗口信息：标题 | 分辨率 | PID
        for hwnd, title, pid, width, height in windows:
            display_name = f"{title[:30]:<30} | {width}x{height:<10} | PID:{pid}"
            listbox.insert(tk.END, display_name)

        def on_select(event):
            if not listbox.curselection():
                return
            sel = listbox.curselection()[0]
            hwnd, title, pid, width, height = windows[sel]
            
            # 先置顶窗口让用户看到
            import win32gui, win32con
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            except:
                pass
            
            # 延迟关闭对话框并进入框选
            dialog.after(500, lambda: self._confirm_and_select(dialog, hwnd, title))

        listbox.bind("<<ListboxSelect>>", on_select)
    
    def _confirm_and_select(self, dialog, hwnd, title):
        dialog.destroy()
        self._start_region_select(hwnd, title)

    def _start_region_select(self, hwnd, title):
        index = len(self.task_frames)
        RegionSelector(hwnd, lambda region: self._on_region_selected(index, hwnd, title, region))

    def _on_region_selected(self, index, hwnd, title, region):
        # 区域已在 RegionSelector 里取消置顶
        task = MonitorTask(hwnd, region, lambda msg: self.log(msg))
        self._add_task_row(index, hwnd, title, task)
        self.log(f"已添加: {title[:12]}")

    def _add_task_row(self, index, hwnd, title, task):
        frame = tk.Frame(self.list_frame, relief=tk.RIDGE, borderwidth=1, pady=2)
        frame.pack(fill=tk.X, pady=2)
        name_var = tk.StringVar(value=title[:15])
        tk.Label(frame, textvariable=name_var, width=16, anchor='w', font=('Arial', 9)).pack(side=tk.LEFT, padx=3)
        status_var = tk.StringVar(value="未启动")
        tk.Label(frame, textvariable=status_var, width=7, fg='gray', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        enable_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="启用", variable=enable_var, font=('Arial', 8),
                       command=lambda: self.toggle_task(index)).pack(side=tk.LEFT, padx=2)
        sound_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="声音", variable=sound_var, font=('Arial', 8)).pack(side=tk.LEFT, padx=1)
        tk.Button(frame, text="导入", width=4, font=('Arial', 8),
                  command=lambda: self.import_sound(index)).pack(side=tk.LEFT, padx=1)
        tk.Button(frame, text="删除", width=4, font=('Arial', 8),
                  command=lambda: self.delete_task(index)).pack(side=tk.LEFT, padx=1)
        self.task_frames.append({'frame': frame, 'name_var': name_var, 'status_var': status_var,
                                 'enable_var': enable_var, 'sound_var': sound_var, 'task': task})

    def toggle_task(self, index):
        if index >= len(self.task_frames):
            return
        t = self.task_frames[index]
        if t['enable_var'].get():
            interval = float(self.interval_var.get())
            volume = self.volume_var.get() / 100.0
            t['task'].set_sound_enabled(t['sound_var'].get())
            t['task'].set_volume(volume)
            t['task'].start(interval, t['status_var'])
            self.log(f"{t['name_var'].get()[:10]} 启动")
        else:
            t['task'].stop()
            t['status_var'].set("未启动")
            self.log(f"{t['name_var'].get()[:10]} 停止")
    
    def on_volume_change(self, value):
        """音量改变时更新所有运行中的任务"""
        volume = float(value) / 100.0
        for t in self.task_frames:
            if t['task']:
                t['task'].set_volume(volume)

    def toggle_global(self):
        running = self.start_btn['text'] == '启动'
        if running:
            self.start_btn.config(text="停止", bg='red')
            for i, t in enumerate(self.task_frames):
                t['enable_var'].set(True)
                self.toggle_task(i)
        else:
            self.start_btn.config(text="启动", bg='green')
            for i, t in enumerate(self.task_frames):
                if t['enable_var'].get():
                    t['enable_var'].set(False)
                    self.toggle_task(i)

    def import_sound(self, index):
        if index >= len(self.task_frames):
            return
        path = filedialog.askopenfilename(filetypes=[("音频", "*.wav *.mp3")])
        if path:
            self.task_frames[index]['task'].set_audio(path)
            self.log(f"已设置提示音")

    def delete_task(self, index):
        if index >= len(self.task_frames):
            return
        t = self.task_frames[index]
        t['task'].stop()
        t['frame'].destroy()
        self.task_frames.pop(index)
        self.log(f"已删除任务")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        # 限制日志最大100行
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > 100:
            self.log_text.delete('1.0', f'{line_count - 100}.0')
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def check_update(self):
        """检查并执行更新（后台线程）- 支持取消"""
        import threading
        
        # 如果正在更新，取消并重新开始
        if self.update_thread and self.update_thread.is_alive():
            self.log("取消当前更新...")
            self.update_cancel_flag = True
            # 删除临时文件
            import glob
            for tmp_file in glob.glob("K-*.exe.tmp"):
                try:
                    os.remove(tmp_file)
                except:
                    pass
            # 等待线程结束
            self.update_thread.join(timeout=2)
        
        self.log("正在检查更新...")
        self.update_cancel_flag = False
        self.update_thread = threading.Thread(target=self._check_update_thread, daemon=True)
        self.update_thread.start()
    
    def _check_update_thread(self):
        """后台检查更新"""
        if self.update_cancel_flag:
            return
        
        try:
            from updater import check_update, download_and_update
            new_version, download_url = check_update(VERSION)
            
            if self.update_cancel_flag:
                return
            
            if new_version:
                # 回到主线程显示对话框
                self.root.after(0, lambda: self._show_update_dialog(new_version, download_url))
            else:
                self.root.after(0, lambda: self.log("已是最新版本"))
                self.root.after(0, lambda: messagebox.showinfo("检查更新", "当前已是最新版本"))
        except Exception as e:
            if not self.update_cancel_flag:
                self.root.after(0, lambda: self.log(f"更新失败: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("更新失败", str(e)))
    
    def _show_update_dialog(self, new_version, download_url):
        """显示更新对话框"""
        if messagebox.askyesno("发现新版本", f"当前版本: v{VERSION}\n最新版本: v{new_version}\n\n是否立即更新？"):
            self.log(f"开始下载 v{new_version}...")
            from updater import download_and_update
            import threading
            import time
            
            last_percent = [0]
            last_update_time = [time.time()]
            
            def progress_callback(percent, downloaded, total):
                now = time.time()
                # 每10%更新一次，或者距上次更新超过30秒
                if percent - last_percent[0] >= 10 or percent == 100 or (now - last_update_time[0] >= 30):
                    mb_downloaded = downloaded / 1024 / 1024
                    mb_total = total / 1024 / 1024
                    self.root.after(0, lambda p=percent, d=mb_downloaded, t=mb_total: 
                                   self.log(f"下载进度: {p}% ({d:.1f}/{t:.1f} MB)"))
                    last_percent[0] = percent
                    last_update_time[0] = now
            
            self.update_thread = threading.Thread(
                target=lambda: download_and_update(download_url, new_version, 
                                                   lambda: self.update_cancel_flag,
                                                   progress_callback), 
                daemon=True
            )
            self.update_thread.start()

if __name__ == "__main__":
    print(f"=== K监控工具 v{VERSION} 启动中 ===")
    print(f"运行文件: {__file__}")
    from elevate import require_admin
    require_admin()
    root = tk.Tk()
    app = MonitorGUI(root)
    root.mainloop()
