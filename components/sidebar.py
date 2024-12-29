from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QLinearGradient, QColor, QPainter

class SidebarButton(QPushButton):
    def __init__(self, icon, tooltip=""):
        super().__init__()
        self.setFixedSize(70, 70)
        self.setText(icon)
        self.setToolTip(tooltip)
        self.setFont(QFont('Segoe UI', 16))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QPushButton[Active=true] {
                color: white;
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)

    def paintEvent(self, event):
        if not self:
            return
        
        painter = QPainter(self)
        if not painter.isActive():
            painter.begin(self)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        if self.property("Active"):
            painter.setBrush(QColor(255, 255, 255, 25))
        else:
            painter.setBrush(QColor(255, 255, 255, 10))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        painter.end()

class Sidebar(QWidget):
    page_changed = pyqtSignal(int)
    
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.setFixedWidth(70)
        self.setup_ui()
        
    def setup_ui(self):
        # Set gradient background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #93C5FD,
                    stop:1 #A78BFA);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo
        logo = QLabel("⬢")
        logo.setFixedHeight(70)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color: white; font-size: 32px;")
        layout.addWidget(logo)
        
        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("⌂", "Dashboard", 0),
            ("⚇", "Clients", 1),
            ("▤", "Server", 2),
            ("⊡", "Builder", 3),
            ("⚙", "Settings", 4),
            ("≡", "Modules", 5)
        ]
        
        for icon, tooltip, index in nav_items:
            btn = SidebarButton(icon, tooltip)
            btn.clicked.connect(lambda c, i=index: self.change_page(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        layout.addStretch()
        
        # Expand button
        expand_btn = SidebarButton("❯")
        layout.addWidget(expand_btn)
        
        # Stack widget
        self.stack = QStackedWidget()
        
    def change_page(self, index):
        self.stack.setCurrentIndex(index)
        self.page_changed.emit(index)
        
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("Active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
