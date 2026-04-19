"""OCR文字识别逻辑 - 识别房间人数"""
import numpy as np
from PIL import Image
import pytesseract

def detect_status(img):
    """识别圆形区域内的文字，判断是否满人。返回: 'green' 或 'no_green'"""
    if img is None:
        return 'no_green'
    
    try:
        # 图像预处理：转灰度、二值化、放大
        img_gray = img.convert('L')
        
        # 放大图像提高识别率
        width, height = img_gray.size
        img_large = img_gray.resize((width * 3, height * 3), Image.LANCZOS)
        
        # 二值化处理
        arr = np.array(img_large)
        threshold = np.mean(arr)
        arr_binary = np.where(arr > threshold, 255, 0).astype(np.uint8)
        img_binary = Image.fromarray(arr_binary)
        
        # OCR识别（只识别数字和斜杠）
        text = pytesseract.image_to_string(img_binary, config='--psm 7 -c tessedit_char_whitelist=0123456789/')
        text = text.strip().replace(' ', '').replace('\n', '')
        
        # 调试输出
        if not hasattr(detect_status, 'debug_count'):
            detect_status.debug_count = 0
        if detect_status.debug_count < 5:
            print(f"[调试] OCR识别结果: '{text}'")
            detect_status.debug_count += 1
        
        # 判断是否满人
        if '4/4' in text or '4／4' in text:
            return 'green'  # 满人
        elif '/4' in text or '／4' in text:
            return 'no_green'  # 有空位 (2/4, 3/4)
        else:
            # 识别失败，回退到颜色检测
            return detect_by_color(img)
    
    except Exception as e:
        # OCR失败，回退到颜色检测
        return detect_by_color(img)

def detect_by_color(img):
    """备用方案：颜色检测"""
    arr = np.array(img)
    height, width = arr.shape[:2]
    
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 2
    
    y, x = np.ogrid[:height, :width]
    circle_mask = (x - center_x)**2 + (y - center_y)**2 <= radius**2
    circle_pixels = arr[circle_mask]
    
    if len(circle_pixels) == 0:
        return 'no_green'
    
    # 简单的绿色检测
    green_mask = (circle_pixels[:, 1] > circle_pixels[:, 0] + 15) & \
                 (circle_pixels[:, 1] > circle_pixels[:, 2] + 15) & \
                 (circle_pixels[:, 1] > 50)
    
    green_pixels = np.sum(green_mask)
    return 'green' if green_pixels > 3 else 'no_green'
