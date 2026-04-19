"""提示音播放系统"""
import pygame
import threading

# 初始化 pygame mixer
pygame.mixer.init()

def play_sound(audio_path=None, volume=1.0):
    """
    播放提示音
    audio_path: 音频文件路径，None则播放系统蜂鸣声
    volume: 音量 0.0-1.0
    """
    def _play():
        try:
            if audio_path:
                sound = pygame.mixer.Sound(audio_path)
                sound.set_volume(volume)
                sound.play()
            else:
                # 无音频文件，播放系统蜂鸣声
                import winsound
                winsound.Beep(1000, 500)
        except:
            # 失败时播放系统蜂鸣声
            import winsound
            winsound.Beep(1000, 500)
    
    threading.Thread(target=_play, daemon=True).start()
