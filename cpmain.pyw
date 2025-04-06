import pystray,sys,os,threading,json
from PIL import Image
from CPCore import*
import subprocess

def load_settings():
    settings_file = os.path.join("data/app.json")
    
    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            settings = json.load(f)
            return settings
    return {
        "html_widget_enabled": True,
        "md_widget_enabled": True,
        "qs_enabled": True,
        "auto_start_enabled": False
    }

def baricon():
    menu = pystray.Menu(
        pystray.MenuItem('设置', lambda: threading.Thread(target=Settings.start_app).start()), 
        pystray.MenuItem('退出', lambda: exitapp("defult")),
        )

    image = Image.open("cp.ico")

    icon = pystray.Icon("name", title=f"Class Pro", icon=image, menu=menu) # type: ignore
    icon.run()

def exitapp(mode):
    """
    退出ClassPro

    :param mode: 模式，可选值：
        "defult"：退出，
        "restart"：重启（不知道该放哪所以做到这来了）。
    """
    if mode == "defult":
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["taskkill", "/f", "/im", "pythonw.exe"],
                      creationflags=subprocess.CREATE_NO_WINDOW)
    elif mode == "restart":

        p = sys.executable
        try:
            # 启动新程序(解释器路径, 当前程序)
            os.execl(p, p, *sys.argv)
        except OSError:
            # 关闭当前程序
            sys.exit()

if __name__ == "__main__":
    print(
        """
   _____ _                   _____           
  / ____| |                 |  __ \          
 | |    | | __ _ ___ ___    | |__) | __ ___  
 | |    | |/ _` / __/ __|   |  ___/ '__/ _ \ 
 | |____| | (_| \__ \__ \   | |   | | | (_) |
  \_____|_|\__,_|___/___/   |_|   |_|  \___/
  """)
    
    settings = load_settings()
    
    if settings.get("qs_enabled", True):
        threading.Thread(target=lambda: subprocess.run(["python", "springboard.py", "qs"], creationflags=subprocess.CREATE_NO_WINDOW)).start()
    if settings.get("md_widget_enabled", True):
        threading.Thread(target=lambda: subprocess.run(["python", "springboard.py", "mdwidget"], creationflags=subprocess.CREATE_NO_WINDOW)).start()
    if settings.get("html_widget_enabled", True):
        threading.Thread(target=lambda: subprocess.run(["python", "springboard.py", "htmlwidget"], creationflags=subprocess.CREATE_NO_WINDOW)).start()
    
    baricon()