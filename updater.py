"""GitHub 自动更新模块"""
import requests
import os
import sys
import subprocess
from pathlib import Path

REPO = "qiankuishe/k"
CURRENT_VERSION = None  # 由 gui.py 传入

def check_update(current_version):
    """检查是否有新版本"""
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None, None
        
        data = resp.json()
        latest_version = data['tag_name'].lstrip('v')
        
        if int(latest_version) > int(current_version):
            # 查找 exe 下载链接
            for asset in data.get('assets', []):
                if asset['name'].startswith('K-') and asset['name'].endswith('.exe'):
                    return latest_version, asset['browser_download_url']
        return None, None
    except:
        return None, None

def download_and_update(download_url, new_version):
    """下载新版本并替换当前 exe"""
    try:
        # 下载到临时文件
        temp_file = Path(f"K-{new_version}.exe.tmp")
        resp = requests.get(download_url, stream=True, timeout=30)
        with open(temp_file, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 创建更新脚本（bat）
        current_exe = sys.executable if getattr(sys, 'frozen', False) else None
        if not current_exe:
            return False
        
        new_exe = Path(f"K-{new_version}.exe")
        bat_script = f"""@echo off
timeout /t 2 /nobreak >nul
del /f /q "{current_exe}"
move /y "{temp_file}" "{new_exe}"
start "" "{new_exe}"
del "%~f0"
"""
        bat_file = Path("update.bat")
        bat_file.write_text(bat_script, encoding='gbk')
        
        # 执行更新脚本并退出
        subprocess.Popen(['cmd', '/c', str(bat_file)], 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit()
        
    except Exception as e:
        return False
