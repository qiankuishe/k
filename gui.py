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
        self.root.title("游戏房间满员监测工具")
        self.root.geometry("800x600")
        
        self.tasks = []
        self.global_running = False
        
        self.create_widgets()
        self.load_config()
    
    def create_widgets(self):
        # 主控区
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X, padx=10)
        
        self.start_btn = tk.Button(control_frame, text="全局启动", 
                                   command=self.toggle_global, width=12, bg='green', fg='white')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="添加任务", 
                 command=self.add_task, width=12).pack(side=tk.LEFT, padx=5)
        
        tk.Label(control_frame, text="检测间隔(秒):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="2")
        tk.Entry(control_frame, textvariable=self.interval_var, width=5).pack(side=tk.LEFT)
        
        # 任务列表区
        list_frame = tk.LabelFrame(self.root, text="监控任务列表", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.task_frames = []
        for i in range(3):
            self.create_task_row(list_frame, i)
        
        # 日志区
        log_frame = tk.LabelFrame(self.root, text="运行日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
    
    def create_task_row(self, parent, index):
        frame = tk.Frame(parent, relief=tk.RIDGE, borderwidth=1, pady=5)
        frame.pack(fill=tk.X, pady=5)
        
        name_var = tk.StringVar(value=f"窗口{index+1}")
        tk.Entry(frame, textvariable=name_var, width=15).pack(side=tk.LEFT, padx=5)
        
        status_var = tk.StringVar(value="未启动")
        tk.Label(frame, textvariable=status_var, width=10, 
                fg='gray').pack(side=tk.LEFT, padx=5)
        
        enable_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="启用", variable=enable_var,
                      command=lambda: self.toggle_task(index)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame, text="导入声音", 
                 command=lambda: self.import_sound(index)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(frame, text="删除", 
                 command=lambda: self.delete_task(index)).pack(side=tk.LEFT, padx=2)
        
        self.task_frames.append({
            'frame': frame,
            'name_var': name_var,
            'status_var': status_var,
            'enable_var': enable_var,
            'task': None
        })
    
    def add_task(self):
        # 找到第一个空位
        index = next((i for i, t in enumerate(self.task_frames) if t['task'] is None), None)
        if index is None:
            messagebox.showwarning("警告", "最多支持3个监控任务")
            return
        
        # 选择窗口
        windows = list_windows()
        if not windows:
            messagebox.showerror("错误", "未找到可用窗口")
            return
        
        # 创建窗口选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择窗口")
        dialog.geometry("400x300")
        
        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for hwnd, title in windows:
            listbox.insert(tk.END, f"{title}")
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                hwnd, title = windows[selection[0]]
                dialog.destroy()
                # 启动区域选择
                RegionSelector(hwnd, lambda region: self.on_region_selected(index, hwnd, title, region))
        
        tk.Button(dialog, text="确定", command=on_select).pack(pady=5)
    
    def on_region_selected(self, index, hwnd, title, region):
        task = MonitorTask(hwnd, region, lambda msg: self.log(msg))
        self.task_frames[index]['task'] = task
        self.task_frames[index]['name_var'].set(title[:15])
        self.log(f"任务{index+1}已添加: {title}")
    
    def toggle_task(self, index):
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
            for i, task_info in enumerate(self.task_frames):
                if task_info['task']:
                    task_info['enable_var'].set(True)
                    self.toggle_task(i)
        else:
            self.start_btn.config(text="全局启动", bg='green')
            for i, task_info in enumerate(self.task_frames):
                if task_info['enable_var'].get():
                    task_info['enable_var'].set(False)
                    self.toggle_task(i)
    
    def import_sound(self, index):
        if self.task_frames[index]['task'] is None:
            messagebox.showwarning("警告", "请先添加任务")
            return
        
        path = filedialog.askopenfilename(
            filetypes=[("音频文件", "*.wav *.mp3"), ("所有文件", "*.*")]
        )
        if path:
            self.task_frames[index]['task'].set_audio(path)
            self.log(f"{self.task_frames[index]['name_var'].get()} 已设置提示音")
    
    def delete_task(self, index):
        task_info = self.task_frames[index]
        if task_info['task']:
            task_info['task'].stop()
            task_info['task'] = None
            task_info['name_var'].set(f"窗口{index+1}")
            task_info['status_var'].set("未启动")
            task_info['enable_var'].set(False)
            self.log(f"任务{index+1}已删除")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def save_config(self):
        config = {
            'interval': self.interval_var.get(),
            'tasks': []
        }
        for i, task_info in enumerate(self.task_frames):
            if task_info['task']:
                config['tasks'].append({
                    'name': task_info['name_var'].get(),
                    'hwnd': task_info['task'].hwnd,
                    'region': task_info['task'].region,
                    'audio': task_info['task'].audio_path
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
