from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QFrame, QTextEdit)
from PyQt6.QtCore import Qt
from datetime import datetime

class LogEntry(QWidget):
    def __init__(self, time, message):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        time_label = QLabel(f"[{time}]")
        time_label.setStyleSheet("color: #4fd1c5; font-family: 'Courier New';")
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #4fd1c5; font-family: 'Courier New';")
        
        layout.addWidget(time_label)
        layout.addWidget(message_label)
        layout.addStretch()

class MetricCard(QFrame):
    def __init__(self, title, value, icon, start_color, end_color, tooltip=""):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {start_color}, stop:1 {end_color});
                border-radius: 15px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px;")
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        
        if tooltip:
            self.setToolTip(tooltip)

    def update_value(self, value):
        self.value_label.setText(value)

class DashboardPage(QWidget):
    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.setup_ui()
        self.initial_logs()
        
    def setup_ui(self):
        self.setStyleSheet("background-color: #0f172a;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Dashboard")
        header.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        layout.addWidget(header)
        
        # Metrics
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)
        
        self.clients_card = MetricCard(
            "Clients", "1", "👥", "#38B2AC", "#319795"
        )
        self.server_card = MetricCard(
            "Server", "1", "🖥️", "#F56565", "#E53E3E"
        )
        self.usage_card = MetricCard(
            "Usage", "1.45%", "📊", "#9F7AEA", "#805AD5"
        )
        
        metrics_layout.addWidget(self.clients_card)
        metrics_layout.addWidget(self.server_card)
        metrics_layout.addWidget(self.usage_card)
        layout.addLayout(metrics_layout)
        
        # Activity Log
        log_container = QFrame()
        log_container.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        log_layout = QVBoxLayout(log_container)
        
        log_header = QLabel("Recent Activity")
        log_header.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        log_layout.addWidget(log_header)
        
        self.log_area = QWidget()
        self.log_layout = QVBoxLayout(self.log_area)
        self.log_layout.setSpacing(8)
        
        scroll = QScrollArea()
        scroll.setWidget(self.log_area)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        log_layout.addWidget(scroll)
        layout.addWidget(log_container)
        
    def initial_logs(self):
        logs = [
            ("17:32:41", "SUCCESS: Loaded 6.0 frame!"),
            ("17:32:41", "SUCCESS: Connecting to Server \"T234\""),
            ("17:32:41", "INFO: Scribus 6.0"),
            ("17:32:41", "INFO: Welcome, User!"),
            ("17:32:54", "INFO: Client \"Client\" connected!")
        ]
        for time, message in logs:
            self.add_log(time, message)
            
    def add_log(self, time, message):
        log_entry = LogEntry(time, message)
        self.log_layout.insertWidget(0, log_entry)
        
    def update_metrics(self, clients_count, server_status, usage_percent):
        self.clients_card.update_value(str(clients_count))
        self.server_card.update_value("1" if server_status else "0")
        self.usage_card.update_value(f"{usage_percent}%")