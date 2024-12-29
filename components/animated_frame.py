from PyQt6.QtGui import QPalette, QColor
from dataclasses import dataclass
from typing import Dict

@dataclass
class Theme:
    name: str
    primary: str
    secondary: str
    background: str
    surface: str
    text: str
    accent: str
    error: str
    success: str
    warning: str
    info: str

class ThemeManager:
    def __init__(self):
        self.themes = {
            "dark": Theme(
                name="Dark",
                primary="#805AD5",
                secondary="#D53F8C",
                background="#0a192f",
                surface="#1a2332",
                text="#FFFFFF",
                accent="#38B2AC",
                error="#F56565",
                success="#48BB78",
                warning="#ECC94B",
                info="#4299E1"
            ),
            "cyberpunk": Theme(
                name="Cyberpunk",
                primary="#FF0055",
                secondary="#00FFC8",
                background="#120458",
                surface="#1B0C40",
                text="#FFFFFF",
                accent="#00FF9F",
                error="#FF3366",
                success="#00FF9F",
                warning="#FFB800",
                info="#00C8FF"
            ),
            "nord": Theme(
                name="Nord",
                primary="#88C0D0",
                secondary="#81A1C1",
                background="#2E3440",
                surface="#3B4252",
                text="#ECEFF4",
                accent="#A3BE8C",
                error="#BF616A",
                success="#A3BE8C",
                warning="#EBCB8B",
                info="#5E81AC"
            )
        }
        self.current_theme = self.themes["dark"]

    def get_theme(self, name: str) -> Theme:
        return self.themes.get(name, self.themes["dark"])

    def set_theme(self, name: str):
        self.current_theme = self.get_theme(name)
        return self.get_stylesheet()

    def get_stylesheet(self) -> str:
        theme = self.current_theme
        return f"""
            QMainWindow {{
                background-color: {theme.background};
            }}
            
            QLabel {{
                color: {theme.text};
            }}
            
            QPushButton {{
                background-color: {theme.primary};
                color: {theme.text};
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self._adjust_color(theme.primary, 20)};
            }}
            
            QTreeWidget {{
                background-color: {theme.surface};
                border-radius: 10px;
                padding: 15px;
                color: {theme.text};
            }}
            
            QTreeWidget::item:hover {{
                background-color: {self._adjust_color(theme.surface, 20)};
                border-radius: 5px;
            }}
            
            QLineEdit {{
                background-color: {theme.surface};
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: {theme.text};
            }}
            
            QGroupBox {{
                color: {theme.text};
                border: 1px solid {self._adjust_color(theme.surface, 20)};
                border-radius: 10px;
                padding: 20px;
                margin-top: 15px;
            }}
            
            QCheckBox {{
                color: {theme.text};
            }}
            
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {self._adjust_color(theme.surface, 30)};
            }}
            
            QCheckBox::indicator:checked {{
                background: {theme.primary};
                border: 2px solid {theme.primary};
            }}
        """

    def _adjust_color(self, color: str, amount: int) -> str:
        """Lighten or darken a color by the specified amount"""
        if color.startswith('#'):
            color = color[1:]
        
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, max(0, c + amount)) for c in rgb)
        
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"