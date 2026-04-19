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
        self.sound_enabled = True
        self.running = False
        self.thread = None
        self.last_alert_time = 0
    
    def set_audio(self, path):
        self.audio_path = path
    
    def set_sound_enabled(self, enabled):
        self.sound_enabled = enabled
    
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
                
                status = detect_status(img)
                
                if status == 'green':
                    self.status_var.set("有绿色")
                    self.last_alert_time = 0  # 重置提醒计时
                else:
                    self.status_var.set("无绿色")
                    now = time.time()
                    # 无绿色且距上次提醒>=15秒，播放提示音（如果启用）
                    if now - self.last_alert_time >= 15:
                        if self.sound_enabled:
                            play_sound(self.audio_path)
                            self.log_callback("无绿色，已提醒")
                        else:
                            self.log_callback("无绿色（静音）")
                        self.last_alert_time = now
                
            except Exception as e:
                self.log_callback(f"错误: {str(e)}")
            
            time.sleep(interval)
