"""窗口捕获模块 - 支持后台窗口截图"""
import win32gui
import win32ui
import win32con
import win32process
from ctypes import windll
from PIL import Image

def list_windows():
    """列出所有可见窗口，返回 (hwnd, title, pid, width, height)"""
    windows = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            windows.append((hwnd, title, pid, width, height))
    win32gui.EnumWindows(callback, None)
    return windows

def capture_window(hwnd, region=None):
    """
    捕获窗口图像（支持后台窗口）
    region: (center_x, center_y, radius) 圆形区域，或 (x, y, width, height) 矩形区域
    """
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        if region:
            if len(region) == 3:
                # 圆形区域
                cx, cy, radius = region
                # 裁剪为正方形包围盒
                x1 = max(0, cx - radius)
                y1 = max(0, cy - radius)
                x2 = min(width, cx + radius)
                y2 = min(height, cy + radius)
                img = img.crop((x1, y1, x2, y2))
            else:
                # 矩形区域（兼容旧版）
                x, y, w, h = region
                img = img.crop((x, y, x + w, y + h))
        
        return img if result == 1 else None
    except:
        return None
