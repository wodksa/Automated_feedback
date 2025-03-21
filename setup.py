import subprocess
import sys

def install_dependencies():
    print("正在安装所需的依赖...")
    
    dependencies = [
        "pandas",
        "PyQt5",
        "openai"
    ]
    
    for dep in dependencies:
        print(f"安装 {dep}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
    
    print("所有依赖安装完成！")
    print("现在您可以运行 chat_analyzer.py 启动应用程序")

if __name__ == "__main__":
    install_dependencies()