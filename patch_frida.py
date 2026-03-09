# -*- coding: utf-8 -*-
"""
Frida 魔改脚本 - 去除检测特征
针对 Frida 16.4.7

特征修改:
1. 默认端口 27042 -> 随机端口
2. re.frida.server -> 随机名称
3. frida-agent -> 随机名称
4. frida-server 线程名 -> 随机名称
5. gum-js-loop 线程名 -> 随机名称
"""

import os
import re
import random
import string

# 配置
FRIDA_ROOT = r"E:\frida-16.4.7"
RANDOM_SUFFIX = ''.join(random.choices(string.ascii_lowercase, k=4))

# 替换规则 - 完整版
REPLACEMENTS = {
    # ===== 端口特征 =====
    "27042": "39042",
    "27052": "39052",
    
    # ===== 目录名特征 =====
    "re.frida.server": "re.xmsf.helper",
    
    # ===== 线程名特征 =====
    "frida-server-main-loop": "pool-main-loop",
    "gum-js-loop": "v8-loop",
    "frida-agent-container": "jni-container",
    "frida-agent-emulated": "dex-emulated",
    
    # ===== D-Bus/RPC 特征 =====
    "frida:rpc": "xmsf:rpc",
    
    # ===== SO名称特征 =====
    "frida-agent-arm.so": "libxmsf-arm.so",
    "frida-agent-arm64.so": "libxmsf-arm64.so",
    "frida-agent-32.so": "libxmsf-32.so",
    "frida-agent-64.so": "libxmsf-64.so",
    'frida-agent-<arch>.so': 'libxmsf-<arch>.so',
    "frida-agent.dll": "libxmsf.dll",
    
    # ===== Gadget特征 =====
    "FridaGadget": "NativeHelper",
    "frida-gadget": "native-helper",
}

# 需要处理的文件扩展名
EXTENSIONS = ['.vala', '.c', '.h', '.py', '.js']

def should_process(filepath):
    """判断是否需要处理该文件"""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in EXTENSIONS

def patch_file(filepath, replacements):
    """修改单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"  [!] 读取失败: {e}")
        return False
    
    original = content
    changes = []
    
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            changes.append(f"{old} -> {new}")
    
    if content != original:
        try:
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            print(f"  [+] {filepath}")
            for c in changes:
                print(f"      {c}")
            return True
        except Exception as e:
            print(f"  [!] 写入失败: {e}")
            return False
    
    return False

def patch_directory(directory, replacements):
    """递归处理目录"""
    modified_count = 0
    
    for root, dirs, files in os.walk(directory):
        # 跳过.git目录
        if '.git' in root:
            continue
        
        for filename in files:
            filepath = os.path.join(root, filename)
            if should_process(filepath):
                if patch_file(filepath, replacements):
                    modified_count += 1
    
    return modified_count

def main():
    print("=" * 60)
    print("Frida 魔改脚本 - 去除检测特征")
    print("=" * 60)
    print()
    print(f"[*] Frida目录: {FRIDA_ROOT}")
    print(f"[*] 随机后缀: {RANDOM_SUFFIX}")
    print()
    print("[*] 替换规则:")
    for old, new in REPLACEMENTS.items():
        print(f"    {old} -> {new}")
    print()
    
    # 处理核心目录
    directories = [
        os.path.join(FRIDA_ROOT, "subprojects", "frida-core"),
        os.path.join(FRIDA_ROOT, "subprojects", "frida-gum"),
    ]
    
    total_modified = 0
    for directory in directories:
        if os.path.exists(directory):
            print(f"\n[*] 处理目录: {directory}")
            count = patch_directory(directory, REPLACEMENTS)
            total_modified += count
            print(f"    修改了 {count} 个文件")
    
    print()
    print("=" * 60)
    print(f"[+] 完成! 共修改 {total_modified} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
