"""GitHub 自动更新模块 - 支持国内镜像加速"""
import requests
import os
import sys
import subprocess
from pathlib import Path

REPO = "qiankuishe/k"

# API 端点列表（按优先级）
API_ENDPOINTS = [
    f"https://api.github.com/repos/{REPO}/releases/latest",  # 官方 API
    "https://ghproxy.com/https://api.github.com/repos/qiankuishe/k/releases/latest",  # ghproxy 镜像
]

# 下载镜像列表
DOWNLOAD_MIRRORS = [
    "",  # 原始链接
    "https://ghproxy.com/",  # ghproxy
    "https://mirror.ghproxy.com/",  # ghproxy 备用
]

def check_update(current_version):
    """检查是否有新版本"""
    for api_url in API_ENDPOINTS:
        try:
            resp = requests.get(api_url, timeout=8)
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            latest_version = data['tag_name'].lstrip('v')
            
            if int(latest_version) > int(current_version):
                # 查找 exe 下载链接
                for asset in data.get('assets', []):
                    if asset['name'].startswith('K-') and asset['name'].endswith('.exe'):
                        return latest_version, asset['browser_download_url']
            return None, None
        except:
            continue
    
    return None, None

def download_and_update(download_url, new_version, cancel_check=None):
    """下载新版本并替换当前 exe"""
    temp_file = Path(f"K-{new_version}.exe.tmp")
    
    # 尝试多个镜像下载
    for mirror in DOWNLOAD_MIRRORS:
        if cancel_check and cancel_check():
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
            return False
        
        try:
            url = mirror + download_url if mirror else download_url
            resp = requests.get(url, stream=True, timeout=30)
            
            if resp.status_code == 200:
                with open(temp_file, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if cancel_check and cancel_check():
                            # 取消下载，删除临时文件
                            f.close()
                            temp_file.unlink()
                            return False
                        f.write(chunk)
                
                # 下载成功，执行更新
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
                
                subprocess.Popen(['cmd', '/c', str(bat_file)], 
                                creationflags=subprocess.CREATE_NO_WINDOW)
                sys.exit()
        except:
            continue
    
    return False
