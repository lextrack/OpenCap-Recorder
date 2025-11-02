import abc
import logging
import os
import datetime
import subprocess
import sys
import threading
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSlider, QFileDialog,
                             QMessageBox, QGroupBox, QGridLayout, QFrame,
                             QLineEdit, QMainWindow, QStyle, QDialog, QTextEdit, QSizePolicy,
                             QCheckBox, QDialogButtonBox, QGridLayout, QListWidget, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QColor, QFont, QImage
import mss
import numpy as np
import cv2
from PIL import Image
from screeninfo import get_monitors

from common.area_selector import AreaSelector
from common.audio_device_monitor import AudioDeviceMonitor
from common.themes import ThemeManager
from common.translation_manager import TranslationManager
from common.logging_config import setup_logging
from configparser import ConfigParser

class ABCQtMeta(type(QMainWindow), type(abc.ABC)):
    pass

class StatusSignals(QObject):
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

class AudioDeviceSelector(QDialog):
    def __init__(self, parent, audio_devices, title="Select Audio Devices"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 300)
        
        self.selected_devices = []
        
        layout = QVBoxLayout(self)
        
        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        for device in audio_devices:
            self.device_list.addItem(device)
        
        self.volume_container = QWidget()
        self.volume_layout = QGridLayout(self.volume_container)
        self.volume_controls = {}
        
        for i, device in enumerate(audio_devices):
            label = QLabel(device)
            self.volume_layout.addWidget(label, i, 0)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(100)
            slider.setMinimumWidth(150)
            self.volume_layout.addWidget(slider, i, 1)
            
            value_label = QLabel("100%")
            value_label.setFixedWidth(40)
            self.volume_layout.addWidget(value_label, i, 2)
            
            self.volume_controls[device] = {
                'slider': slider,
                'label': value_label
            }
            
            slider.valueChanged.connect(lambda v, label=value_label: label.setText(f"{v}%"))
            
        instructions = QLabel(parent.t("select_devices_recording"))
        instructions.setWordWrap(True)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(instructions)
        layout.addWidget(self.device_list)
        layout.addWidget(self.volume_container)
        layout.addWidget(buttons)
        
        self.device_list.itemSelectionChanged.connect(self.update_volume_visibility)
        
    def update_volume_visibility(self):
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            device_name = item.text()
            
            for row in range(self.volume_layout.rowCount()):
                label = self.volume_layout.itemAtPosition(row, 0)
                slider = self.volume_layout.itemAtPosition(row, 1)
                value = self.volume_layout.itemAtPosition(row, 2)
                
                if label and label.widget().text() == device_name:
                    visible = item.isSelected()
                    label.widget().setVisible(visible)
                    slider.widget().setVisible(visible)
                    value.widget().setVisible(visible)
                    break
    
    def get_selected_devices(self):
        selected_devices = []
        
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            if item.isSelected():
                device_name = item.text()
                if device_name in self.volume_controls:
                    volume = self.volume_controls[device_name]['slider'].value()
                    selected_devices.append((device_name, volume))
        
        return selected_devices

class ScreenRecorderBase(QMainWindow, abc.ABC, metaclass=ABCQtMeta):
    def __init__(self):
            super().__init__()
            self.logger = self._initialize_logger()
            
            self.logger.info("APPLICATION STARTED")
            self.setWindowTitle("Opencap Recorder")
            self.resize(1100, 650)
            
            self.setMinimumSize(950, 650)

            self.config = ConfigParser()
            self.config_file = 'config.ini'
            self.load_config()

            self.translation_manager = TranslationManager(self.config.get('Settings', 'language', fallback='en-US'))
            self.theme_manager = ThemeManager(self)
            self.set_theme(self.config.get('Settings', 'theme', fallback='dark'))

            self.set_icon()
            
            self.monitors = self.get_monitors()
            if len(self.monitors) == 0:
                QMessageBox.critical(self, "Error", "No monitors found.")
                return

            self.audio_devices = self.get_audio_devices()
            if len(self.audio_devices) == 0:
                QMessageBox.critical(self, "Error", "No audio devices.")
                return

            self.selected_audio_devices = [] 

            self.init_ui()

            self.platform_initialize()

            self.audio_device_monitor = AudioDeviceMonitor(self)
            self.audio_device_monitor.devices_changed.connect(self.on_audio_devices_changed)
            self.audio_device_monitor.device_disconnected.connect(self.on_audio_device_disconnected)
            self.audio_device_monitor.start_monitoring()

            self.create_output_folder()
            self.recording_process = None
            self.running = False
            self.elapsed_time = 0
            self.record_area = None
            self.area_selector = AreaSelector(self)
            self.preview_running = False
            self.preview_timer = QTimer()
            self.preview_timer.timeout.connect(self.update_preview)

            self.current_video_part = 0
            self.video_parts = []
            
            self.status_signals = StatusSignals()
            self.status_signals.status_changed.connect(self.update_status_label)
            self.status_signals.error_occurred.connect(self.show_error_message)

            self.load_audio_device_selection()
            self.update_audio_button_text()

    def _initialize_logger(self):
        if not hasattr(self.__class__, '_logger_initialized'):
            self.logger = setup_logging()
            self.__class__._logger_initialized = True
            return self.logger
        return logging.getLogger()
    
    def on_audio_devices_changed(self, new_devices):
        self.logger.info(f"Updated audio devices: {new_devices}")
        self.audio_devices = new_devices

        available_devices = []
        unavailable_devices = []
        
        for device, volume in self.selected_audio_devices:
            if device in new_devices:
                available_devices.append((device, volume))
            else:
                unavailable_devices.append(device)
        
        if len(unavailable_devices) > 0:
            self.selected_audio_devices = available_devices
            self.update_audio_button_text()
            self.save_config()
            
            if not self.running:
                disconnected_devices = ", ".join(unavailable_devices)
                QMessageBox.warning(
                    self, 
                    self.t("warning"), 
                    self.t("warning_devices_disconnected").format(devices=disconnected_devices)
                )

    def on_audio_device_disconnected(self, device_name):
        self.logger.warning(f"Dispositivo de audio desconectado: {device_name}")
        
        if self.running and device_name in [d[0] for d in self.selected_audio_devices]:
            self.logger.error("An audio device in use has been disconnected. Stopping recording.")
            QMessageBox.critical(
                self, 
                self.t("error"), 
                self.t("error_device_disconnected").format(device=device_name)
            )
            self.stop_recording()

    def platform_initialize(self):
        pass
    
    def t(self, key):
        return self.translation_manager.t(key)
        
    @abc.abstractmethod
    def set_icon(self):
        pass
        
    def change_theme(self, theme):
        theme = theme.lower()
        self.set_theme(theme)
        self.save_config()
        
    def set_theme(self, theme):
        self.theme_manager.set_theme(theme)
        self.current_theme = theme
        
    def save_config(self):
        audio_selections = []
        for device, volume in self.selected_audio_devices:
            audio_selections.append(f"{device}|{volume}")
        
        self.config['Settings'] = {
            'language': self.translation_manager.language,
            'theme': self.theme_combo.currentText().lower(),
            'monitor': self.monitor_combo.currentIndex(),
            'fps': self.fps_combo.currentIndex(),
            'bitrate': self.bitrate_combo.currentIndex(),
            'codec': self.codec_combo.currentIndex(),
            'format': self.format_combo.currentIndex(),
            'audio_devices': ';;'.join(audio_selections),
            'output_folder': self.output_folder
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        
    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config['Settings'] = {
                'language': 'en-US',
                'theme': 'dark',
                'monitor': '0',
                'fps': '1',
                'bitrate': '0',
                'codec': '0',
                'format': '0',
                'audio_devices': '',
                'output_folder': os.path.join(os.getcwd(), "OutputFiles")
            }
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        
        self.output_folder = self.config.get('Settings', 'output_folder', 
                                        fallback=os.path.join(os.getcwd(), "OutputFiles"))
    
    def load_audio_device_selection(self):
        audio_selections = self.config.get('Settings', 'audio_devices', fallback='')
        if audio_selections:
            self.selected_audio_devices = []
            for selection in audio_selections.split(';;'):
                if '|' in selection:
                    device, volume = selection.split('|')
                    try:
                        volume = int(volume)
                        if device in self.audio_devices:
                            self.selected_audio_devices.append((device, volume))
                    except ValueError:
                        pass
                        
    def change_language(self):
        selected_language = self.language_combo.currentText()
        language_map = {
            'English': 'en-US',
            'Español': 'es-CL',
            '简体中文': 'zh-Hans',
            "繁體中文": 'zh-Hant',
            'Italiano': 'it-IT',
            'Français': 'fr-FR',
            'हिन्दी': 'hi-IN',
            'Deutsch': 'de-DE',
            'Português': 'pt-BR',
            'Pусский': 'ru-RU',
            "日本語": 'ja-JP',
            "한국어": 'ko-KR',
            "Polski": 'pl-PL',
            "العربية": 'ar',
            "Tiếng Việt": 'vi-VN',
            "українська мова": 'uk-UA',
            "ไทยกลาง": 'th-TH',
            "Filipino": 'fil-PH',
            "Türkçe": 'tr-TR'
        }
        new_language = language_map.get(selected_language, 'en-US')
        
        if new_language != self.translation_manager.language:
            self.translation_manager.change_language(new_language)
            self.save_config()
            self.update_ui_texts()
            QMessageBox.information(self, self.t("language_change"), self.t("language_changed_success"))

    def update_ui_texts(self):
        self.top_group.setTitle(self.t("app_settings"))
        self.monitor_group.setTitle(self.t("monitor"))
        self.video_settings_group.setTitle(self.t("video_settings"))
        self.audio_settings_group.setTitle(self.t("audio_settings"))
        self.preview_group.setTitle(self.t("preview"))
        self.controls_group.setTitle(self.t("controls"))
        
        self.language_label.setText(self.t("Language") + ":")
        self.theme_label.setText(self.t("theme") + ":")
        self.fps_label.setText(self.t("framerate") + ":")
        self.bitrate_label.setText(self.t("bitrate") + ":")
        self.codec_label.setText(self.t("video_codec") + ":")
        self.format_label.setText(self.t("output_format") + ":")
        self.audio_label.setText(self.t("audio_device") + ":")
        self.output_settings_group.setTitle(self.t("output_settings"))
        self.output_folder_label.setText(self.t("output_folder") + ":")
        
        self.toggle_btn.setText(self.t("start_recording") if not self.running else self.t("stop_recording"))
        self.preview_btn.setText(self.t("start_preview") if not self.preview_running else self.t("stop_preview"))
        self.select_area_btn.setText(self.t("select_recording_area"))
        self.reset_area_btn.setText(self.t("reset_recording_area"))
        self.open_folder_btn.setText(self.t("open_output_folder"))
        self.info_btn.setText(self.t("about"))
        
        self.select_audio_btn.setText(self.t("select_audio_devices"))
        
        self.status_label.setText(self.t("status_recording") if self.running else self.t("status_ready"))

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.top_group = QGroupBox(self.t("app_settings"))
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 5, 10, 5)
        top_layout.setSpacing(10)

        language_container = QHBoxLayout()
        language_container.setContentsMargins(0, 0, 0, 0)
        language_container.setSpacing(5)

        self.language_label = QLabel(self.t("Language") + ":")
        self.language_label.setFixedWidth(65)
        self.language_combo = QComboBox()
        self.language_combo.setFixedWidth(140)
        self.language_combo.addItems(["English", "Español", "简体中文", "繁體中文", "Italiano", "Français", 
                                    "हिन्दी", "Deutsch", "Português", "Pусский", 
                                    "日本語", "한국어", "Polski", "العربية", "Tiếng Việt", 
                                    "українська мова", "ไทยกลาง", "Filipino", "Türkçe"])
        current_language_index = ["en-US", "es-CL", "zh-Hans", "zh-Hant", "it-IT", "fr-FR", "hi-IN", "de-DE", "pt-BR", "ru-RU", 
                                "ja-JP", "ko-KR", "pl-PL", "ar", "vi-VN", "uk-UA", "th-TH", "fil-PH", "tr-TR"].index(self.translation_manager.language)
        self.language_combo.setCurrentIndex(current_language_index)
        self.language_combo.currentTextChanged.connect(self.change_language)

        language_container.addWidget(self.language_label)
        language_container.addWidget(self.language_combo)

        spacer = QWidget()
        spacer.setFixedWidth(30)

        theme_container = QHBoxLayout()
        theme_container.setContentsMargins(0, 0, 0, 0)
        theme_container.setSpacing(5)

        self.theme_label = QLabel(self.t("theme") + ":")
        self.theme_label.setFixedWidth(50)
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(140)
        self.theme_combo.addItems(["Dark", "Light", "Dark Blue", "Light Green", "Purple", "Starry Night", "Sunset"])
        current_theme = self.config.get('Settings', 'theme', fallback='dark')
        theme_index = {"dark": 0, "light": 1, "dark blue": 2, "light green": 3, "purple": 4, "starry night": 5, "sunset": 6}.get(current_theme, 0)
        self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.currentTextChanged.connect(self.change_theme)

        theme_container.addWidget(self.theme_label)
        theme_container.addWidget(self.theme_combo)

        container_widget = QWidget()
        container_layout = QHBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addLayout(language_container)
        container_layout.addWidget(spacer)
        container_layout.addLayout(theme_container)
        container_layout.addStretch()

        top_layout.addWidget(container_widget)

        self.top_group.setLayout(top_layout)
        main_layout.addWidget(self.top_group)

        content_layout = QHBoxLayout()
        
        left_panel = QWidget()
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        self.monitor_group = QGroupBox(self.t("monitor"))
        monitor_layout = QVBoxLayout()
        self.monitor_combo = QComboBox()
        monitor_descriptions = [f"Monitor {i+1}: ({monitor.width}x{monitor.height})" for i, monitor in enumerate(self.monitors)]
        self.monitor_combo.addItems(monitor_descriptions)
        self.monitor_combo.setCurrentIndex(0)
        self.monitor_combo.currentIndexChanged.connect(self.on_monitor_change)
        monitor_layout.addWidget(self.monitor_combo)
        self.monitor_group.setLayout(monitor_layout)
        left_layout.addWidget(self.monitor_group)

        self.video_settings_group = QGroupBox(self.t("video_settings"))
        video_layout = QGridLayout()

        self.fps_label = QLabel(self.t("framerate") + ":")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30", "60"])
        self.fps_combo.setCurrentIndex(int(self.config.get('Settings', 'fps', fallback='1')))
        self.fps_combo.currentIndexChanged.connect(self.save_config)
        
        self.bitrate_label = QLabel(self.t("bitrate") + ":")
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["1000k", "2000k", "4000k", "6000k", "8000k", "10000k", "15000k", "20000k"])
        self.bitrate_combo.setCurrentIndex(int(self.config.get('Settings', 'bitrate', fallback='0')))
        self.bitrate_combo.currentIndexChanged.connect(self.save_config)

        self.codec_label = QLabel(self.t("video_codec") + ":")
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["libx264", "libx265"])
        self.codec_combo.setCurrentIndex(int(self.config.get('Settings', 'codec', fallback='0')))
        self.codec_combo.currentIndexChanged.connect(self.save_config)

        self.format_label = QLabel(self.t("output_format") + ":")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mkv", "mp4"])
        self.format_combo.setCurrentIndex(int(self.config.get('Settings', 'format', fallback='0')))
        self.format_combo.currentIndexChanged.connect(self.save_config)

        video_layout.addWidget(self.fps_label, 0, 0)
        video_layout.addWidget(self.fps_combo, 0, 1)
        video_layout.addWidget(self.bitrate_label, 1, 0)
        video_layout.addWidget(self.bitrate_combo, 1, 1)
        video_layout.addWidget(self.codec_label, 2, 0)
        video_layout.addWidget(self.codec_combo, 2, 1)
        video_layout.addWidget(self.format_label, 3, 0)
        video_layout.addWidget(self.format_combo, 3, 1)
        
        self.video_settings_group.setLayout(video_layout)
        left_layout.addWidget(self.video_settings_group)

        self.audio_settings_group = QGroupBox(self.t("audio_settings"))
        audio_layout = QVBoxLayout()
        
        self.audio_label = QLabel(self.t("audio_device") + ":")
        self.select_audio_btn = QPushButton(self.t("select_audio_devices"))
        self.select_audio_btn.clicked.connect(self.show_audio_device_selector)
        self.update_audio_button_text()
        
        audio_layout.addWidget(self.audio_label)
        audio_layout.addWidget(self.select_audio_btn)
        
        self.audio_settings_group.setLayout(audio_layout)
        left_layout.addWidget(self.audio_settings_group)

        self.output_settings_group = QGroupBox(self.t("output_settings"))
        output_layout = QHBoxLayout()
        
        self.output_folder_label = QLabel(self.t("output_folder") + ":")
        self.output_folder_entry = QLineEdit()
        self.output_folder_entry.setText(self.output_folder)
        self.browse_folder_btn = QPushButton("...")
        self.browse_folder_btn.setFixedWidth(30)
        self.browse_folder_btn.clicked.connect(self.browse_output_folder)
        
        output_layout.addWidget(self.output_folder_label)
        output_layout.addWidget(self.output_folder_entry)
        output_layout.addWidget(self.browse_folder_btn)
        
        self.output_settings_group.setLayout(output_layout)
        left_layout.addWidget(self.output_settings_group)
        
        left_layout.addStretch()
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(5)
        
        self.preview_group = QGroupBox(self.t("preview"))
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: black;")
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        preview_layout.addWidget(self.preview_label)
        self.preview_group.setLayout(preview_layout)
        
        right_layout.addWidget(self.preview_group, 3)
        
        self.controls_group = QGroupBox(self.t("controls"))
        controls_layout = QGridLayout()
        controls_layout.setSpacing(5)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        
        self.toggle_btn = QPushButton(self.t("start_recording"))
        self.toggle_btn.clicked.connect(self.toggle_recording)
        self.toggle_btn.setFixedHeight(35)
        
        self.preview_btn = QPushButton(self.t("start_preview"))
        self.preview_btn.clicked.connect(self.toggle_preview_monitor)
        self.preview_btn.setFixedHeight(35)
        
        self.select_area_btn = QPushButton(self.t("select_recording_area"))
        self.select_area_btn.clicked.connect(self.select_area)
        self.select_area_btn.setFixedHeight(35)
        
        self.reset_area_btn = QPushButton(self.t("reset_recording_area"))
        self.reset_area_btn.clicked.connect(self.reset_recording_area)
        self.reset_area_btn.setFixedHeight(35)
        
        controls_layout.addWidget(self.toggle_btn, 0, 0)
        controls_layout.addWidget(self.preview_btn, 0, 1)
        controls_layout.addWidget(self.select_area_btn, 0, 2)
        controls_layout.addWidget(self.reset_area_btn, 0, 3)
        
        self.open_folder_btn = QPushButton(self.t("open_output_folder"))
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setFixedHeight(35)
        
        self.info_btn = QPushButton(self.t("about"))
        self.info_btn.clicked.connect(self.show_info)
        self.info_btn.setFixedHeight(35)
        
        controls_layout.addWidget(self.open_folder_btn, 1, 0, 1, 2)
        controls_layout.addWidget(self.info_btn, 1, 2, 1, 2)
        
        self.controls_group.setLayout(controls_layout)
        right_layout.addWidget(self.controls_group)
        
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)
        
        main_layout.addLayout(content_layout)
        
        bottom_layout = QHBoxLayout()
        
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.status_label = QLabel(self.t("status_ready"))
        self.status_label.setFont(QFont("Arial", 10))
        
        bottom_layout.addWidget(self.timer_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.status_label)
        
        main_layout.addLayout(bottom_layout)
    
    @abc.abstractmethod
    def get_audio_devices(self):
        pass
    
    def show_audio_device_selector(self):
        dialog = AudioDeviceSelector(self, self.audio_devices, self.t("select_audio_devices"))
        
        for device, _ in self.selected_audio_devices:
            for i in range(dialog.device_list.count()):
                if dialog.device_list.item(i).text() == device:
                    dialog.device_list.item(i).setSelected(True)
                    break

        for device, volume in self.selected_audio_devices:
            if device in dialog.volume_controls:
                dialog.volume_controls[device]['slider'].setValue(volume)
        
        dialog.update_volume_visibility()
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_audio_devices = dialog.get_selected_devices()
            self.save_config()
            self.update_audio_button_text()
    
    def update_audio_button_text(self):
        count = len(self.selected_audio_devices)
        if count == 0:
            text = self.t("select_audio_devices")
        elif count == 1:
            text = f"1 {self.t('audio_device')}"
        else:
            text = f"{count} {self.t('audio_devices')}"
        self.select_audio_btn.setText(text)
    
    def get_selected_audio_devices(self):
        return self.selected_audio_devices
        
    def toggle_preview_monitor(self):
        if self.preview_running:
            self.close_preview()
            self.preview_btn.setText(self.t("start_preview"))
        else:
            self.preview_running = True
            self.preview_timer.start(60)
            self.preview_btn.setText(self.t("stop_preview"))
            
    def update_preview(self):
        if not self.preview_running:
            return
        
        try:
            if not hasattr(self, 'preview_label') or self.preview_label is None:
                return
            
            with mss.mss() as sct:
                monitor_index = self.monitor_combo.currentIndex()
                if monitor_index < len(sct.monitors) - 1:
                    monitor = sct.monitors[monitor_index + 1]
                    
                    if self.record_area:
                        x1, y1, x2, y2 = self.record_area
                        monitor = {
                            "left": x1 + monitor.get("left", 0),
                            "top": y1 + monitor.get("top", 0),
                            "width": x2 - x1,
                            "height": y2 - y1
                        }
                else:
                    monitor = sct.monitors[0]
                    
                if hasattr(self, '_preview_scale'):
                    scaled_monitor = {
                        "left": monitor["left"],
                        "top": monitor["top"],
                        "width": monitor["width"] // 2,
                        "height": monitor["height"] // 2,
                    }
                    screenshot = np.array(sct.grab(scaled_monitor))
                    screenshot = cv2.resize(screenshot, (monitor["width"], monitor["height"]), 
                                        interpolation=cv2.INTER_LINEAR)
                else:
                    screenshot = np.array(sct.grab(monitor))
                
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2RGB)
                
                available_size = self.preview_label.size()
                max_available_width = available_size.width()
                max_available_height = available_size.height()
                max_preview_size = 800
                
                if max_available_height > 50 and max_available_width > 50:
                    original_height = screenshot.shape[0]
                    original_width = screenshot.shape[1]
                    aspect_ratio = original_width / original_height
                    
                    new_height = min(max_available_height - 10, max_preview_size)
                    new_width = int(new_height * aspect_ratio)
                    
                    if new_width > max_available_width - 10:
                        new_width = min(max_available_width - 10, max_preview_size)
                        new_height = int(new_width / aspect_ratio)
                    
                    screenshot = cv2.resize(screenshot, (new_width, new_height), 
                                        interpolation=cv2.INTER_LINEAR)
                else:
                    screenshot = cv2.resize(screenshot, (170, 90), 
                                        interpolation=cv2.INTER_LINEAR)
                
                h, w, ch = screenshot.shape
                bytes_per_line = ch * w
                qt_image = QImage(screenshot.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                pixmap = QPixmap(qt_image)
                
                self.preview_label.setPixmap(pixmap)
                
        except Exception as e:
            self.logger.error(f"Error in preview: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.preview_running:
            QTimer.singleShot(100, self.update_preview)
            
    def close_preview(self):
        self.preview_running = False
        self.preview_timer.stop()
        
        if hasattr(self, 'preview_label') and self.preview_label is not None:
            self.preview_label.clear()
        
    def closeEvent(self, event):
        self.close_preview()
        
        if hasattr(self, 'audio_device_monitor'):
            self.audio_device_monitor.stop_monitoring()
        
        if self.running:
            reply = QMessageBox.question(self, self.t("warning"), self.t("warning_quit"),
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_recording()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def browse_output_folder(self):
        new_folder = QFileDialog.getExistingDirectory(
            self,
            self.t("select_output_folder"),
            self.output_folder
        )
        
        if new_folder:
            self.output_folder = new_folder
            self.output_folder_entry.setText(new_folder)
            self.save_config()
            self.create_output_folder()
            
    def on_monitor_change(self):
        if self.running:
            self.stop_current_recording()
            self.start_new_recording()
        self.save_config()
        
    def start_new_recording(self):
        self.create_new_video_file()
        self.start_recording(continue_timer=True)
        
    def create_new_video_file(self):
        video_name = f"Video_part{self.current_video_part}.{datetime.datetime.now().strftime('%m-%d-%Y.%H.%M.%S')}.mkv"
        self.video_path = os.path.join(self.output_folder, video_name)
        
    def stop_current_recording(self):
        if self.recording_process:
            try:
                self.recording_process.stdin.write('q')
                self.recording_process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            try:
                self.recording_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.recording_process.terminate()
                try:
                    self.recording_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.recording_process.kill()

            if os.path.exists(self.video_path) and os.path.getsize(self.video_path) > 0:
                self.video_parts.append(self.video_path)
            self.current_video_part += 1
            self.recording_process = None
            
    def toggle_recording(self):
        if not self.running:
            self.start_recording()
            self.toggle_btn.setText(self.t("stop_recording"))
        else:
            self.stop_recording()
            self.toggle_btn.setText(self.t("start_recording"))
            
    def create_output_folder(self):
        if not hasattr(self, 'output_folder') or not self.output_folder:
            self.output_folder = os.path.join(os.getcwd(), "OutputFiles")
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            
    def get_monitors(self):
        return get_monitors()
        
    def select_area(self):
        self.area_selector.select_area(self.set_record_area)
        
    def set_record_area(self, record_area):
        self.record_area = record_area
        
    @abc.abstractmethod
    def get_ffmpeg_path(self):
        pass
        
    @abc.abstractmethod
    def start_recording(self, continue_timer=False):
        pass
        
    def update_status_label(self, text):
        self.status_label.setText(text)
        
    def show_error_message(self, error):
        QMessageBox.critical(self, "Error", error)
        
    def stop_recording(self):
        if self.recording_process:
            try:
                self.recording_process.stdin.write('q')
                self.recording_process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            try:
                self.recording_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.recording_process.terminate()
                try:
                    self.recording_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.recording_process.kill()

            for pipe in [self.recording_process.stdin, self.recording_process.stdout, self.recording_process.stderr]:
                try:
                    pipe.close()
                except:
                    pass

            if os.path.exists(self.video_path) and os.path.getsize(self.video_path) > 0:
                self.video_parts.append(self.video_path)

            self.recording_process = None

        self.status_label.setText(self.t("status_saving"))
        self.update()
        
        self.concat_video_parts()
        
        self.toggle_widgets(recording=False)
        self.stop_timer()
        self.status_label.setText(self.t("status_ready"))
        
        self.record_area = None
        self.running = False
        
    def read_ffmpeg_output(self):
        if self.recording_process:
            buffer = []
            last_progress_log = 0
            
            try:
                for stdout_line in iter(self.recording_process.stderr.readline, ""):
                    line = stdout_line.strip()
                    
                    try:
                        if isinstance(line, bytes):
                            line = line.decode('utf-8', errors='replace')
                    except:
                        pass

                    if "A/V sync" in line or "late audio frame" in line or "asynchronous" in line:
                        self.logger.warning(f"Audio sync warning: {line}")
                    elif "error" in line.lower() and "fatal" in line.lower():
                        self.logger.error(f"FFmpeg Critical Error: {line}")
                    elif "error" in line.lower():
                        self.logger.error(f"FFmpeg Error: {line}")
                    elif "warning" in line.lower():
                        self.logger.warning(f"FFmpeg Warning: {line}")
                    elif "frame=" in line or "fps=" in line or "size=" in line:
                        current_time = time.time()
                        if current_time - last_progress_log > 1.0:
                            self.logger.debug(f"FFmpeg Progress: {line}")
                            last_progress_log = current_time
                    elif "configuration:" not in line and "libav" not in line and line:
                        buffer.append(line)

                        if len(buffer) >= 10:
                            self.logger.info(f"FFmpeg Output: {' | '.join(buffer)}")
                            buffer = []
                            
            except BrokenPipeError:
                self.logger.warning("FFMPEG PROCESS HAS BEEN CLOSED")
            except Exception as e:
                self.logger.error(f"ERROR READING FFMPEG OUTPUT: {e}")
            finally:
                if buffer:
                    self.logger.info(f"FFmpeg Output: {' | '.join(buffer)}")
        
    @abc.abstractmethod
    def concat_video_parts(self):
        pass

    def reset_recording_area(self):
        self.record_area = None
        
    def toggle_widgets(self, recording):
        enabled = not recording
        
        self.fps_combo.setEnabled(enabled)
        self.bitrate_combo.setEnabled(enabled)
        self.codec_combo.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.select_audio_btn.setEnabled(enabled)
        self.language_combo.setEnabled(enabled)
        self.theme_combo.setEnabled(enabled)
        self.output_folder_entry.setEnabled(enabled)

        self.select_area_btn.setEnabled(enabled)
        self.open_folder_btn.setEnabled(enabled)
        self.info_btn.setEnabled(enabled)
        self.browse_folder_btn.setEnabled(enabled)
        self.reset_area_btn.setEnabled(enabled)

        self.toggle_btn.setText(self.t("stop_recording") if recording else self.t("start_recording"))
        
        if recording:
            self.toggle_btn.setStyleSheet("background-color: #d9534f; color: white;")
        else:
            self.toggle_btn.setStyleSheet("")
        
        self.status_label.setText(self.t("status_recording") if recording else self.t("status_ready"))
        
    @abc.abstractmethod
    def open_output_folder(self):
        pass
        
    def start_timer(self):
        self.running = True
        self.elapsed_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        
    def stop_timer(self):
        self.running = False
        if hasattr(self, 'timer') and self.timer is not None:
            self.timer.stop()
        self.timer_label.setText("00:00:00")
        self.timer_label.setStyleSheet("")
            
    def update_timer(self):
        if self.running:
            self.elapsed_time += 1
            elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(self.elapsed_time))
            self.timer_label.setText(elapsed_time_str)
            self.timer_label.setStyleSheet("color: #db221d;")
            
    def show_info(self):
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle(self.t("about"))
        info_dialog.resize(360, 260)
        info_dialog.setFixedSize(360, 260)
        
        layout = QVBoxLayout(info_dialog)
        text = self.t("version_info")
        
        text_edit = QTextEdit(info_dialog)
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        if self.translation_manager.is_rtl:
            text_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            text_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
        info_dialog.exec()