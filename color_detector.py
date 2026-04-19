"""颜色检测逻辑"""
import numpy as np

def detect_status(img):
    """检测区域是否有绿色。返回: 'green' 或 'no_green'"""
    if img is None:
        return 'no_green'
    
    arr = np.array(img)
    
    # 绿色判定条件放宽：G通道 > R+20 且 G通道 > B+20 且 G > 60
    green_mask = (arr[:, :, 1] > arr[:, :, 0] + 20) & \
                 (arr[:, :, 1] > arr[:, :, 2] + 20) & \
                 (arr[:, :, 1] > 60)
    
    # 绿色像素占比超过3%认为有绿色（从5%降低到3%）
    green_ratio = np.sum(green_mask) / green_mask.size
    return 'green' if green_ratio > 0.03 else 'no_green'
