from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty

class MetricCard(QFrame):
    def __init__(self, title, value, icon, start_color, end_color, tooltip=""):
        super().__init__()
        self.start_color = start_color
        self.end_color = end_color
        self._hover = 0.0
        self.setup_ui(title, value, icon, tooltip)
        
        # Setup hover animation
        self._animation = QPropertyAnimation(self, b"hover")
        self._animation.setDuration(300)
        
    @pyqtProperty(float)
    def hover(self):
        return self._hover
        
    @hover.setter
    def hover(self, value):
        self._hover = value
        self.update()
        
    def setup_ui(self, title, value, icon, tooltip):
        self.setFixedHeight(120)
        self.setToolTip(tooltip)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: white;
            font-size: 16px;
        """)
        title_row.addWidget(title_label)
        title_row.addStretch()
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 20px;
        """)
        title_row.addWidget(icon_label)
        
        layout.addLayout(title_row)
        
        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)
        layout.addWidget(self.value_label)
        
    def paintEvent(self, event):
        if not self:
            return
        
        painter = QPainter(self)
        if not painter.isActive():
            painter.begin(self)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(self.start_color))
        gradient.setColorAt(1, QColor(self.end_color))
        
        # Draw rounded rectangle with gradient
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        
        painter.end()
        
    def update_value(self, new_value):
        self.value_label.setText(str(new_value))
        
    def enterEvent(self, event):
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.start()
        
    def leaveEvent(self, event):
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.start()
