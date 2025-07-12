#!/usr/bin/env python
"""
安装Flask Session管理所需的依赖
"""
import subprocess
import sys
import os

def install_dependencies():
    print("安装会话管理依赖...")
    dependencies = ["Flask-Session"]
    

    try:
        print("尝试安装Redis客户端...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "redis"])
        print("✅ Redis客户端安装成功")
        dependencies.append("redis")
    except subprocess.CalledProcessError:
        print("⚠️ Redis客户端安装失败，将使用文件系统存储会话")
    

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + dependencies)
        print("✅ Flask-Session安装成功")
    except subprocess.CalledProcessError:
        print("❌ Flask-Session安装失败，请手动安装: pip install Flask-Session")
        return False
    

    try:
        session_dirs = ['/tmp/flask_session', 'flask_session']
        for dir_path in session_dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"✅ 会话存储目录创建成功: {dir_path}")
    except Exception as e:
        print(f"⚠️ 创建会话存储目录失败: {str(e)}")
    

    try:
        for dir_path in session_dirs:
            if os.path.exists(dir_path):
                os.chmod(dir_path, 0o777)  # 设置全局可写权限
                print(f"✅ 设置会话目录权限成功: {dir_path}")
    except Exception as e:
        print(f"⚠️ 设置目录权限失败: {str(e)}")
    
    print("\n配置完成！您的系统现在应该可以正确处理多设备会话。")
    print("请重启Flask应用以应用更改: sudo systemctl restart flask_hutb.service")
    return True

if __name__ == "__main__":
    install_dependencies() 