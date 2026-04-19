"""颜色检测逻辑"""
import numpy as np

def detect_status(img):
    """检测区域是否有绿色。返回: 'green' 或 'no_green'"""
    if img is None:
        return 'no_green'
    
    arr = np.array(img)
    # 绿色判定：G通道 > R+30 且 G通道 > B+30 且 G > 70
    green_mask = (arr[:, :, 1] > arr[:, :, 0] + 30) & \
                 (arr[:, :, 1] > arr[:, :, 2] + 30) & \
                 (arr[:, :, 1] > 70)
    
    # 绿色像素占比超过5%认为有绿色
    green_ratio = np.sum(green_mask) / green_mask.size
    return 'green' if green_ratio > 0.05 else 'no_green'
