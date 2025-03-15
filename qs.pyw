import sys
import os
import time
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QGraphicsBlurEffect, QFileDialog, QVBoxLayout, QHBoxLayout, QMenu, QAction, 
                             QMessageBox, QLineEdit, QCheckBox,QCompleter)
from PyQt5.QtGui import QIcon, QPainter, QBrush, QColor, QPainterPath
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve,QSharedMemory,QMutex
import winreg

class QuickLaunchApp(QMainWindow):
    def __init__(self):
        # 检查是否已有实例运行
        self.mutex = QMutex()
        self.shared_memory = QSharedMemory("QuickLaunchApp")
        if self.shared_memory.attach():
            QMessageBox.warning(None, "警告", "程序已经在运行中！")
            sys.exit(1)
        self.shared_memory.create(1)
        
        super().__init__()
        self.initUI()
        self.loadSettings()
        self.restorePosition()

        self.initTimers()

        self.last_activity_time = time.time()

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(256)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.updateWeather)
        self.weather_timer.start(600000)
        self.updateWeather()

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def initUI(self):
        self.setWindowTitle("快速启动")
        self.setGeometry(100, 100, 400, 120)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(15, 15, 15, 10)

        self.title_label = QLabel("快速启动", self)
        self.title_label.setAlignment(Qt.AlignLeft)
        self.title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
            padding-bottom: 5px;
        """)
        self.layout.addWidget(self.title_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(15)
        self.layout.addLayout(self.button_layout)

        self.bottom_label = QLabel("天气获取中", self)
        self.bottom_label.setAlignment(Qt.AlignLeft)
        self.bottom_label.setStyleSheet("""
            font-size: 14px;
            color: #666666;
            padding-top: 5px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #e8e8e8);
            border-radius: 0 0 15px 15px;
            padding: 5px 10px;
        """)
        self.layout.addWidget(self.bottom_label)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self.drag_position = QPoint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

    def initTimers(self):
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.savePosition)
        self.position_timer.start(5000)

        self.ppt_check_timer = QTimer(self)
        self.ppt_check_timer.timeout.connect(self.checkPPTFullscreen)
        self.ppt_check_timer.start(1000)

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.checkInactivity)
        self.inactivity_timer.start(1000)

        self.cursor_check_timer = QTimer(self)
        self.cursor_check_timer.timeout.connect(self.checkCursorOverWindow)
        self.cursor_check_timer.start(100)

        self.color_timer = QTimer(self)
        self.color_timer.timeout.connect(self.updateWindowColor)
        self.color_timer.start(1000)

    def updateWindowColor(self):
        current_hour = time.localtime().tm_hour
        if 7 <= current_hour <= 19:
            self.central_widget.setStyleSheet("background-color: rgba(255, 255, 255, 200); color: black; border-radius: 10px; font-family: Microsoft YaHei;")
            self.bottom_label.setStyleSheet("font-size: 16px; color: blue;")  # 白天模式下天气文字为蓝色
            # 白天模式下应用名称文字为黑色
            for i in range(self.button_layout.count()):
                widget = self.button_layout.itemAt(i).layout()
                if widget:
                    label = widget.itemAt(1).widget()
                    if isinstance(label, QLabel):
                        label.setStyleSheet("font-size: 16px; color: black;")
        else:
            self.central_widget.setStyleSheet("background-color: rgba(0, 0, 0, 200); color: white; border-radius: 10px; font-family: Microsoft YaHei;")
            self.bottom_label.setStyleSheet("font-size: 16px; color: lightblue;")  # 深色模式下天气文字为浅蓝色
            self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")  # 深色模式下标题文字为白色
            # 深色模式下应用名称文字为白色
            for i in range(self.button_layout.count()):
                widget = self.button_layout.itemAt(i).layout()
                if widget:
                    label = widget.itemAt(1).widget()
                    if isinstance(label, QLabel):
                        label.setStyleSheet("font-size: 16px; color: white;")

    def checkCursorOverWindow(self):
        cursor_pos = self.cursor().pos()
        window_geometry = self.geometry()
        if window_geometry.contains(cursor_pos):
            self.restoreFromEdge()
            self.last_activity_time = time.time()

    def checkInactivity(self):
        if self.is_near_edge and time.time() - self.last_activity_time > 1:
            self.hideToEdge()

    def closeEvent(self, event):
        self.shared_memory.detach()
        self.savePosition()
        event.accept()

    def savePosition(self):
        if self.pos().x() != self.settings["position"]["x"] or self.pos().y() != self.settings["position"]["y"]:
            self.settings["position"] = {
                "x": self.pos().x(),
                "y": self.pos().y()
            }
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)

    def restorePosition(self):
        if "position" in self.settings:
            pos = self.settings["position"]
            self.move(pos["x"], pos["y"])
            self.checkEdgeSnap()

    def checkEdgeSnap(self):
        screen_geometry = QApplication.desktop().availableGeometry()
        pos = self.pos()
        width = self.width()
        height = self.height()

        # 检查左边缘
        if pos.x() <= 10:
            self.move(0, pos.y())
        # 检查右边缘
        elif pos.x() + width >= screen_geometry.width() - 15:
            self.move(screen_geometry.width() - width, pos.y())
        # 检查下边缘
        if pos.y() + height >= screen_geometry.height() - 15:
            self.move(pos.x(), screen_geometry.height() - height)

        # 检查是否靠近边缘（仅左右边缘）
        self.is_near_edge = (pos.x() <= 10 or pos.x() + width >= screen_geometry.width() - 15)

    def hideToEdge(self):
        screen_geometry = QApplication.desktop().availableGeometry()
        pos = self.pos()
        width = self.width()
        height = self.height()

        target_pos = None
        if pos.x() <= 10:  # 左边缘
            target_pos = QPoint(-width + 10, pos.y())
        elif pos.x() + width >= screen_geometry.width() - 15:  # 右边缘
            target_pos = QPoint(screen_geometry.width() - 10, pos.y())
        elif pos.y() + height >= screen_geometry.height() - 15:  # 下边缘
            target_pos = QPoint(pos.x(), screen_geometry.height() - 10)

        if target_pos:
            self.animation.setStartValue(self.pos())
            self.animation.setEndValue(target_pos)
            self.animation.start()

    def restoreFromEdge(self):
        screen_geometry = QApplication.desktop().availableGeometry()
        pos = self.pos()
        width = self.width()
        height = self.height()

        target_pos = None
        if pos.x() == -width + 10:  # 左边缘
            target_pos = QPoint(0, pos.y())
        elif pos.x() == screen_geometry.width() - 10:  # 右边缘
            target_pos = QPoint(screen_geometry.width() - width, pos.y())
        elif pos.y() == screen_geometry.height() - 10:  # 下边缘
            target_pos = QPoint(pos.x(), screen_geometry.height() - height)

        if target_pos:
            self.animation.setStartValue(self.pos())
            self.animation.setEndValue(target_pos)
            self.animation.start()

    def updateButtons(self):
        for i in reversed(range(self.button_layout.count())): 
            widget = self.button_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.settings["apps"]:
            no_app_label = QLabel("未添加程序", self)
            no_app_label.setAlignment(Qt.AlignCenter)
            no_app_label.setStyleSheet("font-size: 18px; color: gray;")
            self.button_layout.addWidget(no_app_label)
            self.resize(200, 120)
            return

        self.resize(len(self.settings["apps"]) * 100 + 20, 150)  # 调整窗口宽度以适应更大的按钮

        buttons = []
        for i, app in enumerate(self.settings["apps"]):
            button = QPushButton(self)
            button.setFixedSize(80, 80)  # 将按钮尺寸从64x64放大到80x80
            button.setStyleSheet("background-color: transparent;")
            button.setIcon(QIcon())
            if app["icon"]:
                icon = QIcon()
                icon.addFile(app["icon"], mode=QIcon.Normal, state=QIcon.On)
                button.setIcon(icon)
                button.setIconSize(button.size())  # 图标尺寸与按钮尺寸一致

            # 绑定按钮点击事件
            button.clicked.connect(lambda checked, command=app["command"]: self.launchApp(command))

            name_label = QLabel(app["name"], self)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 16px; color: black;")
            name_label.setFixedWidth(80)  # 增加标签宽度以适应更大的按钮
            name_label.setWordWrap(True)

            vbox = QVBoxLayout()
            vbox.setSpacing(5)
            vbox.setAlignment(Qt.AlignCenter)
            vbox.addWidget(button, 0, Qt.AlignCenter)
            vbox.addWidget(name_label, 0, Qt.AlignCenter)
            buttons.append(vbox)

        for button in buttons:
            self.button_layout.addLayout(button)

    def launchApp(self, command):
        if command:
            try:
                os.startfile(command)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开应用程序: {str(e)}")
        else:
            QMessageBox.information(self, "提示", "此按钮尚未关联任何应用程序")

    def showContextMenu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #cccccc;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px 5px 10px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
        """)
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.showSettings)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exitApp)
        menu.addAction(settings_action)
        menu.addAction(exit_action)
        menu.exec_(self.mapToGlobal(pos))

    def showSettings(self):
        self.settings_window = QMainWindow()
        self.settings_window.setWindowTitle("设置")
        self.settings_window.setGeometry(100, 100, 600, 400)
        self.settings_window.setStyleSheet("font-family: Microsoft YaHei;")
        
        self.settings_window.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.settings_window.closeEvent = lambda event: event.ignore()
        
        central_widget = QWidget()
        self.settings_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 开机自启动设置
        self.autostart_checkbox = QCheckBox("开机自启动", self.settings_window)
        self.autostart_checkbox.setChecked(self.settings.get("autostart", False))
        layout.addWidget(self.autostart_checkbox)

        # 城市设置
        city_label = QLabel("当前城市（例：北京）:")
        layout.addWidget(city_label)
        
        # 添加城市搜索框
        self.city_edit = QLineEdit(self.settings.get("city", "北京"))  # 默认城市为北京
        self.city_edit.setPlaceholderText("输入城市名称进行搜索")
        self.city_completer = QCompleter(self.getCityList(), self.settings_window)
        self.city_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.city_edit.setCompleter(self.city_completer)
        layout.addWidget(self.city_edit)

        # 应用程序设置
        self.app_frame = QWidget()
        self.app_layout = QVBoxLayout(self.app_frame)
        layout.addWidget(self.app_frame)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加应用")
        self.add_button.clicked.connect(self.addApp)
        button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("移除应用")
        self.remove_button.clicked.connect(self.removeApp)
        button_layout.addWidget(self.remove_button)

        layout.addLayout(button_layout)

        save_button = QPushButton("保存")
        save_button.clicked.connect(self.saveSettings)
        layout.addWidget(save_button)
        
        self.app_entries = []
        for app in self.settings["apps"]:
            self.addAppEntry(app["name"], app["command"])

        self.settings_window.show()

    def addApp(self):
        self.addAppEntry()

    def addAppEntry(self, name="", command=""):
        if len(self.app_entries) >= 5:
            QMessageBox.information(self.settings_window, "提示", "最多只能添加5个应用程序")
            return

        entry_widget = QWidget()
        entry_layout = QHBoxLayout(entry_widget)

        name_edit = QLineEdit(name)
        command_edit = QLineEdit(command)
        browse_button = QPushButton("浏览应用程序")
        browse_button.clicked.connect(lambda: self.browseFile(command_edit))

        entry_layout.addWidget(name_edit)
        entry_layout.addWidget(command_edit)
        entry_layout.addWidget(browse_button)

        self.app_layout.addWidget(entry_widget)
        self.app_entries.append((name_edit, command_edit))

    def removeApp(self):
        if self.app_entries:
            last_entry = self.app_layout.takeAt(self.app_layout.count() - 1)
            last_entry.widget().deleteLater()
            self.app_entries.pop()

    def browseFile(self, command_edit):
        file_path, _ = QFileDialog.getOpenFileName(self.settings_window, "选择文件", "", "Executable Files (*.exe)")
        if file_path:
            command_edit.setText(file_path)
            # 自动提取图标
            self.extractIcon(file_path)

    def extractIcon(self, exe_path):
        try:
            ico_path = os.path.splitext(exe_path)[0] + ".ico"
            if not os.path.exists(ico_path):
                from PIL import Image
                import win32api
                import win32con
                import win32ui
                import win32gui

                ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
                ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)

                large, small = win32gui.ExtractIconEx(exe_path, 0)
                win32gui.DestroyIcon(small[0])

                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
                hdc = hdc.CreateCompatibleDC()
                hdc.SelectObject(hbmp)
                hdc.DrawIcon((0, 0), large[0])

                bmpinfo = hbmp.GetInfo()
                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )

                img.save(ico_path)
                win32gui.DestroyIcon(large[0])
            return ico_path
        except Exception as e:
            print(f"无法提取图标: {e}")
            return ""

    def getCityList(self):
        try:
            with open("weather/weatherlib.txt", "r", encoding="utf-8") as f:
                content = f.read()
                # 解码Base64内容
                import base64
                decoded_content = base64.b64decode(content).decode("utf-8")
                # 解析城市数据
                import re
                city_data = re.findall(r'{"name":"([^"]+)","city_num":(\d+)}', decoded_content)
                # 将城市名称与cityid对应起来
                self.city_map = {name: int(city_num) for name, city_num in city_data}
                return list(self.city_map.keys())  # 返回城市名称列表
        except Exception as e:
            print(f"无法加载城市列表: {e}")
            return []

    def updateWeather(self):
        try:
            import requests
            city = self.settings.get("city", "北京")
            cityid = self.settings.get("cityid", 101010100)
            url = f"https://weatherapi.market.xiaomi.com/wtr-v3/weather/all?latitude=110&longitude=112&isLocated=true&locationKey=weathercn%3A{cityid}&days=1&appKey=weather20151024&sign=zUFJoAR2ZVrDy1vF3D07&romVersion=7.2.16&appVersion=87&alpha=false&isGlobal=false&device=cancro&modDevice=&locale=zh_cn"
            heads={
                "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
            }
            response = requests.get(url, headers=heads,timeout=5)
            data = response.json()
            if "current" in data:
                weather_code = int(data["current"]["weather"])
                try:
                    with open("weather/weather_status.json", "r", encoding="utf-8") as f:
                        weather_status = json.load(f)
                        weather_desc = next((item["wea"] for item in weather_status["weatherinfo"] if item["code"] == weather_code), "未知")
                except FileNotFoundError:
                    weather_desc = "未知"
                temp = data["current"]["temperature"]["value"]+data["current"]["temperature"]["unit"]
                self.bottom_label.setText(f"📍 {city} | {weather_desc} | {temp}")
                self.bottom_label.setStyleSheet(f"""
                    font-size: 14px;
                    color: #666666;
                    padding-top: 5px;
                    border-top: 1px solid rgba(0, 0, 0, 0.1);
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #e8e8e8);
                    border-radius: 0 0 15px 15px; /* 底部圆角 */
                    padding: 5px 10px;
                """)
            else:
                self.bottom_label.setText("天气获取失败")
        except requests.exceptions.RequestException as e:
            self.bottom_label.setText(f"获取失败：网络错误 ({str(e)})")
        except Exception as e:
            self.bottom_label.setText(f"未知错误 ({str(e)})")

    def saveSettings(self):
        new_apps = []
        for entry in self.app_entries:
            name = entry[0].text()
            command = entry[1].text()
            # 如果名称和路径均为空，则忽略该条目
            if not name and not command:
                continue
            icon = self.extractIcon(command) if command else ""
            new_apps.append({"name": name, "icon": icon, "command": command})

        # 保存开机自启动状态
        autostart_enabled = self.autostart_checkbox.isChecked()
        self.settings["autostart"] = autostart_enabled
        self.updateAutostart(autostart_enabled)

        # 检查城市输入是否有效
        city = self.city_edit.text()
        if city and city not in self.getCityList():
            QMessageBox.warning(self.settings_window, "警告", f"'{city}' 不是有效的城市名称，请重新输入")
            return  # 如果城市无效，直接返回，不保存设置

        # 保存城市设置及其对应的cityid
        self.settings["city"] = city
        self.settings["cityid"] = self.city_map.get(city, 0)  # 如果找不到对应的cityid，默认为0

        self.settings["apps"] = new_apps

        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

        self.updateButtons()
        
        # 释放共享内存，以便重启时不受多开限制
        self.shared_memory.detach()

        # 获取可执行文件路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            exe_path = sys.executable
        else:
            # 如果是开发环境中的脚本
            exe_path = os.path.abspath(sys.argv[0])

        # 在ProgramData目录下创建快捷方式
        self.createStartupShortcut(exe_path)
        sys.exit()

    def createStartupShortcut(self, target_path):
        import winshell
        from win32com.client import Dispatch

        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "QuickLaunchApp.lnk")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.save()

    def updateAutostart(self, enable):
        import winshell
        from win32com.client import Dispatch

        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "QuickLaunchApp.lnk")

        if enable:
            # 获取可执行文件路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                exe_path = sys.executable
            else:
                # 如果是开发环境中的脚本
                exe_path = os.path.abspath(sys.argv[0])

            # 创建快捷方式
            self.createStartupShortcut(exe_path)
        else:
            # 删除快捷方式
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)

    def loadSettings(self):
        self.settings_file = "quickstart.json"
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "opacity": 0.9,
                "apps": [],
                "position": {"x": 0, "y": 878},
                "autostart": False  # 默认不启用开机自启动
            }
        self.updateOpacity(self.settings["opacity"])
        self.updateButtons()

    def exitApp(self):
        os.system(f"taskkill /F /PID {os.getpid()}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.last_activity_time = time.time()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            self.checkEdgeSnap()
            self.savePosition()
            self.last_activity_time = time.time()

    def checkPPTFullscreen(self):
        import win32gui
        window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        if "PowerPoint " in window_title or "WPS Presentation Slide Show" in window_title:
            if self.isVisible():
                self.hide()
        else:
            if not self.isVisible():
                self.show()

    def updateOpacity(self, opacity):
        self.setWindowOpacity(opacity)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuickLaunchApp()
    window.show()    
    sys.exit(app.exec_())