"""GUI主界面"""
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from monitor_task import MonitorTask
from window_capture import list_windows
from region_selector import RegionSelector
import json

class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("K检测 v001")
        self.root.geometry("420x320")
        self.root.resizable(False, False)
        self.tasks = []
        self.task_frames = []
        self.create_widgets()

    def create_widgets(self):
        # 顶部控制
        top = tk.Frame(self.root, pady=3)
        top.pack(fill=tk.X, padx=6)
        self.start_btn = tk.Button(top, text="启动", command=self.toggle_global,
                                   width=8, bg='green', fg='white', font=('Arial', 9))
        self.start_btn.pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="添加", command=self.add_task, width=8, font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        tk.Label(top, text="间隔(秒):", font=('Arial', 9)).pack(side=tk.LEFT, padx=(6, 2))
        self.interval_var = tk.StringVar(value="2")
        tk.Entry(top, textvariable=self.interval_var, width=3, font=('Arial', 9)).pack(side=tk.LEFT)

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
        dialog.geometry("320x220")
        dialog.grab_set()
        tk.Label(dialog, text="点击窗口开始框选区域:", pady=4, font=('Arial', 9)).pack()
        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        sb = tk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(frame, yscrollcommand=sb.set, font=('Arial', 9))
        listbox.pack(fill=tk.BOTH, expand=True)
        sb.config(command=listbox.yview)
        for hwnd, title in windows:
            listbox.insert(tk.END, title)

        def on_click(event):
            sel = listbox.curselection()
            if not sel:
                return
            hwnd, title = windows[sel[0]]
            dialog.destroy()
            # 置顶窗口
            import win32gui, win32con
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.root.after(200, lambda: self._start_region_select(hwnd, title))

        listbox.bind("<ButtonRelease-1>", on_click)

    def _start_region_select(self, hwnd, title):
        index = len(self.task_frames)
        RegionSelector(hwnd, lambda region: self._on_region_selected(index, hwnd, title, region))

    def _on_region_selected(self, index, hwnd, title, region):
        import win32gui, win32con
        # 取消置顶
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
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
        tk.Button(frame, text="声音", width=4, font=('Arial', 8),
                  command=lambda: self.import_sound(index)).pack(side=tk.LEFT, padx=1)
        tk.Button(frame, text="删除", width=4, font=('Arial', 8),
                  command=lambda: self.delete_task(index)).pack(side=tk.LEFT, padx=1)
        self.task_frames.append({'frame': frame, 'name_var': name_var, 'status_var': status_var,
                                 'enable_var': enable_var, 'task': task})

    def toggle_task(self, index):
        if index >= len(self.task_frames):
            return
        t = self.task_frames[index]
        if t['enable_var'].get():
            interval = float(self.interval_var.get())
            t['task'].start(interval, t['status_var'])
            self.log(f"{t['name_var'].get()[:10]} 启动")
        else:
            t['task'].stop()
            t['status_var'].set("未启动")
            self.log(f"{t['name_var'].get()[:10]} 停止")

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
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    from elevate import require_admin
    require_admin()
    root = tk.Tk()
    app = MonitorGUI(root)
    root.mainloop()
