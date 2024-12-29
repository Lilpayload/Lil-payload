from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QComboBox, QSpinBox,
                           QCheckBox, QLineEdit, QFileDialog, QScrollArea,
                           QStackedWidget, QTextEdit)
from PyQt6.QtCore import Qt
import json
import logging
from pathlib import Path

class SettingsCard(QFrame):
    def __init__(self, title, icon="⚙️"):
        super().__init__()
        self.title = title
        self.icon = icon
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2D3748, stop:1 #1A202C);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"{self.icon} {self.title}")
        header.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding-bottom: 10px;
        """)
        layout.addWidget(header)

class ThemeSettings(SettingsCard):
    def __init__(self):
        super().__init__("Appearance", "🎨")
        self.init_theme_settings()
        
    def init_theme_settings(self):
        settings_layout = QVBoxLayout()
        
        # Theme selector
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #4A5568;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        settings_layout.addLayout(theme_layout)
        
        # Accent color selector
        accent_layout = QHBoxLayout()
        accent_label = QLabel("Accent Color")
        accent_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["Teal", "Blue", "Purple", "Red", "Green"])
        self.accent_combo.setStyleSheet("""
            QComboBox {
                background-color: #4A5568;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                min-width: 150px;
            }
        """)
        
        accent_layout.addWidget(accent_label)
        accent_layout.addWidget(self.accent_combo)
        accent_layout.addStretch()
        settings_layout.addLayout(accent_layout)
        
        self.layout().addLayout(settings_layout)

class ServerSettings(SettingsCard):
    def __init__(self, server_manager):
        super().__init__("Server Configuration", "🖥️")
        self.server_manager = server_manager
        self.init_server_settings()
        
    def init_server_settings(self):
        settings_layout = QVBoxLayout()
        
        # Default port
        port_layout = QHBoxLayout()
        port_label = QLabel("Default Port")
        port_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(4444)
        self.port_input.setStyleSheet("""
            QSpinBox {
                background-color: #4A5568;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                min-width: 150px;
            }
        """)
        
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        settings_layout.addLayout(port_layout)
        
        # Timeout setting
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Connection Timeout (s)")
        timeout_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 300)
        self.timeout_input.setValue(60)
        self.timeout_input.setStyleSheet("""
            QSpinBox {
                background-color: #4A5568;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                min-width: 150px;
            }
        """)
        
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_input)
        timeout_layout.addStretch()
        settings_layout.addLayout(timeout_layout)
        
        self.layout().addLayout(settings_layout)

class LoggingSettings(SettingsCard):
    def __init__(self):
        super().__init__("Logging", "📝")
        self.init_logging_settings()
        
    def init_logging_settings(self):
        settings_layout = QVBoxLayout()
        
        # Log level
        level_layout = QHBoxLayout()
        level_label = QLabel("Log Level")
        level_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.setStyleSheet("""
            QComboBox {
                background-color: #4A5568;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                min-width: 150px;
            }
        """)
        
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        settings_layout.addLayout(level_layout)
        
        # Log file location
        file_layout = QHBoxLayout()
        file_label = QLabel("Log File Location")
        file_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select log file location...")
        self.file_input.setStyleSheet("""
            QLineEdit {
                background-color: #4A5568;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                min-width: 300px;
            }
        """)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4A5568;
            }
        """)
        browse_btn.clicked.connect(self.browse_log_location)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)
        settings_layout.addLayout(file_layout)
        
        self.layout().addLayout(settings_layout)
        
    def browse_log_location(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Select Log File Location", "", "Log Files (*.log)")
        if filename:
            self.file_input.setText(filename)

class SettingsPage(QWidget):
    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with save button
        header_layout = QHBoxLayout()
        
        header = QLabel("Settings")
        header.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        header_layout.addWidget(header)
        
        save_btn = QPushButton("💾 Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38B2AC, stop:1 #319795);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #319795, stop:1 #2C7A7B);
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        header_layout.addStretch()
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # Settings cards in a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(20)
        
        # Add settings cards
        self.theme_settings = ThemeSettings()
        self.server_settings = ServerSettings(self.server_manager)
        self.logging_settings = LoggingSettings()
        
        settings_layout.addWidget(self.theme_settings)
        settings_layout.addWidget(self.server_settings)
        settings_layout.addWidget(self.logging_settings)
        settings_layout.addStretch()
        
        scroll.setWidget(settings_widget)
        layout.addWidget(scroll)
        
        # Load current settings
        self.load_settings()
        
    def load_settings(self):
        """Load saved settings"""
        try:
            settings_file = Path("config/settings.json")
            if settings_file.exists():
                with open(settings_file) as f:
                    settings = json.load(f)
                    
                # Apply settings to UI
                self.theme_settings.theme_combo.setCurrentText(
                    settings.get("theme", "Dark"))
                self.theme_settings.accent_combo.setCurrentText(
                    settings.get("accent_color", "Teal"))
                self.server_settings.port_input.setValue(
                    settings.get("default_port", 4444))
                self.server_settings.timeout_input.setValue(
                    settings.get("timeout", 60))
                self.logging_settings.level_combo.setCurrentText(
                    settings.get("log_level", "INFO"))
                self.logging_settings.file_input.setText(
                    settings.get("log_file", ""))
                    
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")
            
    def save_settings(self):
        """Save current settings"""
        try:
            settings = {
                "theme": self.theme_settings.theme_combo.currentText(),
                "accent_color": self.theme_settings.accent_combo.currentText(),
                "default_port": self.server_settings.port_input.value(),
                "timeout": self.server_settings.timeout_input.value(),
                "log_level": self.logging_settings.level_combo.currentText(),
                "log_file": self.logging_settings.file_input.text()
            }
            
            # Ensure config directory exists
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            # Save settings
            with open(config_dir / "settings.json", "w") as f:
                json.dump(settings, f, indent=4)
                
            # Apply settings
            self.apply_settings(settings)
            
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
            
    def apply_settings(self, settings):
        """Apply the saved settings"""
        # Apply theme
        # Apply server settings
        # Update logging configuration
        pass