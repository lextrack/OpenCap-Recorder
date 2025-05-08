from PyQt6.QtGui import QPalette, QColor

class ThemeManager:
    def __init__(self, app):
        self.app = app
        
    def set_theme(self, theme):
        if theme == "dark":
            self.set_dark_theme()
        elif theme == "light":
            self.set_light_theme()
        elif theme == "dark blue":
            self.set_dark_blue_theme()
        elif theme == "light green":
            self.set_light_green_theme()
        elif theme == "purple":
            self.set_purple_theme()
        elif theme == "starry night":
            self.set_starry_night_theme()
        elif theme == "sunset":
            self.set_sunset_theme()
    
    def set_dark_theme(self):
        stylesheet = """
        QWidget {
            background-color: #2e2e2e;
            color: white;
        }
        QGroupBox {
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 1em;
            color: white;
            background-color: #2e2e2e;
            margin-bottom: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 5px;
            bottom: 2px;
            padding: 0;
        }
        QComboBox {
            background-color: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin-right: 5px;
        }
        QPushButton {
            background-color: #1e1e1e;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 8px 15px;
            color: white;
        }
        QPushButton:hover {
            background-color: #3a3a3a;
        }
        QPushButton:pressed {
            background-color: #0a0a0a;
        }
        QLineEdit {
            background-color: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #1e1e1e;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #555;
            border: 1px solid #888;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #888;
        }
        QLabel {
            color: white;
        }
        """
        self.app.setStyleSheet(stylesheet)
    
    def set_light_theme(self):
        stylesheet = """
        QWidget {
            background-color: #f0f0f0;
            color: black;
        }
        QGroupBox {
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 1em;
            color: black;
            background-color: #f0f0f0;
            margin-bottom: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 5px;
            padding: 0;
        }
        QComboBox {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 5px;
            color: black;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid black;
            margin-right: 5px;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 8px 15px;
            color: black;
        }
        QPushButton:hover {
            background-color: #c0c0c0;
        }
        QPushButton:pressed {
            background-color: #a0a0a0;
        }
        QLineEdit {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 5px;
            color: black;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #aaa;
            border: 1px solid #777;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #888;
        }
        QLabel {
            color: black;
        }
        """
        self.app.setStyleSheet(stylesheet)
    
    def set_dark_blue_theme(self):
        stylesheet = """
        QWidget {
            background-color: #2c3e50;
            color: white;
        }
        QGroupBox {
            border: 1px solid #3498db;
            border-radius: 5px;
            margin-top: 1em;
            color: white;
            background-color: #2c3e50;
            margin-bottom: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 5px;
            padding: 0;
        }
        QComboBox {
            background-color: #34495e;
            border: 1px solid #3498db;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin-right: 5px;
        }
        QPushButton {
            background-color: #3498db;
            border: 1px solid #2980b9;
            border-radius: 5px;
            padding: 8px 15px;
            color: white;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #21618c;
        }
        QLineEdit {
            background-color: #34495e;
            border: 1px solid #3498db;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #34495e;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #3498db;
            border: 1px solid #2980b9;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #5dade2;
        }
        QLabel {
            color: white;
        }
        """
        self.app.setStyleSheet(stylesheet)
    
    def set_light_green_theme(self):
        stylesheet = """
        QWidget {
            background-color: #2e4d2e;
            color: white;
        }
        QGroupBox {
            border: 1px solid #3a5f3a;
            border-radius: 5px;
            margin-top: 1em;
            color: white;
            background-color: #2e4d2e;
            margin-bottom: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 5px;
            padding: 0;
        }
        QComboBox {
            background-color: #1f3d1f;
            border: 1px solid #3a5f3a;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin-right: 5px;
        }
        QPushButton {
            background-color: #3a5f3a;
            border: 1px solid #2e4d2e;
            border-radius: 5px;
            padding: 8px 15px;
            color: white;
        }
        QPushButton:hover {
            background-color: #4a7f4a;
        }
        QPushButton:pressed {
            background-color: #1f3d1f;
        }
        QLineEdit {
            background-color: #1f3d1f;
            border: 1px solid #3a5f3a;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #1f3d1f;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #3a5f3a;
            border: 1px solid #2e4d2e;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #4a7f4a;
        }
        QLabel {
            color: white;
        }
        """
        self.app.setStyleSheet(stylesheet)
    
    def set_purple_theme(self):
        stylesheet = """
        QWidget {
            background-color: #6a0f6a;
            color: white;
        }
        QGroupBox {
            border: 1px solid #8c2b8c;
            border-radius: 5px;
            margin-top: 1em;
            color: white;
            background-color: #6a0f6a;
            margin-bottom: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 5px;
            padding: 0;
        }
        QComboBox {
            background-color: #8c2b8c;
            border: 1px solid #9b4d9b;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin-right: 5px;
        }
        QPushButton {
            background-color: #8c2b8c;
            border: 1px solid #9b4d9b;
            border-radius: 5px;
            padding: 8px 15px;
            color: white;
        }
        QPushButton:hover {
            background-color: #9b4d9b;
        }
        QPushButton:pressed {
            background-color: #7a1f7a;
        }
        QLineEdit {
            background-color: #8c2b8c;
            border: 1px solid #9b4d9b;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #8c2b8c;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #9b4d9b;
            border: 1px solid #ab5dab;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #bb6dbb;
        }
        QLabel {
            color: white;
        }
        """
        self.app.setStyleSheet(stylesheet)
    
    def set_starry_night_theme(self):
        stylesheet = """
        QWidget {
            background-color: #2e3a5f;
            color: white;
        }
        QGroupBox {
            border: 1px solid #3b4e6c;
            border-radius: 5px;
            margin-top: 1em;
            color: white;
            background-color: #2e3a5f;
            margin-bottom: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 5px;
            padding: 0;
        }
        QComboBox {
            background-color: #1b263b;
            border: 1px solid #3b4e6c;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin-right: 5px;
        }
        QPushButton {
            background-color: #3b4e6c;
            border: 1px solid #4b5e7c;
            border-radius: 5px;
            padding: 8px 15px;
            color: white;
        }
        QPushButton:hover {
            background-color: #a9ad68;
        }
        QPushButton:pressed {
            background-color: #1b263b;
        }
        QLineEdit {
            background-color: #1b263b;
            border: 1px solid #3b4e6c;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #1b263b;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #3b4e6c;
            border: 1px solid #4b5e7c;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #a9ad68;
        }
        QLabel {
            color: white;
        }
        """
        self.app.setStyleSheet(stylesheet)
    
    def set_sunset_theme(self):
        stylesheet = """
        QWidget {
            background-color: #2d2d3d;
            color: white;
        }
        QGroupBox {
            border: 1px solid #c65c4e;
            border-radius: 5px;
            margin-top: 1em;
            color: white;
            background-color: #2d2d3d;
            margin-bottom: 1em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 5px;
            padding: 0;
        }
        QComboBox {
            background-color: #3d3d5c;
            border: 1px solid #c65c4e;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin-right: 5px;
        }
        QPushButton {
            background-color: #c65c4e;
            border: 1px solid #d47b38;
            border-radius: 5px;
            padding: 8px 15px;
            color: white;
        }
        QPushButton:hover {
            background-color: #d47b38;
        }
        QPushButton:pressed {
            background-color: #b64c3e;
        }
        QLineEdit {
            background-color: #3d3d5c;
            border: 1px solid #c65c4e;
            border-radius: 3px;
            padding: 5px;
            color: white;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #3d3d5c;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #c65c4e;
            border: 1px solid #d47b38;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #d47b38;
        }
        QLabel {
            color: white;
        }
        """
        self.app.setStyleSheet(stylesheet)