from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                           QVBoxLayout, QFrame, QStackedWidget, QLabel)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPalette, QColor
import sys
import logging
from datetime import datetime
import psutil
import os

# Import managers
from server_manager import ServerManager
from module_manager import ModuleManager

# Import pages
from components.dashboard_page import DashboardPage
from components.clients_page import ClientsPage
from components.server_page import ServerPage
from components.builder_page import BuilderPage
from components.modules_page import ModulesPage
from components.settings_page import SettingsPage

class ServerMonitorThread(QThread):
    error_occurred = pyqtSignal(str)
    metrics_updated = pyqtSignal(dict)

    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.running = True

    def run(self):
        while self.running:
            try:
                # Get metrics
                clients_count = len(self.server_manager.get_active_clients())
                server_status = self.server_manager.server_running
                cpu_percent = psutil.cpu_percent()

                # Emit metrics
                self.metrics_updated.emit({
                    'clients_count': clients_count,
                    'server_status': server_status,
                    'cpu_percent': cpu_percent
                })

            except Exception as e:
                self.error_occurred.emit(str(e))
            
            # Sleep for a short interval
            self.msleep(1000)  # Sleep for 1 second

    def stop(self):
        self.running = False
        
class SidebarButton(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, icon, text, is_active=False):
        super().__init__()
        self.is_active = is_active
        self.text = text
        self.icon = icon
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        icon_label = QLabel(self.icon)
        text_label = QLabel(self.text)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()
        
        self.update_style()
        
    def update_style(self):
        base_style = """
            QWidget {
                border-radius: 8px;
                padding: 8px;
                color: white;
            }
        """
        
        if self.is_active:
            self.setStyleSheet(base_style + """
                background-color: rgba(255, 255, 255, 0.1);
            """)
        else:
            self.setStyleSheet(base_style)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            
    def set_active(self, active):
        self.is_active = active
        self.update_style()

class Sidebar(QFrame):
    page_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-right: 1px solid #2d3748;
            }
        """)
        
        self.setFixedWidth(200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Logo area
        logo_widget = QWidget()
        logo_widget.setStyleSheet("""
            QWidget {
                background-color: #1a2234;
                padding: 20px;
            }
        """)
        logo_layout = QHBoxLayout(logo_widget)
        logo_label = QLabel("🔷 Lil Payload")
        logo_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        logo_layout.addWidget(logo_label)
        
        layout.addWidget(logo_widget)
        
        # Navigation buttons
        self.buttons = []
        nav_items = [
            ("🏠", "Dashboard"),
            ("👥", "Clients"),
            ("🖥️", "Server"),
            ("🛠️", "Builder"),
            ("📦", "Modules"),
            ("⚙️", "Settings")
        ]
        
        for i, (icon, text) in enumerate(nav_items):
            btn = SidebarButton(icon, text, i == 0)
            btn.clicked.connect(lambda x=i: self.handle_button_click(x))
            layout.addWidget(btn)
            self.buttons.append(btn)
            
        layout.addStretch()
        
    def handle_button_click(self, index):
        for i, btn in enumerate(self.buttons):
            btn.set_active(i == index)
        self.page_changed.emit(index)

class ModernDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize managers with debug logging
        self.server_manager = ServerManager()
        logging.debug("Server manager initialized")
        self.module_manager = ModuleManager()
        logging.debug("Module manager initialized")
        
        self.setWindowTitle("Lil Payload")
        self.setMinimumSize(1200, 800)
        logging.debug("Setting up UI...")
        self.setup_dark_theme()
        self.setup_ui()
        self.start_monitoring()
        
    def setup_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            QWidget {
                color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #1a2234;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a5568;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
    def setup_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add sidebar
        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)
        
        # Create stacked widget for pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #0f172a;")
        
        # Create and add pages
        self.dashboard_page = DashboardPage(self.server_manager)
        self.clients_page = ClientsPage(self.server_manager)
        self.server_page = ServerPage(self.server_manager)
        self.builder_page = BuilderPage()
        self.modules_page = ModulesPage(self.module_manager)
        self.settings_page = SettingsPage(self.server_manager)
        
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.clients_page)
        self.stack.addWidget(self.server_page)
        self.stack.addWidget(self.builder_page)
        self.stack.addWidget(self.modules_page)
        self.stack.addWidget(self.settings_page)
        
        layout.addWidget(self.stack)
        
        # Connect signals
        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)
        
    def start_updates(self):
        """Start periodic updates"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(5000)  # Update every 5 seconds

    def start_monitoring(self):
        """Start server monitoring in a separate thread"""
        self.monitor_thread = ServerMonitorThread(self.server_manager)
        self.monitor_thread.metrics_updated.connect(self.update_metrics)
        self.monitor_thread.error_occurred.connect(self.handle_monitor_error)
        self.monitor_thread.start()

    def update_metrics(self, metrics):
        """Update UI with new metrics"""
        try:
            # Update dashboard
            self.dashboard_page.update_metrics(
                metrics['clients_count'],
                metrics['server_status'],
                metrics['cpu_percent']
            )
            
            # Update clients page
            self.clients_page.update_clients(self.server_manager.get_active_clients())
            
        except Exception as e:
            logging.error(f"Error updating metrics: {e}")

    def handle_monitor_error(self, error_msg):
        """Handle errors from the monitor thread"""
        logging.error(f"Monitor thread error: {error_msg}")

    def closeEvent(self, event):
        """Handle application closure"""
        try:
            # Stop the monitor thread
            if hasattr(self, 'monitor_thread'):
                self.monitor_thread.stop()
                self.monitor_thread.wait()
            
            # Stop the server
            self.server_manager.stop_server()
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
        
        event.accept()

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    app = QApplication(sys.argv)
    
    # Set application-wide style
    app.setStyle("Fusion")
    
    # Create and show window
    window = ModernDashboard()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()