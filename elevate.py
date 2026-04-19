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
        current_name = os.path.basename(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # 跳过当前进程
                if proc.info['pid'] == current_pid:
                    continue
                # 匹配 python 进程运行同一脚本，或同名 exe
                if proc.info['cmdline'] and len(proc.info['cmdline']) > 1:
                    if sys.argv[0] in ' '.join(proc.info['cmdline']):
                        proc.kill()
                elif proc.info['name'] == current_name:
                    proc.kill()
            except:
                pass
    except ImportError:
        pass  # psutil 未安装则跳过

def require_admin():
    """若非管理员，静默以管理员重启并退出当前进程"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
        )
        sys.exit()
    # 管理员模式下，杀掉旧实例
    kill_old_instances()
