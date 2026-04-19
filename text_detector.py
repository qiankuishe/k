"""OCR文字识别逻辑 - 识别房间人数 (4/4格式)"""
import numpy as np
from PIL import Image, ImageEnhance
import pytesseract

def detect_status(img):
    """识别矩形区域内的文字，判断是否满人。返回: (status, text)"""
    if img is None:
        return 'no_green', '未识别'
    
    try:
        # 图像预处理
        # 1. 放大图像
        width, height = img.size
        img_large = img.resize((width * 4, height * 4), Image.LANCZOS)
        
        # 2. 转灰度
        img_gray = img_large.convert('L')
        
        # 3. 增强对比度
        enhancer = ImageEnhance.Contrast(img_gray)
        img_contrast = enhancer.enhance(2.0)
        
        # 4. 二值化（白色文字变黑色，背景变白色，适合OCR）
        arr = np.array(img_contrast)
        # 反转：白色文字(高值) -> 黑色(0), 蓝色背景(低值) -> 白色(255)
        arr_inv = 255 - arr
        threshold = np.mean(arr_inv)
        arr_binary = np.where(arr_inv > threshold, 0, 255).astype(np.uint8)
        img_binary = Image.fromarray(arr_binary)
        
        # 5. OCR识别
        text = pytesseract.image_to_string(
            img_binary, 
            config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789/'
        )
        text = text.strip().replace(' ', '').replace('\n', '').replace('|', '/')
        
        # 调试输出
        if not hasattr(detect_status, 'debug_count'):
            detect_status.debug_count = 0
        if detect_status.debug_count < 5:
            print(f"[调试] OCR识别结果: '{text}'")
            img_binary.save(f"debug_ocr_{detect_status.debug_count}.png")
            detect_status.debug_count += 1
        
        # 判断是否满人
        if '4/4' in text or '4／4' in text:
            return 'green', '4/4'  # 满人
        elif '3/4' in text or '3／4' in text:
            return 'no_green', '3/4'  # 有空位
        elif '2/4' in text or '2／4' in text:
            return 'no_green', '2/4'  # 有空位
        else:
            return 'no_green', '未识别'  # 识别失败
    
    except Exception as e:
        print(f"[错误] OCR识别失败: {e}")
        return 'no_green', '错误'
