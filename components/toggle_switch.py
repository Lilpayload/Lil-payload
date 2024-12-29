from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

class ToggleSwitch(QWidget):
    clicked = pyqtSignal(bool)
    
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self._enabled = False
        self._margin = 2
        self._handle_position = self._margin
        
        # Setup animation
        self._animation = QPropertyAnimation(self, b"handle_position", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Setup layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self.label = QLabel(text)
        self.label.setStyleSheet("""
            color: #64748b;
            font-size: 14px;
            font-weight: 500;
        """)
        layout.addWidget(self.label)
        
        # Toggle container
        self.toggle = QWidget()
        self.toggle.setFixedSize(44, 24)
        layout.addWidget(self.toggle)
        layout.addStretch()
        
        self.setLayout(layout)
        
    @pyqtProperty(float)
    def handle_position(self):
        return self._handle_position
        
    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.toggle.update()
        
    def paintEvent(self, event):
        if not self.toggle:
            return
        
        painter = QPainter(self.toggle)
        if not painter.isActive():
            painter.begin(self.toggle)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw track
        track_color = QColor("#22c55e") if self._enabled else QColor("#e2e8f0")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 4, 44, 16, 8, 8)
        
        # Draw handle
        handle_color = QColor("white")
        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.setBrush(handle_color)
        
        handle_y = 0
        handle_size = 24
        painter.drawEllipse(int(self._handle_position), handle_y, handle_size, handle_size)
        
        painter.end()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._enabled = not self._enabled
            self.clicked.emit(self._enabled)
            
            # Animate handle
            start = self._margin if not self._enabled else 18
            end = 18 if self._enabled else self._margin
            
            self._animation.setStartValue(start)
            self._animation.setEndValue(end)
            self._animation.start()
        
    def isChecked(self):
        return self._enabled
        
    def setChecked(self, checked):
        if self._enabled != checked:
            self._enabled = checked
            self._handle_position = 18 if checked else self._margin
            self.toggle.update()
