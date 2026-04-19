"""颜色检测逻辑"""
import numpy as np

def detect_status(img):
    """检测区域是否有绿色。返回: 'green' 或 'no_green'"""
    if img is None:
        return 'no_green'
    
    arr = np.array(img)
    
    # 多种绿色检测策略
    # 策略1：标准绿色 (G > R+15 且 G > B+15)
    green_mask1 = (arr[:, :, 1] > arr[:, :, 0] + 15) & \
                  (arr[:, :, 1] > arr[:, :, 2] + 15) & \
                  (arr[:, :, 1] > 50)
    
    # 策略2：宽松绿色 (G > R+10 且 G > B+10)
    green_mask2 = (arr[:, :, 1] > arr[:, :, 0] + 10) & \
                  (arr[:, :, 1] > arr[:, :, 2] + 10) & \
                  (arr[:, :, 1] > 40)
    
    # 策略3：任何绿色倾向 (G 是最大通道)
    green_mask3 = (arr[:, :, 1] > arr[:, :, 0]) & \
                  (arr[:, :, 1] > arr[:, :, 2]) & \
                  (arr[:, :, 1] > 30)
    
    # 合并所有策略
    green_mask = green_mask1 | green_mask2 | green_mask3
    
    # 绿色像素占比超过0.5%认为有绿色
    green_ratio = np.sum(green_mask) / green_mask.size
    
    # 调试输出（前3次）
    if not hasattr(detect_status, 'debug_count'):
        detect_status.debug_count = 0
    if detect_status.debug_count < 3:
        print(f"[调试] 绿色占比: {green_ratio*100:.2f}%, 平均RGB: R={np.mean(arr[:,:,0]):.1f} G={np.mean(arr[:,:,1]):.1f} B={np.mean(arr[:,:,2]):.1f}")
        detect_status.debug_count += 1
    
    return 'green' if green_ratio > 0.005 else 'no_green'
