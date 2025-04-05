import sys
import os
import time
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QMenu, 
                             QMessageBox, QLineEdit, QCompleter)
from PySide6.QtGui import QIcon, QPainter, QBrush, QColor, QAction
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PIL import Image

class QuickStart(QMainWindow):
    def __init__(self, config_path="data/qs.json"):
        super().__init__()
        self.config_path = config_path
        self.initUI()
        self.loadSettings()
        self.restorePosition()
        self.initTimers()

        self.last_activity_time = time.time()

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.updateWeather)
        self.weather_timer.start(600000)
        self.updateWeather()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("font-family: Microsoft YaHei;")

    def initUI(self):
        self.setWindowTitle("ClassPro_qs")
        self.setGeometry(100, 100, 300, 90)  # 缩小窗口尺寸
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: rgba(255, 255, 255, 200); color: black; border-radius: 10px; font-family: Microsoft YaHei;")
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(12, 12, 12, 6)  # 缩小边距
        self.layout.setSpacing(12)  # 增加元素之间的垂直间距

        self.title_label = QLabel("快速启动", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333333; margin-bottom: 10px;")  # 缩小字体，增加下边距
        self.layout.addWidget(self.title_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(12)  # 缩小按钮间距
        self.layout.addLayout(self.button_layout)

        self.bottom_label = QLabel("天气获取中", self)
        self.bottom_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.bottom_label.setStyleSheet("font-size: 12px; color: blue; margin-top: 10px;")  # 缩小字体，增加上边距
        self.layout.addWidget(self.bottom_label)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self.drag_position = QPoint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

    def initTimers(self):
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.savePosition)
        self.position_timer.start(5000)

        self.ppt_check_timer = QTimer(self)
        self.ppt_check_timer.timeout.connect(self.checkFullscreenPrograms)
        self.ppt_check_timer.start(1000)

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.checkInactivity)
        self.inactivity_timer.start(200)

        self.cursor_check_timer = QTimer(self)
        self.cursor_check_timer.timeout.connect(self.checkCursorOverWindow)
        self.cursor_check_timer.start(200)

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
        screen = self.screen()
        screen_geometry = screen.availableGeometry()
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
        screen = self.screen()
        screen_geometry = screen.availableGeometry()
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
        screen = self.screen()
        screen_geometry = screen.availableGeometry()
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
            no_app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_app_label.setStyleSheet("font-size: 14px; color: gray;")  # 缩小字体
            self.button_layout.addWidget(no_app_label)
            self.resize(150, 90)  # 缩小窗口尺寸
            return

        self.resize(len(self.settings["apps"]) * 70 + 20, 100)  # 调整窗口宽度以适应更大的按钮

        buttons = []
        for i, app in enumerate(self.settings["apps"]):
            button = QPushButton(self)
            button.setFixedSize(45, 45)  # 缩小按钮尺寸
            button.setStyleSheet("background-color: transparent;")
            button.setIcon(QIcon())
            if app["icon"]:
                icon = QIcon()
                icon.addFile(app["icon"], mode=QIcon.Mode.Normal, state=QIcon.State.On)
                button.setIcon(icon)
                button.setIconSize(button.size())  # 图标尺寸与按钮尺寸一致

            # 绑定按钮点击事件
            button.clicked.connect(lambda checked, command=app["command"]: self.launchApp(command))

            name_label = QLabel(app["name"], self)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("font-size: 14px; color: black;")  # 缩小字体
            name_label.setWordWrap(True)

            vbox = QVBoxLayout()
            vbox.setSpacing(5)
            vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(button, 0, Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(name_label, 0, Qt.AlignmentFlag.AlignCenter)
            buttons.append(vbox)

        for button in buttons:
            self.button_layout.addLayout(button)

    def launchApp(self, command):
        if command:
            try:
                os.startfile(command)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开应用: {str(e)}")
        else:
            QMessageBox.information(self, "提示", "未关联任何应用")

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
        menu.addAction(settings_action)
        menu.exec(self.mapToGlobal(pos))

    def showSettings(self):
        self.settings_window = QMainWindow()
        self.settings_window.setWindowTitle("设置")
        self.settings_window.setGeometry(100, 100, 600, 400)
        self.settings_window.setStyleSheet("font-family: Microsoft YaHei;")
        
        self.settings_window.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint)
        self.settings_window.closeEvent = lambda event: event.ignore()
        
        central_widget = QWidget()
        self.settings_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 城市设置
        city_label = QLabel("当前城市（例：北京）:")
        layout.addWidget(city_label)
        
        # 添加城市搜索框
        self.city_edit = QLineEdit(self.settings.get("city", "北京"))  # 默认城市为北京
        self.city_edit.setPlaceholderText("输入城市名称进行搜索")
        self.city_completer = QCompleter(self.getCityList(), self.settings_window)
        self.city_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
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

        save_button = QPushButton("应用更改")
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

    def checkFullscreenPrograms(self):
        import win32gui
        import win32con
        import win32api

        # 定义要检测的关键字列表
        ppt_keywords = ["PowerPoint ", "WPS Presentation Slide Show", "希沃白板","Microsoft Edge"]

        try:
            # 获取当前活动窗口的句柄
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)

            # 获取屏幕的尺寸
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

            # 获取窗口的尺寸
            window_rect = win32gui.GetWindowRect(hwnd)
            window_width = window_rect[2] - window_rect[0]
            window_height = window_rect[3] - window_rect[1]

            # 判断窗口是否全屏
            is_fullscreen = (window_width == screen_width and window_height == screen_height)

            # 如果窗口标题包含PPT相关关键字且处于全屏状态，则隐藏主窗口
            if any(keyword in window_title for keyword in ppt_keywords) and is_fullscreen:
                if self.isVisible():
                    self.hide()
            else:
                if not self.isVisible():
                    self.show()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检查PPT全屏时出错: {e}")  # 使用弹窗提示错误信息

    def updateWeather(self):
        try:
            import requests
            city = self.settings.get("city", "北京")
            cityid = self.settings.get("cityid", 101010100)
            url = f"https://weatherapi.market.xiaomi.com/wtr-v3/weather/all?latitude=110&longitude=112&isLocated=true&locationKey=weathercn%3A{cityid}&days=1&appKey=weather20151024&sign=zUFJoAR2ZVrDy1vF3D07&romVersion=7.2.16&appVersion=87&alpha=false&isGlobal=false&device=cancro&modDevice=&locale=zh_cn"
            heads={
                "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
            }
            response = requests.get(url, headers=heads, timeout=5)
            response.raise_for_status()  # 确保请求成功
            data = response.json()
            if "current" in data:
                weather_code = int(data["current"]["weather"])
                try:
                    with open("data/weather/weather_status.data", "r", encoding="utf-8") as f:
                        weather_status = json.load(f)
                        weather_desc = next((item["wea"] for item in weather_status["weatherinfo"] if item["code"] == weather_code), "未知")
                except FileNotFoundError:
                    weather_desc = "未知"
                temp = data["current"]["temperature"]["value"]+data["current"]["temperature"]["unit"]
                self.bottom_label.setText(f"📍 {city} | {weather_desc} | {temp}")
                self.bottom_label.setStyleSheet("font-size: 14px; color: blue;")
            else:
                self.bottom_label.setText("天气获取失败")
        except requests.exceptions.RequestException as e:
            self.bottom_label.setText(f"获取失败：网络错误 ({str(e)})")
        except Exception as e:
            self.bottom_label.setText(f"未知错误 ({str(e)})")

    def getCityList(self):
        try:
            with open("data/weather/weatherlib.data", "r", encoding="utf-8") as f:
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
            QMessageBox.critical(self, "错误", f"无法加载城市列表: {e}")  # 使用弹窗提示错误信息
            return []

    def extractIcon(self, exe_path):
        try:
            ico_path = os.path.splitext(exe_path)[0] + ".ico"
            if not os.path.exists(ico_path):
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
            return ""

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

        QMessageBox.information(self.settings_window, "提示", "设置已保存")
        self.settings_window.destroy()

    def loadSettings(self):
        self.settings_file = "data/qs.json"
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "opacity": 0.9,
                "apps": [],
                "position": {"x": 0, "y": 878},
            }
        self.updateOpacity(self.settings["opacity"])
        self.updateButtons()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.last_activity_time = time.time()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.checkEdgeSnap()
            self.savePosition()
            self.last_activity_time = time.time()

    def updateOpacity(self, opacity):
        self.setWindowOpacity(opacity)

class QuickStartApp:
    def __init__(self, config_path="data/qs.json"):
        self.config_path = config_path

    def run(self):
        app = QApplication(sys.argv)
        window = QuickStart(config_path=self.config_path)
        window.show()
        sys.exit(app.exec())

def run_quickstart(config_path="data/qs.json"):
    """
    启动快速启动应用的便捷方法
    
    :param config_path: 配置文件路径
    """
    app = QuickStartApp(config_path=config_path)
    app.run()

#run_quickstart()