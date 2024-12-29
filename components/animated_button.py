from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty, Qt
from PyQt6.QtGui import QColor

class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._background = QColor("#805AD5")
        
        # Position animation
        self._pos_animation = QPropertyAnimation(self, b"geometry")
        self._pos_animation.setDuration(200)
        self._pos_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Color animation
        self._color_animation = QPropertyAnimation(self, b"background_color")
        self._color_animation.setDuration(200)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        
    @pyqtProperty(QColor)
    def background_color(self):
        return self._background
        
    @background_color.setter
    def background_color(self, color):
        self._background = color
        self.update_style()
        
    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._background.name()};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(self._background, 20).name()};
            }}
        """)
        
    def _darken_color(self, color: QColor, amount: int) -> QColor:
        """Darken a color by the specified amount"""
        h = color.hue()
        s = color.saturation()
        l = max(0, color.lightness() - amount)
        return QColor.fromHsl(h, s, l)
        
    def enterEvent(self, event):
        # Scale animation
        rect = self.geometry()
        self._pos_animation.setStartValue(rect)
        self._pos_animation.setEndValue(rect.adjusted(-2, -2, 2, 2))
        self._pos_animation.start()
        
        # Color animation
        start_color = QColor(self._background)
        end_color = self._darken_color(self._background, 20)
        self._color_animation.setStartValue(start_color)
        self._color_animation.setEndValue(end_color)
        self._color_animation.start()
        
    def leaveEvent(self, event):
        # Scale animation
        rect = self.geometry()
        self._pos_animation.setStartValue(rect)
        self._pos_animation.setEndValue(rect.adjusted(2, 2, -2, -2))
        self._pos_animation.start()
        
        # Color animation
        self._color_animation.setStartValue(self._darken_color(self._background, 20))
        self._color_animation.setEndValue(QColor(self._background))
        self._color_animation.start()