"""颜色检测逻辑 - 针对小图标优化"""
import numpy as np

def detect_status(img):
    """检测区域是否有绿色。返回: 'green' 或 'no_green'"""
    if img is None:
        return 'no_green'
    
    arr = np.array(img)
    
    # 针对这种小图标的绿色检测
    # 绿色特征：G通道明显高于R和B，且G值较高
    
    # 策略1：明显的绿色 (G > 100 且 G > R*1.3 且 G > B*1.3)
    green_mask1 = (arr[:, :, 1] > 100) & \
                  (arr[:, :, 1] > arr[:, :, 0] * 1.3) & \
                  (arr[:, :, 1] > arr[:, :, 2] * 1.3)
    
    # 策略2：中等绿色 (G > 80 且 G > R+30 且 G > B+30)
    green_mask2 = (arr[:, :, 1] > 80) & \
                  (arr[:, :, 1] > arr[:, :, 0] + 30) & \
                  (arr[:, :, 1] > arr[:, :, 2] + 30)
    
    # 策略3：浅绿色 (G > 60 且 G > R+20 且 G > B+20)
    green_mask3 = (arr[:, :, 1] > 60) & \
                  (arr[:, :, 1] > arr[:, :, 0] + 20) & \
                  (arr[:, :, 1] > arr[:, :, 2] + 20)
    
    # 合并策略
    green_mask = green_mask1 | green_mask2 | green_mask3
    
    # 计算绿色像素数量（不是占比，因为图标很小）
    green_pixels = np.sum(green_mask)
    
    # 调试输出
    if not hasattr(detect_status, 'debug_count'):
        detect_status.debug_count = 0
    if detect_status.debug_count < 5:
        avg_r = np.mean(arr[:,:,0])
        avg_g = np.mean(arr[:,:,1])
        avg_b = np.mean(arr[:,:,2])
        max_g = np.max(arr[:,:,1])
        print(f"[调试] 绿色像素数: {green_pixels}, 平均RGB: R={avg_r:.1f} G={avg_g:.1f} B={avg_b:.1f}, 最大G={max_g}")
        detect_status.debug_count += 1
    
    # 只要有超过5个绿色像素就认为是绿色（图标很小）
    return 'green' if green_pixels > 5 else 'no_green'
