"""颜色检测逻辑 - 只检测圆形内部像素"""
import numpy as np

def detect_status(img):
    """检测圆形区域内是否有绿色。返回: 'green' 或 'no_green'"""
    if img is None:
        return 'no_green'
    
    arr = np.array(img)
    height, width = arr.shape[:2]
    
    # 创建圆形遮罩（只检测圆内像素）
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 2
    
    y, x = np.ogrid[:height, :width]
    circle_mask = (x - center_x)**2 + (y - center_y)**2 <= radius**2
    
    # 只分析圆内的像素
    circle_pixels = arr[circle_mask]
    
    if len(circle_pixels) == 0:
        return 'no_green'
    
    # 绿色检测：G通道明显高于R和B
    # 策略1：明显绿色 (G > 100 且 G > R*1.3 且 G > B*1.3)
    green_mask1 = (circle_pixels[:, 1] > 100) & \
                  (circle_pixels[:, 1] > circle_pixels[:, 0] * 1.3) & \
                  (circle_pixels[:, 1] > circle_pixels[:, 2] * 1.3)
    
    # 策略2：中等绿色 (G > 80 且 G > R+30 且 G > B+30)
    green_mask2 = (circle_pixels[:, 1] > 80) & \
                  (circle_pixels[:, 1] > circle_pixels[:, 0] + 30) & \
                  (circle_pixels[:, 1] > circle_pixels[:, 2] + 30)
    
    # 策略3：浅绿色 (G > 60 且 G > R+20 且 G > B+20)
    green_mask3 = (circle_pixels[:, 1] > 60) & \
                  (circle_pixels[:, 1] > circle_pixels[:, 0] + 20) & \
                  (circle_pixels[:, 1] > circle_pixels[:, 2] + 20)
    
    # 合并策略
    green_mask = green_mask1 | green_mask2 | green_mask3
    green_pixels = np.sum(green_mask)
    
    # 调试输出
    if not hasattr(detect_status, 'debug_count'):
        detect_status.debug_count = 0
    if detect_status.debug_count < 5:
        avg_r = np.mean(circle_pixels[:, 0])
        avg_g = np.mean(circle_pixels[:, 1])
        avg_b = np.mean(circle_pixels[:, 2])
        max_g = np.max(circle_pixels[:, 1])
        print(f"[调试] 圆内像素数: {len(circle_pixels)}, 绿色像素: {green_pixels}, 平均RGB: R={avg_r:.1f} G={avg_g:.1f} B={avg_b:.1f}, 最大G={max_g}")
        detect_status.debug_count += 1
    
    # 只要有超过5个绿色像素就认为是绿色
    return 'green' if green_pixels > 5 else 'no_green'
