"""打包脚本 - 生成 K-{VERSION}.exe"""
import subprocess
import sys
import re
import os
import shutil

# 清理旧的打包文件
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('__pycache__'):
    shutil.rmtree('__pycache__')

# 删除所有 .pyc 文件
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pyc'):
            os.remove(os.path.join(root, file))
    if '__pycache__' in dirs:
        shutil.rmtree(os.path.join(root, '__pycache__'))

# 读取版本号
with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'VERSION = "(\d+)"', content)
    if match:
        version = match.group(1)
    else:
        print("无法读取版本号")
        sys.exit(1)

exe_name = f"K-{version}"

print(f"=== 开始打包 {exe_name}.exe ===")
print(f"版本号: {version}")

# PyInstaller 命令
cmd = [
    'pyinstaller',
    '--onefile',
    '--windowed',
    '--name', exe_name,
    '--clean',
    '--noconfirm',
    'gui.py'
]

result = subprocess.run(cmd)

if result.returncode == 0:
    print(f"\n=== 打包成功 ===")
    print(f"文件位置: dist/{exe_name}.exe")
    print(f"版本: v{version}")
else:
    print("\n打包失败")
    sys.exit(1)
