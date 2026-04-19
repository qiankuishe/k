"""管理员权限检测与静默提权"""
import sys
import ctypes
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def kill_old_instances():
    """杀掉所有同名进程（除了当前进程）"""
    try:
        import psutil
        current_pid = os.getpid()
        script_name = os.path.basename(sys.argv[0])  # gui.py 或 game_monitor.py
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                
                # 检查是否是 python 进程运行 gui.py 或 game_monitor.py
                cmdline = proc.info.get('cmdline')
                if cmdline and isinstance(cmdline, list):
                    cmdline_str = ' '.join(cmdline)
                    if 'python' in proc.info['name'].lower() and \
                       ('gui.py' in cmdline_str or 'game_monitor.py' in cmdline_str):
                        proc.kill()
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
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
