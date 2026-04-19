"""颜色检测逻辑"""
import numpy as np

def detect_status(img):
    """检测区域是否有绿色。返回: 'green' 或 'no_green'"""
    if img is None:
        return 'no_green'
    
    arr = np.array(img)
    
    # 绿色判定条件进一步放宽：G通道 > R+15 且 G通道 > B+15 且 G > 50
    green_mask = (arr[:, :, 1] > arr[:, :, 0] + 15) & \
                 (arr[:, :, 1] > arr[:, :, 2] + 15) & \
                 (arr[:, :, 1] > 50)
    
    # 绿色像素占比超过1%认为有绿色（从3%降低到1%，更敏感）
    green_ratio = np.sum(green_mask) / green_mask.size
    return 'green' if green_ratio > 0.01 else 'no_green'
