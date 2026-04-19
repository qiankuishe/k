"""GUI主界面"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from monitor_task import MonitorTask
from window_capture import list_windows
from region_selector import RegionSelector
import json

class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("监测工具")
        self.root.geometry("520x400")
        self.root.resizable(False, False)

        self.tasks = []
        self.global_running = False
        self.task_frames = []

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        # 顶部控制栏
        top = tk.Frame(self.root, pady=4)
        top.pack(fill=tk.X, padx=8)

        self.start_btn = tk.Button(top, text="全局启动", command=self.toggle_global,
                                   width=10, bg='green', fg='white')
        self.start_btn.pack(side=tk.LEFT, padx=2)

        tk.Button(top, text="添加任务", command=self.add_task, width=10).pack(side=tk.LEFT, padx=2)

        tk.Label(top, text="间隔(秒):").pack(side=tk.LEFT, padx=(8, 2))
        self.interval_var = tk.StringVar(value="2")
        tk.Entry(top, textvariable=self.interval_var, width=4).pack(side=tk.LEFT)

        # 任务列表
        self.list_frame = tk.Frame(self.root)
        self.list_frame.pack(fill=tk.X, padx=8, pady=4)

        # 日志
        log_frame = tk.LabelFrame(self.root, text="日志", padx=4, pady=4)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED, font=("Consolas", 9))
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _add_task_row(self, index, title=""):
        frame = tk.Frame(self.list_frame, relief=tk.RIDGE, borderwidth=1, pady=3)
        frame.pack(fill=tk.X, pady=2)

        name_var = tk.StringVar(value=title or f"窗口{index+1}")
        tk.Entry(frame, textvariable=name_var, width=18).pack(side=tk.LEFT, padx=4)

        status_var = tk.StringVar(value="未启动")
        tk.Label(frame, textvariable=status_var, width=8, fg='gray').pack(side=tk.LEFT, padx=2)

        enable_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="启用", variable=enable_var,
                       command=lambda i=index: self.toggle_task(i)).pack(side=tk.LEFT, padx=2)

        tk.Button(frame, text="声音", width=4,
                  command=lambda i=index: self.import_sound(i)).pack(side=tk.LEFT, padx=2)
        tk.Button(frame, text="删除", width=4,
                  command=lambda i=index: self.delete_task(i)).pack(side=tk.LEFT, padx=2)

        info = {'frame': frame, 'name_var': name_var, 'status_var': status_var,
                'enable_var': enable_var, 'task': None}
        self.task_frames.append(info)
        return info

    def add_task(self):
        if len(self.task_frames) >= 6:
            messagebox.showwarning("警告", "最多支持6个监控任务")
            return

        windows = list_windows()
        if not windows:
            messagebox.showerror("错误", "未找到可用窗口")
            return

        # 窗口选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择窗口")
        dialog.geometry("360x260")
        dialog.grab_set()

        tk.Label(dialog, text="选择要监控的窗口：", pady=6).pack()

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10)

        sb = tk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(frame, yscrollcommand=sb.set, activestyle='dotbox')
        listbox.pack(fill=tk.BOTH, expand=True)
        sb.config(command=listbox.yview)

        for hwnd, title in windows:
            listbox.insert(tk.END, title)

        def on_select():
            sel = listbox.curselection()
            if not sel:
                return
            hwnd, title = windows[sel[0]]
            dialog.destroy()
            # 将目标窗口置顶并激活
            import win32gui, win32con
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            index = len(self.task_frames)
            self._add_task_row(index, title)
            RegionSelector(hwnd, lambda region, i=index, h=hwnd, t=title:
                           self.on_region_selected(i, h, t, region))

        tk.Button(dialog, text="确定", command=on_select, width=10).pack(pady=6)
        listbox.bind("<Double-Button-1>", lambda e: on_select())

    def on_region_selected(self, index, hwnd, title, region):
        import win32gui, win32con
        # 区域选完后取消置顶，锁定位置
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        task = MonitorTask(hwnd, region, lambda msg: self.log(msg))
        self.task_frames[index]['task'] = task
        self.task_frames[index]['name_var'].set(title[:18])
        self.log(f"任务{index+1}已添加: {title}")

    def toggle_task(self, index):
        if index >= len(self.task_frames):
            return
        task_info = self.task_frames[index]
        if task_info['task'] is None:
            messagebox.showwarning("警告", "请先添加任务")
            task_info['enable_var'].set(False)
            return
        if task_info['enable_var'].get():
            interval = float(self.interval_var.get())
            task_info['task'].start(interval, task_info['status_var'])
            self.log(f"{task_info['name_var'].get()} 已启动")
        else:
            task_info['task'].stop()
            task_info['status_var'].set("未启动")
            self.log(f"{task_info['name_var'].get()} 已停止")

    def toggle_global(self):
        self.global_running = not self.global_running
        if self.global_running:
            self.start_btn.config(text="全局停止", bg='red')
            for i, t in enumerate(self.task_frames):
                if t['task']:
                    t['enable_var'].set(True)
                    self.toggle_task(i)
        else:
            self.start_btn.config(text="全局启动", bg='green')
            for i, t in enumerate(self.task_frames):
                if t['enable_var'].get():
                    t['enable_var'].set(False)
                    self.toggle_task(i)

    def import_sound(self, index):
        if index >= len(self.task_frames) or self.task_frames[index]['task'] is None:
            messagebox.showwarning("警告", "请先添加任务")
            return
        path = filedialog.askopenfilename(
            filetypes=[("音频文件", "*.wav *.mp3"), ("所有文件", "*.*")])
        if path:
            self.task_frames[index]['task'].set_audio(path)
            self.log(f"{self.task_frames[index]['name_var'].get()} 已设置提示音")

    def delete_task(self, index):
        if index >= len(self.task_frames):
            return
        task_info = self.task_frames[index]
        if task_info['task']:
            task_info['task'].stop()
        task_info['frame'].destroy()
        self.task_frames.pop(index)
        # 重新绑定索引
        for i, t in enumerate(self.task_frames):
            for btn in t['frame'].winfo_children():
                pass  # 索引已通过 lambda 默认参数绑定，无需重绑
        self.log(f"任务已删除")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def save_config(self):
        config = {'interval': self.interval_var.get(), 'tasks': []}
        for t in self.task_frames:
            if t['task']:
                config['tasks'].append({
                    'name': t['name_var'].get(),
                    'hwnd': t['task'].hwnd,
                    'region': t['task'].region,
                    'audio': t['task'].audio_path
                })
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def load_config(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.interval_var.set(config.get('interval', '2'))
        except:
            pass
