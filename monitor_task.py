"""监控任务管理"""
import threading
import time
from window_capture import capture_window
from text_detector import detect_status
from audio_player import play_sound

class MonitorTask:
    def __init__(self, hwnd, region, log_callback):
        self.hwnd = hwnd
        self.region = region
        self.log_callback = log_callback
        self.audio_path = None
        self.sound_enabled = True
        self.volume = 1.0  # 音量 0.0-1.0
        self.running = False
        self.thread = None
        self.last_alert_time = 0
        self.no_green_start_time = None  # 记录首次检测到无绿色的时间
    
    def set_audio(self, path):
        self.audio_path = path
    
    def set_sound_enabled(self, enabled):
        self.sound_enabled = enabled
    
    def set_volume(self, volume):
        """设置音量 0.0-1.0"""
        self.volume = max(0.0, min(1.0, volume))
    
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
                
                # 调试：保存截图（仅前3次）
                if not hasattr(self, 'debug_count'):
                    self.debug_count = 0
                if self.debug_count < 3 and img:
                    img.save(f"debug_capture_{self.debug_count}.png")
                    self.debug_count += 1
                
                status, text = detect_status(img)
                now = time.time()
                
                if status == 'green':
                    self.status_var.set(text)  # 显示 "4/4"
                    self.no_green_start_time = None  # 重置防抖计时
                    self.last_alert_time = 0
                else:
                    self.status_var.set(text)  # 显示 "2/4", "3/4" 等
                    
                    # 首次检测到有空位，记录时间
                    if self.no_green_start_time is None:
                        self.no_green_start_time = now
                    
                    # 防抖：持续有空位超过8秒才开始提醒
                    if now - self.no_green_start_time >= 8:
                        # 每20秒重复提醒
                        if now - self.last_alert_time >= 20:
                            if self.sound_enabled:
                                play_sound(self.audio_path, self.volume)
                                self.log_callback(f"检测到空位 ({text})，已提醒")
                            else:
                                self.log_callback(f"检测到空位 ({text})（静音）")
                            self.last_alert_time = now
                
            except Exception as e:
                self.log_callback(f"错误: {str(e)}")
            
            time.sleep(interval)
