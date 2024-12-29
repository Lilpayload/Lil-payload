from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QLineEdit, QSpinBox,
                           QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt
import logging

class ServerControls(QFrame):
    def __init__(self, server_manager, log_widget):
        super().__init__()
        self.server_manager = server_manager
        self.log_widget = log_widget  # Store reference to log widget
        self.setup_ui()
        self.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Server configuration
        config_layout = QHBoxLayout()
        
        # IP input
        ip_layout = QVBoxLayout()
        ip_label = QLabel("IP Address")
        ip_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        self.ip_input = QLineEdit()
        self.ip_input.setText("0.0.0.0")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d3748;
                border: none;
                padding: 8px;
                border-radius: 5px;
                color: white;
            }
            QLineEdit:focus {
                background-color: #3d4758;
            }
        """)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        
        # Port input
        port_layout = QVBoxLayout()
        port_label = QLabel("Port")
        port_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(4444)
        self.port_input.setStyleSheet("""
            QSpinBox {
                background-color: #2d3748;
                border: none;
                padding: 8px;
                border-radius: 5px;
                color: white;
            }
            QSpinBox:focus {
                background-color: #3d4758;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: transparent;
                border: none;
            }
        """)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        
        config_layout.addLayout(ip_layout)
        config_layout.addLayout(port_layout)
        layout.addLayout(config_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.verbose_checkbox = QCheckBox("Verbose Output")
        self.keep_listening_checkbox = QCheckBox("Keep Listening")
        self.keep_listening_checkbox.setChecked(True)
        
        for checkbox in [self.verbose_checkbox, self.keep_listening_checkbox]:
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: rgba(255, 255, 255, 0.8);
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: none;
                    background-color: #2d3748;
                }
                QCheckBox::indicator:checked {
                    background-color: #4299e1;
                }
                QCheckBox::indicator:hover {
                    background-color: #3d4758;
                }
            """)
            options_layout.addWidget(checkbox)
            
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶️ Start Server")
        self.stop_button = QPushButton("⏹️ Stop Server")
        self.stop_button.setEnabled(False)
        
        for button in [self.start_button, self.stop_button]:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4A5568;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2D3748;
                }
                QPushButton:disabled {
                    background-color: #1a202c;
                    color: rgba(255, 255, 255, 0.3);
                }
            """)
            buttons_layout.addWidget(button)
            
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        
        layout.addLayout(buttons_layout)
        
    def start_server(self):
        """Start the server with current configuration"""
        try:
            ip = self.ip_input.text()
            port = self.port_input.value()
            verbose = self.verbose_checkbox.isChecked()
            keep_listening = self.keep_listening_checkbox.isChecked()
            
            logging.debug(f"Starting server on {ip}:{port}")
            logging.debug(f"Verbose: {verbose}, Keep Listening: {keep_listening}")
            
            success = self.server_manager.start_server(
                ip,
                port,
                verbose,
                keep_listening
            )
            
            if success:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.ip_input.setEnabled(False)
                self.port_input.setEnabled(False)
                self.log_widget.add_log(f"Server started on {ip}:{port}", "SUCCESS")
            else:
                self.log_widget.add_log("Failed to start server", "ERROR")
            
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            self.log_widget.add_log(f"Error: {str(e)}", "ERROR")
            
    def stop_server(self):
        """Stop the server"""
        try:
            if self.server_manager.stop_server():
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.ip_input.setEnabled(True)
                self.port_input.setEnabled(True)
                self.log_widget.add_log("Server stopped", "INFO")
                
        except Exception as e:
            logging.error(f"Failed to stop server: {e}")
            self.log_widget.add_log(f"Error: {str(e)}", "ERROR")

class ServerLog(QFrame):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Server Log")
        header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                border: none;
                border-radius: 5px;
                color: #4fd1c5;
                font-family: 'Courier New';
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_text)
        
    def add_log(self, message: str, level: str = "INFO"):
        """Add a new log entry"""
        color = {
            "INFO": "#4fd1c5",
            "WARNING": "#f6e05e",
            "ERROR": "#fc8181",
            "SUCCESS": "#68d391"
        }.get(level, "#4fd1c5")
        
        self.log_text.append(f'<span style="color: {color}">[{level}] {message}</span>')
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

class ServerPage(QWidget):
    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Server Control")
        header.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)
        layout.addWidget(header)
        
        # Server log
        self.log = ServerLog()
        
        # Server controls with log reference
        self.controls = ServerControls(self.server_manager, self.log)
        layout.addWidget(self.controls)
        
        # Add log after controls
        layout.addWidget(self.log)
        
    def update_status(self, is_running: bool, client_count: int):
        """Update server status display"""
        status = "Running" if is_running else "Stopped"
        status_color = "#68d391" if is_running else "#fc8181"
        self.status_label.setText(f'Server Status: <span style="color: {status_color}">{status}</span>')
        self.connected_clients.setText(f"Connected Clients: {client_count}")