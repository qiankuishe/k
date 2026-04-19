"""管理员权限检测与静默提权"""
import sys
import ctypes
import os
import subprocess

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def kill_old_instances():
    """杀掉所有运行 gui.py 或 game_monitor.py 的 python 进程"""
    try:
        current_pid = os.getpid()
        # 使用 wmic 获取所有 python 进程
        result = subprocess.run(
            ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'ProcessId,CommandLine', '/format:csv'],
            capture_output=True, text=True, timeout=3
        )
        
        for line in result.stdout.splitlines():
            if 'gui.py' in line or 'game_monitor.py' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        pid = int(parts[-1].strip())
                        if pid != current_pid:
                            subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                         capture_output=True, timeout=2)
                    except:
                        pass
    except:
        pass

def require_admin():
    """若非管理员，静默以管理员重启并退出当前进程"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
        )
        sys.exit()
    # 管理员模式下，杀掉旧实例
    kill_old_instances()
