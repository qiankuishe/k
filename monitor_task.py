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
        self.last_alert_time = 0
    
    def set_audio(self, path):
        self.audio_path = path
    
    def start(self, interval, status_var):
        if self.running:
            return
        self.running = True
        self.status_var = status_var
        self.last_alert_time = 0
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
                status = detect_status(img)
                
                if status == 'green':
                    self.status_var.set("有绿色")
                    self.last_alert_time = 0  # 重置提醒计时
                else:
                    self.status_var.set("无绿色")
                    now = time.time()
                    # 无绿色且距上次提醒>=15秒，播放提示音
                    if now - self.last_alert_time >= 15:
                        play_sound(self.audio_path)
                        self.log_callback("无绿色，已提醒")
                        self.last_alert_time = now
                
            except Exception as e:
                self.log_callback(f"错误: {str(e)}")
            
            time.sleep(interval)
