from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTextEdit, 
    QLineEdit, QHBoxLayout, QLabel, QPushButton, QMessageBox, QStatusBar,
    QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QKeySequence, QShortcut
import logging
import time
import threading
from datetime import datetime
import queue

class ShellWorker(QThread):
    responseReceived = pyqtSignal(str)
    connectionStatusChanged = pyqtSignal(bool)
    
    def __init__(self, server_manager, client_id):
        super().__init__()
        self.server_manager = server_manager
        self.client_id = client_id
        self.running = True
        self.logger = logging.getLogger(__name__)
        self._output_buffer = queue.Queue()
        self._check_interval = 0.1  # Faster checks for output

    def run(self):
        while self.running:
            try:
                is_connected = self.server_manager.is_client_connected(self.client_id)
                self.connectionStatusChanged.emit(is_connected)
                
                if is_connected:
                    response = self.server_manager.get_client_response(self.client_id)
                    if response and isinstance(response, dict) and 'data' in response:
                        data = response['data']
                        if data and data.strip():
                            self.responseReceived.emit(data)
                
                time.sleep(self._check_interval)

            except Exception as e:
                self.logger.error(f"Error in shell worker: {e}")
                time.sleep(0.1)

    def stop(self):
        self.running = False

class RemoteShellWindow(QMainWindow):
    def __init__(self, server_manager, client_id):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.server_manager = server_manager
        self.client_id = client_id
        self.is_connected = True
        self.is_closing = False
        self.command_history = []
        self.history_index = 0
        self.logger = logging.getLogger(__name__)
        self._output_buffer = queue.Queue()
        self.shell_worker = None
        self.connection_check_timer = None
        
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
        
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_worker()
        self.setup_connection_monitor()
        self.add_welcome_message()

    def cleanup_resources(self):
        """Clean up all resources safely"""
        try:
            self.is_closing = True
            
            if self.connection_check_timer:
                self.connection_check_timer.stop()
                self.connection_check_timer.deleteLater()
                self.connection_check_timer = None

            if self.shell_worker:
                try:
                    self.shell_worker.stop()
                    self.shell_worker.responseReceived.disconnect()
                    self.shell_worker.connectionStatusChanged.disconnect()
                    if not self.shell_worker.wait(1000):
                        self.shell_worker.terminate()
                    self.shell_worker.deleteLater()
                    self.shell_worker = None
                except Exception as e:
                    self.logger.error(f"Error cleaning up shell worker: {e}")

            self.server_manager.cleanup_shell(self.client_id)
            
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")

    def setup_connection_monitor(self):
        self.connection_check_timer = QTimer(self)
        self.connection_check_timer.timeout.connect(self.check_connection)
        self.connection_check_timer.start(1000)

    def _process_output_buffer(self):
        if not self._output_buffer:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        for line in self._output_buffer:
            formatted_html = (
                f"<span style='color: #718096'>[{timestamp}]</span> "
                f"<span style='color: #4fd1c5'>{line}</span><br>"
            )
            self.output.moveCursor(QTextCursor.MoveOperation.End)
            self.output.insertHtml(formatted_html)
            
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )
        self._output_buffer.clear()


    def setup_worker(self):
        self.shell_worker = ShellWorker(self.server_manager, self.client_id)
        self.shell_worker.responseReceived.connect(self.handle_response, Qt.ConnectionType.QueuedConnection)
        self.shell_worker.connectionStatusChanged.connect(self.update_connection_status, Qt.ConnectionType.QueuedConnection)
        self.shell_worker.start()

    def initialize_worker(self):
        self.shell_worker = ShellWorker(self.server_manager, self.client_id)
        self.shell_worker.responseReceived.connect(self.handle_response)
        self.shell_worker.connectionStatusChanged.connect(self.update_connection_status)
        self.shell_worker.start()

    def start_output_capture(self):
        """Start capturing output from the server"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output.insertHtml(
            f"<span style='color: #38B2AC'>[{timestamp}] Remote Shell Started. "
            f"Connected to {self.client_id}</span><br><br>"
        )

    def start_output_timer(self):
        """Start timer for periodic output checks"""
        self.output_timer = QTimer(self)
        self.output_timer.timeout.connect(self.check_output)
        self.output_timer.start(100)  # Check every 100ms

    def check_output(self):
        """Periodic check for new output"""
        try:
            if not self.is_connected or self.is_closing:
                return

            response = self.server_manager.get_client_response(self.client_id)
            if response and isinstance(response, dict) and 'data' in response:
                self.handle_response(response['data'])
                
        except Exception as e:
            self.logger.error(f"Error checking output: {e}")

    def setup_ui(self):
        """Setup UI elements"""
        self.setWindowTitle(f"Remote Shell - {self.client_id}")
        self.setMinimumSize(800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Remote Shell")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        
        self.status_label = QLabel("Connected")
        self.status_label.setStyleSheet("""
            color: #68D391;
            background: rgba(104, 211, 145, 0.1);
            padding: 5px 10px;
            border-radius: 5px;
        """)
        header.addWidget(self.status_label)
        header.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #4A5568;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #2D3748;
            }
        """)
        clear_btn.clicked.connect(self.clear_output)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #4fd1c5;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.output)
        
        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 5px;")
        input_layout = QHBoxLayout(input_frame)
        
        self.prompt = QLabel("❯")
        self.prompt.setStyleSheet("color: #38B2AC; font-weight: bold;")
        input_layout.addWidget(self.prompt)
        
        self.input = QLineEdit()
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: white;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }
        """)
        self.input.returnPressed.connect(self.send_command)
        input_layout.addWidget(self.input)
        
        layout.addWidget(input_frame)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        self.setStatusBar(self.statusBar)

    def add_welcome_message(self):
        """Add initial welcome message"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            welcome_msg = (
                f"<span style='color: #38B2AC'>[{timestamp}] Remote Shell Started. "
                f"Type commands below.</span><br>"
                f"<span style='color: #718096'>Connected to {self.client_id}</span><br><br>"
            )
            self.output.insertHtml(welcome_msg)
        except Exception as e:
            self.logger.error(f"Error adding welcome message: {e}")


    def setup_shortcuts(self):
        """Setup keyboard shortcuts for command history"""
        up_shortcut = QShortcut(QKeySequence("Up"), self.input)
        up_shortcut.activated.connect(self.previous_command)
        
        down_shortcut = QShortcut(QKeySequence("Down"), self.input)
        down_shortcut.activated.connect(self.next_command)

    def previous_command(self):
        """Show previous command from history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.input.setText(self.command_history[self.history_index])
            self.input.setCursorPosition(len(self.input.text()))

    def next_command(self):
        """Show next command from history"""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input.setText(self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.input.clear()
        self.input.setCursorPosition(len(self.input.text()))

    def handle_response(self, data: str):
        """Handle output from worker thread"""
        if self.is_closing:
            return
            
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_html = (
                f"<span style='color: #718096'>[{timestamp}]</span> "
                f"<span style='color: #4fd1c5'>{data}</span><br>"
            )
            
            # Use invokeMethod to ensure thread safety
            self.output.moveCursor(QTextCursor.MoveOperation.End)
            self.output.insertHtml(formatted_html)
            self.output.verticalScrollBar().setValue(
                self.output.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            if not self.is_closing:
                self.logger.error(f"Error handling response: {e}")

    def update_connection_status(self, connected: bool):
        """Update connection status in UI"""
        try:
            self.is_connected = connected
            if connected:
                self.status_label.setText("Connected")
                self.status_label.setStyleSheet("""
                    color: #68D391;
                    background: rgba(104, 211, 145, 0.1);
                    padding: 5px 10px;
                    border-radius: 5px;
                """)
            else:
                self.status_label.setText("Disconnected")
                self.status_label.setStyleSheet("""
                    color: #FC8181;
                    background: rgba(252, 129, 129, 0.1);
                    padding: 5px 10px;
                    border-radius: 5px;
                """)
        except Exception as e:
            self.logger.error(f"Error updating connection status: {e}")

    def verify_client_connection(self) -> bool:
        """Verify client is still connected"""
        try:
            return self.server_manager.is_client_connected(self.client_id)
        except Exception as e:
            self.logger.error(f"Error verifying client connection: {e}")
            return False


    def verify_connection(self):
        """Verify connection is still alive"""
        try:
            if self.server_manager.is_client_connected(self.client_id):
                if not self.is_connected:
                    self.update_connection_status(True)
            else:
                if self.is_connected:
                    self.update_connection_status(False)
                    
        except Exception as e:
            self.logger.error(f"Error verifying connection: {e}")
            self.update_connection_status(False)

    def handle_connection_loss(self):
        """Handle lost connection"""
        if self.is_connected:  # Only handle if we haven't already handled it
            self.is_connected = False
            self.update_status(False)
            self.input.setEnabled(False)
            
            # Show warning to user
            QMessageBox.warning(
                self,
                "Connection Lost",
                f"Connection to client {self.client_id} has been lost.",
                QMessageBox.StandardButton.Ok
            )
            
            self.connectionLost.emit()

    def send_command(self):
        if not self.is_connected or self.is_closing:
            QMessageBox.warning(self, "Not Connected", "Cannot send command - client disconnected")
            return
            
        command = self.input.text().strip()
        if not command:
            return
            
        try:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.output.moveCursor(QTextCursor.MoveOperation.End)
            self.output.insertHtml(
                f"<span style='color: #718096'>[{timestamp}]</span> "
                f"<span style='color: #38B2AC'>❯</span> "
                f"<span style='color: white'>{command}</span><br>"
            )
            
            if not command.endswith('\n'):
                command += '\n'
                
            success = self.server_manager.send_command(self.client_id, command)
            if not success:
                self.output.insertHtml(
                    "<span style='color: #FC8181'>Failed to send command</span><br>"
                )
                self.update_connection_status(False)
            
            self.input.clear()
            self.output.verticalScrollBar().setValue(
                self.output.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
            self.output.insertHtml(
                f"<span style='color: #FC8181'>Error: {str(e)}</span><br>"
            )

    def show_error_message(self, title: str, message: str):
        """Show error message dialog"""
        QMessageBox.warning(self, title, message, QMessageBox.StandardButton.Ok)

    def check_server_connection(self) -> bool:
        """Check if server is still running and connected"""
        try:
            return (self.server_manager.server_running and 
                    self.server_manager.ncat_process and 
                    self.server_manager.ncat_process.poll() is None)
        except Exception as e:
            self.logger.error(f"Error checking server connection: {e}")
            return False

    def check_connection(self):
        if not self.is_closing:
            connected = self.server_manager.is_client_connected(self.client_id)
            if connected != self.is_connected:
                self.update_connection_status(connected)

    def check_connection_and_response(self):
        """Check for responses while monitoring connection"""
        if not self.is_connected:
            return
            
        try:
            response = self.server_manager.get_client_response(self.client_id)
            if response and 'data' in response:
                data = response['data']
                if data.strip():
                    logging.debug(f"Received response: {data}")
                    
                    # Format and display response
                    formatted_data = f"<span style='color: #4fd1c5'>{data}</span>"
                    self.output.append(formatted_data)
                    
                    # Scroll to bottom
                    cursor = self.output.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.output.setTextCursor(cursor)
                    
        except Exception as e:
            logging.error(f"Error checking response: {e}")
            self.connection_retries += 1
            if self.connection_retries >= self.MAX_RETRIES:
                self.handle_connection_loss()

    def check_response(self):
        try:
            response = self.server_manager.get_client_response(self.client_id)
            if response and 'data' in response:
                data = response['data']
                if data.strip():  # Only process non-empty responses
                    logging.debug(f"Received response: {data}")
                    
                    # Format and display response
                    formatted_data = f"<span style='color: #4fd1c5'>{data}</span>"
                    self.output.append(formatted_data)
                    
                    # Ensure we're scrolled to bottom
                    cursor = self.output.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.output.setTextCursor(cursor)
                    
                    # Update status
                    self.status_label.setText("Connected")
                    self.status_label.setStyleSheet("""
                        color: #68D391;
                        padding: 5px 10px;
                        background-color: rgba(104, 211, 145, 0.1);
                        border-radius: 10px;
                    """)
        except Exception as e:
            logging.error(f"Error checking response: {e}")
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("""
                color: #FC8181;
                padding: 5px 10px;
                background-color: rgba(252, 129, 129, 0.1);
                border-radius: 10px;
            """)

            
    def clear_output(self):
        """Clear the output window"""
        try:
            self.output.clear()
            self.add_welcome_message()
        except Exception as e:
            self.logger.error(f"Error clearing output: {e}")
        
    def update_status(self, connected: bool):
        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #68D391;
                    padding: 5px 10px;
                    background-color: rgba(104, 211, 145, 0.1);
                    border-radius: 10px;
                }
            """)
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #FC8181;
                    padding: 5px 10px;
                    background-color: rgba(252, 129, 129, 0.1);
                    border-radius: 10px;
                }
            """)

    def closeEvent(self, event):
        """Override close to hide instead of destroy"""
        try:
            self.hide()  # Hide window instead of closing
            event.ignore()  # Prevent window destruction
        except Exception as e:
            self.logger.error(f"Error hiding shell: {e}")

    def force_close(self):
        """Actually close and cleanup the window"""
        self.cleanup_resources()
        super().close()
