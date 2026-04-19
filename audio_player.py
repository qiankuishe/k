"""提示音播放系统"""
import winsound
import threading

def play_sound(audio_path=None):
    """
    播放提示音
    audio_path: 音频文件路径，None则播放系统蜂鸣声
    """
    def _play():
        try:
            if audio_path:
                winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            else:
                winsound.Beep(1000, 500)
        except:
            winsound.Beep(1000, 500)
    
    threading.Thread(target=_play, daemon=True).start()
