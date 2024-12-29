from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QLineEdit, QTableWidgetItem,
                           QMessageBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.client_table import ClientTable
from .remote_shell import RemoteShellWindow

class ClientsPage(QWidget):
    def __init__(self, server_manager, module_manager=None):
        super().__init__()
        self.server_manager = server_manager
        self.module_manager = module_manager
        self.logger = logging.getLogger(__name__)
        self.shell_windows = {}
        self.setup_ui()
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_clients)
        self.refresh_timer.start(1000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with search
        header_layout = QHBoxLayout()
        
        header = QLabel("Clients")
        header.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Search box with icon
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 0, 10, 0)
        
        search_icon = QLabel("🔍")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find by Name")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: white;
                padding: 5px;
                min-width: 200px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_input)
        
        header_layout.addWidget(search_container)
        layout.addLayout(header_layout)
        
        # Show alias toggle
        alias_layout = QHBoxLayout()
        alias_layout.addStretch()
        
        self.show_alias = QPushButton("Show Alias")
        self.show_alias.setCheckable(True)
        self.show_alias.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 10px;
            }
            QPushButton:checked {
                background-color: #38B2AC;
            }
        """)
        alias_layout.addWidget(self.show_alias)
        
        layout.addLayout(alias_layout)
        
        # Create clients table
        try:
            self.clients_table = ClientTable(self.server_manager, self.module_manager)
            layout.addWidget(self.clients_table)
        except Exception as e:
            logging.error(f"Error creating client table: {e}")
            raise

    def launch_shell(self, client_id: str):
        try:
            # Check for existing window
            if client_id in self.shell_windows:
                shell = self.shell_windows[client_id]
                try:
                    if shell.isVisible():
                        shell.raise_()
                        shell.activateWindow()
                        return
                    # If window exists but isn't visible, show it
                    shell.show()
                    return
                except RuntimeError:
                    # Window was deleted, clean it up
                    self.shell_windows.pop(client_id, None)
            
            # Create new window only if needed
            shell = RemoteShellWindow(self.server_manager, client_id)
            shell.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            
            def cleanup_handler():
                if client_id in self.shell_windows:
                    self.shell_windows.pop(client_id, None)
            
            shell.destroyed.connect(cleanup_handler)
            self.shell_windows[client_id] = shell
            shell.show()
            
        except Exception as e:
            self.logger.error(f"Failed to open shell: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open shell: {str(e)}")

    def handle_shell_closed(self, client_id: str):
        if client_id in self.shell_windows:
            shell = self.shell_windows[client_id]
            if shell and not shell.is_closing:
                shell.cleanup_resources()
            self.shell_windows.pop(client_id, None)

    def cleanup_shell(self, client_id: str):
        """Force close and cleanup shell window"""
        if client_id in self.shell_windows:
            try:
                shell = self.shell_windows[client_id]
                if shell:
                    shell.force_close()
            except RuntimeError:
                pass
            finally:
                self.shell_windows.pop(client_id, None)

    def cleanup_all_shells(self):
        """Cleanup all shell windows on page close"""
        for client_id in list(self.shell_windows.keys()):
            self.cleanup_shell(client_id)

    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup_all_shells()
        if self.refresh_timer:
            self.refresh_timer.stop()
        super().closeEvent(event)

    def closeEvent(self, event):
        for shell in list(self.shell_windows.values()):
            try:
                shell.close()
            except:
                pass
        self.shell_windows.clear()
        event.accept()

    def update_clients(self, clients):
        """Update the clients table with current client data"""
        try:
            self.logger.debug(f"Updating clients table with {len(clients)} clients")
            self.clients_table.setRowCount(len(clients))
            
            for row, client in enumerate(clients):
                self.logger.debug(f"Processing client row {row}: {client}")
                
                try:
                    address = client.get('address', ['Unknown', 'Unknown'])
                    
                    # Create and set items with error checking
                    items = [
                        (0, client.get('name', 'Unknown')),
                        (1, str(address[0])),
                        (2, str(address[1])),
                        (3, client.get('os', 'Unknown')),
                        (4, client.get('status', 'Unknown')),
                        (5, client.get('connected_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S') 
                           if isinstance(client.get('connected_at'), datetime) 
                           else str(client.get('connected_at', 'Unknown'))),
                        (6, client.get('ping', 'N/A'))
                    ]
                    
                    for col, value in items:
                        item = QTableWidgetItem(str(value))
                        self.clients_table.setItem(row, col, item)
                        
                        # Set color based on status
                        status = client.get('status', '').lower()
                        color = QColor('#4fd1c5') if status == 'connected' else QColor('#f56565')
                        item.setForeground(color)
                        
                    self.logger.debug(f"Successfully updated row {row}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing client row {row}: {e}", exc_info=True)
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error updating clients table: {e}", exc_info=True)
            
    def refresh_clients(self):
        """Refresh the clients list with debug logging"""
        try:
            clients = self.server_manager.get_active_clients()
            self.logger.debug(f"Raw clients data: {clients}")
            self.logger.info(f"Refreshing clients - found {len(clients)} clients")
            
            if clients:
                self.logger.debug(f"Client details: {clients}")
                    
            self.update_clients(clients)
                
        except Exception as e:
            self.logger.error(f"Error refreshing clients: {e}", exc_info=True)

    def filter_clients(self):
        """Filter clients based on search text"""
        search_text = self.search_input.text().lower()
        for row in range(self.clients_table.rowCount()):
            show = False
            for col in range(self.clients_table.columnCount()):
                item = self.clients_table.item(row, col)
                if item and search_text in item.text().lower():
                    show = True
                    break
            self.clients_table.setRowHidden(row, not show)