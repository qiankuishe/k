"""打包脚本 - 生成 K-{VERSION}.exe"""
import subprocess
import sys
import re

# 读取版本号
with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'VERSION = "(\d+)"', content)
    if match:
        version = match.group(1)
    else:
        print("无法读取版本号")
        sys.exit(1)

exe_name = f"K-{version}.exe"

# PyInstaller 命令
cmd = [
    'pyinstaller',
    '--onefile',
    '--windowed',
    '--name', exe_name.replace('.exe', ''),
    '--icon=NONE',
    '--add-data', 'requirements.txt;.',
    'gui.py'
]

print(f"正在打包 {exe_name}...")
subprocess.run(cmd, check=True)
print(f"\n打包完成: dist/{exe_name}")
