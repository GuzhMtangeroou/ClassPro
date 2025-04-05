import sys
import os
import json
import base64
import uuid
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMenu, QTextEdit, QDialog, QCheckBox)
from PyQt6.QtGui import QPainter, QBrush, QColor, QAction
from PyQt6.QtCore import Qt, QPoint, QTimer

class HtmlWidget(QWidget):
    def __init__(self, config_path, parent=None, manager=None):
        super().__init__(parent)
        self.manager = manager
        self.config_path = config_path
        self.draggable = True
        self.raw_text = ""
        self.custom_style = ""  # 新增：用于存储自定义样式
        self.initUI()
        self.loadSettings()
        self.initAutoSaveTimer()

    def loadSettings(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                self.move(config["position"]["x"], config["position"]["y"])
                self.draggable = config.get("draggable", True)
                self.raw_text = base64.b64decode(config["content"]).decode("utf-8")
                self.custom_style = config.get("style", "")  # 新增：加载自定义样式
                self.updateText(self.raw_text)
                self.applyStyle()  # 新增：应用样式

    def saveSettings(self):
        config = {
            "position": {"x": self.pos().x(), "y": self.pos().y()},
            "draggable": self.draggable,
            "content": base64.b64encode(self.raw_text.encode("utf-8")).decode("utf-8"),
            "style": self.custom_style  # 新增：保存自定义样式
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)

    def applyStyle(self):
        """应用自定义样式"""
        if self.custom_style:
            self.setStyleSheet(self.custom_style)
        else:
            self.setStyleSheet("font-family: Microsoft YaHei;")

    def showSettings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setFixedSize(400, 300)
        layout = QVBoxLayout(dialog)

        draggable_check = QCheckBox("允许拖动", dialog)
        draggable_check.setChecked(self.draggable)
        layout.addWidget(draggable_check)

        text_edit = QTextEdit(self.raw_text, dialog)
        text_edit.setPlainText(self.raw_text)
        text_edit.setPlaceholderText("输入html")
        layout.addWidget(text_edit)

        style_edit = QTextEdit(self.custom_style, dialog)  # 新增：样式输入框
        style_edit.setPlainText(self.custom_style)
        style_edit.setPlaceholderText("输入QSS样式")
        layout.addWidget(style_edit)

        docu = QLabel(dialog,text="""<a href="https://doc.qt.io/qt-6.8/stylesheet-reference.html#list-of-properties">如何编写QSS样式</a>""")
        docu.setOpenExternalLinks(True)
        layout.addWidget(docu)

        save_button = QPushButton("保存", dialog)
        save_button.clicked.connect(lambda: self.saveSettingsAndClose(
            base64.b64encode(text_edit.toPlainText().encode("utf-8")).decode("utf-8"),
            draggable_check.isChecked(), dialog, style_edit.toPlainText()))  # 新增：传递样式
        layout.addWidget(save_button)

        dialog.exec()

    def saveSettingsAndClose(self, content, draggable, dialog, style):
        self.draggable = draggable
        self.custom_style = style  # 新增：保存样式
        self.updateText(base64.b64decode(content).decode("utf-8"))
        self.applyStyle()  # 新增：应用样式
        self.saveSettings()
        dialog.close()

    def initAutoSaveTimer(self):
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.saveSettings)
        self.auto_save_timer.start(3000)

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("font-family: Microsoft YaHei;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        self.text_label = QLabel(self)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.text_label.setStyleSheet("font-size: 14px; color: black;")
        self.text_label.mousePressEvent = self.mousePressEvent
        self.text_label.mouseMoveEvent = self.mouseMoveEvent
        self.layout.addWidget(self.text_label)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self.drag_position = QPoint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

    def updateText(self, text):
        self.raw_text = text
        self.text_label.setText(text)
        self.adjustSize()
        self.resize(min(self.width(), 800), self.height())

    def showContextMenu(self, pos):
        menu = QMenu(self)
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.showSettings)
        menu.addAction(settings_action)

        new_widget_action = QAction("新建html小组件", self)
        new_widget_action.triggered.connect(self.createNewWidget)
        menu.addAction(new_widget_action)

        refresh_action = QAction("刷新所有html小组件", self)
        refresh_action.triggered.connect(self.refreshWidget)
        menu.addAction(refresh_action)

        delete_action = QAction("删除html小组件", self)
        delete_action.triggered.connect(self.deleteWidget)
        menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(pos))

    def refreshWidget(self):
        """刷新小组件，重新加载配置并更新显示内容"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                self.move(config["position"]["x"], config["position"]["y"])
                self.draggable = config.get("draggable", True)
                self.raw_text = base64.b64decode(config["content"]).decode("utf-8")
                self.updateText(self.raw_text)
        else:
            self.close()  # 如果配置文件不存在，关闭小组件

    def createNewWidget(self):
        config_path = os.path.join("data/note/html", f"{uuid.uuid4()}.json")
        default_config = {
            "position": {"x": 100, "y": 100},
            "draggable": True,
            "content": base64.b64encode("<h1>Hello World!</h1>".encode("utf-8")).decode("utf-8")
        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)

        new_widget = HtmlWidget(config_path, manager=self.manager)
        self.manager.widgets.append(new_widget)
        new_widget.show()

    def deleteWidget(self):
        """删除小组件及其配置文件"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.auto_save_timer.stop()
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.draggable:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.draggable:
            self.move(event.globalPosition().toPoint() - self.drag_position)
        super().mouseMoveEvent(event)

class HtmlWidgetManager:
    def __init__(self):
        self.widgets = []
        self.first_run = not os.path.exists("data/note/html")
        self.initUI()

    def initUI(self):
        if not os.path.exists("data/note/html"):
            os.makedirs("data/note/html")

        if self.first_run:
            config_path = os.path.join("data/note/html", f"{uuid.uuid4()}.json")
            example_config = {
                "position": {"x": 100, "y": 100},
                "draggable": True,
                "content": base64.b64encode("<h1>这是一个示例html小组件</h1>".encode("utf-8")).decode("utf-8")
            }
            with open(config_path, "w") as f:
                json.dump(example_config, f, indent=4)
            self.first_run = False

        self.widgets = []
        for filename in os.listdir("data/note/html"):
            if filename.endswith(".json"):
                config_path = os.path.join("data/note/html", filename)
                widget = HtmlWidget(config_path, manager=self)
                widget.show()
                self.widgets.append(widget)

def run_html_widget_manager():
    app = QApplication(sys.argv)
    manager = HtmlWidgetManager()
    sys.exit(app.exec())

#run_html_widget_manager()