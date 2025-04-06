from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QLabel, QApplication, QPushButton, QCheckBox
import sys
import json
import os

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设置")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 添加标签页
        self.tabs.addTab(self.create_general_tab(), "常规")
        self.tabs.addTab(self.create_advanced_tab(), "高级")
        self.tabs.addTab(self.create_about_tab(), "关于")
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # 加载设置
        self.load_settings()
    
    def create_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("功能设置"))

        self.htmlwidget = QCheckBox("开启html小组件")
        self.htmlwidget.setChecked(True)  # 默认开启
        layout.addWidget(self.htmlwidget)

        self.mdwidget = QCheckBox("开启Markdown小组件")
        self.mdwidget.setChecked(True)  # 默认开启
        layout.addWidget(self.mdwidget)

        self.qs = QCheckBox("开启快速启动栏")
        self.qs.setChecked(True)  # 默认开启
        layout.addWidget(self.qs)
        
        # 添加开启自启的设置
        self.auto_start_checkbox = QCheckBox("开启自启动")
        self.auto_start_checkbox.setChecked(False)  # 默认关闭
        layout.addWidget(self.auto_start_checkbox)
        
        # 添加保存设置按钮
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        tab.setLayout(layout)
        return tab
    
    def save_settings(self):
        settings = {
            "html_widget_enabled": self.htmlwidget.isChecked(),
            "md_widget_enabled": self.mdwidget.isChecked(),
            "qs_enabled": self.qs.isChecked(),
            "auto_start_enabled": self.auto_start_checkbox.isChecked()
        }
        
        # 确保 data 文件夹存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 保存设置到 app.json
        with open(os.path.join(data_dir, "app.json"), "w") as f:
            json.dump(settings, f)
        
        # 实现开机自启逻辑
        if settings["auto_start_enabled"]:
            self.enable_auto_start()
        else:
            self.disable_auto_start()
        # 关闭设置窗口
        self.destroy()
    
    def load_settings(self):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        settings_file = os.path.join(data_dir, "app.json")
        
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = json.load(f)
                self.auto_start_checkbox.setChecked(settings.get("auto_start_enabled", False))
                self.htmlwidget.setChecked(settings.get("html_widget_enabled", True))
                self.mdwidget.setChecked(settings.get("md_widget_enabled", True))
                self.qs.setChecked(settings.get("qs_enabled", True))

    def enable_auto_start(self):
        # 实现开机自启逻辑
        if sys.platform == "win32":
            import winshell
            from win32com.client import Dispatch
            
            # 获取启动文件夹路径
            startup_folder = winshell.startup()
            
            # 获取当前程序的路径
            exe_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "cpmain.py"))
            
            # 创建快捷方式
            shortcut_path = os.path.join(startup_folder, "ClassPro.lnk")
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.save()
    
    def disable_auto_start(self):
        # 取消开机自启逻辑
        if sys.platform == "win32":
            import winshell
            
            # 获取启动文件夹路径
            startup_folder = winshell.startup()
            
            # 删除快捷方式
            shortcut_path = os.path.join(startup_folder, "ClassPro.lnk")
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)

    def create_advanced_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("暂无设置项"))
        tab.setLayout(layout)
        return tab
    def create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        markdown_text_edit = QLabel("""
            <img src="cp.ico" />
            <h1>Class Pro</h1>
            <p>版本1.0.0</p>
        """)
        layout.addWidget(markdown_text_edit)
        
        tab.setLayout(layout)
        return tab

def start_app():
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())