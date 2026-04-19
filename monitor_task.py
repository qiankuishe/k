"""监控任务管理"""
import threading
import time
from window_capture import capture_window
from color_detector import detect_status
from audio_player import play_sound

class MonitorTask:
    def __init__(self, hwnd, region, log_callback):
        self.hwnd = hwnd
        self.region = region
        self.log_callback = log_callback
        self.audio_path = None
        self.running = False
        self.thread = None
        self.last_status = None
    
    def set_audio(self, path):
        self.audio_path = path
    
    def start(self, interval, status_var):
        if self.running:
            return
        
        self.running = True
        self.status_var = status_var
        self.thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _monitor_loop(self, interval):
        while self.running:
            try:
                img = capture_window(self.hwnd, self.region)
                current_status = detect_status(img)
                
                # 更新状态显示
                if current_status == 'full':
                    self.status_var.set("已满员")
                else:
                    self.status_var.set("空缺")
                
                # 检测状态切换：满员 -> 空缺
                if self.last_status == 'full' and current_status == 'vacant':
                    play_sound(self.audio_path)
                    self.log_callback("检测到空缺，已播放提示音")
                
                self.last_status = current_status
                
            except Exception as e:
                self.log_callback(f"监控错误: {str(e)}")
            
            time.sleep(interval)
