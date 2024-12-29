from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
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
    opacity: float = 1.0

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
            "light": Theme(
                name="Light",
                primary="#805AD5",
                secondary="#D53F8C",
                background="#F7FAFC",
                surface="#EDF2F7",
                text="#1A202C",
                accent="#319795",
                error="#E53E3E",
                success="#38A169",
                warning="#D69E2E",
                info="#3182CE"
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
            )
        }
        self.current_theme = self.themes["dark"]
        self.transparency_enabled = False
        self.blur_enabled = False

    def set_theme(self, name: str):
        if name in self.themes:
            self.current_theme = self.themes[name]
            self._update_app_style()

    def set_transparency(self, enabled: bool):
        self.transparency_enabled = enabled
        self._update_app_style()

    def set_blur(self, enabled: bool):
        self.blur_enabled = enabled
        self._update_app_style()

    def _update_app_style(self):
        app = QApplication.instance()
        if app:
            opacity = 0.95 if self.transparency_enabled else 1.0
            self.current_theme.opacity = opacity
            app.setStyleSheet(self.get_stylesheet())

    def get_stylesheet(self) -> str:
        theme = self.current_theme
        opacity = int(255 * theme.opacity)
        bg_color = QColor(theme.background)
        bg_color.setAlpha(opacity)
        
        surface_color = QColor(theme.surface)
        surface_color.setAlpha(opacity)

        return f"""
            QMainWindow {{
                background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, {opacity});
            }}
            
            QWidget {{
                color: {theme.text};
                background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, {opacity});
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
                background-color: rgba({surface_color.red()}, {surface_color.green()}, {surface_color.blue()}, {opacity});
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
            
            QFrame {{
                background-color: rgba({surface_color.red()}, {surface_color.green()}, {surface_color.blue()}, {opacity});
            }}
            
            #sidebar {{
                background-color: rgba({surface_color.red()}, {surface_color.green()}, {surface_color.blue()}, {opacity});
                border-radius: 10px;
                padding: 15px;
            }}
            
            #metric-card {{
                background-color: rgba({surface_color.red()}, {surface_color.green()}, {surface_color.blue()}, {opacity});
                border-radius: 10px;
                padding: 15px;
            }}
            
            #dashboard-page {{
                background-color: rgba({surface_color.red()}, {surface_color.green()}, {surface_color.blue()}, {opacity});
                border-radius: 10px;
                padding: 15px;
            }}
        """

    def _adjust_color(self, color: str, amount: int) -> str:
        if color.startswith('#'):
            color = color[1:]
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, max(0, c + amount)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
