"""管理员权限检测与静默提权"""
import sys
import ctypes
import os
import subprocess
import time

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def kill_all_python():
    """杀掉所有 python.exe 进程（除了当前进程）"""
    try:
        current_pid = os.getpid()
        # 使用 tasklist 获取所有 python.exe 的 PID
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
                              capture_output=True, text=True, timeout=3)
        
        for line in result.stdout.strip().split('\n'):
            if 'python.exe' in line:
                parts = line.replace('"', '').split(',')
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        if pid != current_pid:
                            subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                                         capture_output=True, timeout=2)
                    except:
                        pass
        time.sleep(0.5)  # 等待进程完全退出
    except:
        pass

def require_admin():
    """若非管理员，静默以管理员重启并退出当前进程"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
        )
        sys.exit()
    # 管理员模式下，杀掉所有旧 python 进程
    kill_all_python()
