from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget
from PyQt6.QtCore import Qt

class ActivityLog(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1a2332;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Scrollable area for log entries
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.log_widget = QWidget()
        self.log_layout = QVBoxLayout(self.log_widget)
        self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.log_widget)
        
        layout.addWidget(scroll)
        
        # Add "No recent activity" message
        self.no_activity = QLabel("No recent activity")
        self.no_activity.setStyleSheet("""
            color: #718096;
            font-size: 14px;
            padding: 20px;
        """)
        self.log_layout.addWidget(self.no_activity)
        
    def add_entry(self, text, type="info"):
        if self.no_activity.isVisible():
            self.no_activity.hide()
            
        colors = {
            "info": "#4299E1",
            "success": "#48BB78",
            "warning": "#ECC94B",
            "error": "#F56565"
        }
        
        entry = QLabel(text)
        entry.setStyleSheet(f"""
            color: {colors.get(type, colors['info'])};
            font-size: 14px;
            padding: 10px;
            background-color: {colors.get(type, colors['info'])}22;
            border-radius: 5px;
        """)
        
        self.log_layout.insertWidget(0, entry)  # Add new entries at the top