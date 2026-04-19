"""颜色检测逻辑"""
import numpy as np
from PIL import Image

def detect_status(img):
    """
    检测图像主要颜色状态
    返回: 'full' (满员-绿色) 或 'vacant' (空缺-白色/黑色)
    """
    if img is None:
        return 'vacant'
    
    # 转换为numpy数组
    arr = np.array(img)
    
    # 计算平均RGB值
    avg_r = np.mean(arr[:, :, 0])
    avg_g = np.mean(arr[:, :, 1])
    avg_b = np.mean(arr[:, :, 2])
    
    # 绿色判定：绿色通道明显高于红蓝通道
    if avg_g > avg_r + 20 and avg_g > avg_b + 20 and avg_g > 80:
        return 'full'
    
    return 'vacant'
