"""管理员权限检测与提权"""
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def require_admin():
    """若非管理员，弹窗提示并以管理员重启，然后退出当前进程"""
    if is_admin():
        return
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    if messagebox.askyesno("需要管理员权限", "该程序需要管理员权限才能正常运行。\n是否以管理员身份重新启动？"):
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
        )
    root.destroy()
    sys.exit()
