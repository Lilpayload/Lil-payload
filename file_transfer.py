import os
import base64
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple, List
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QInputDialog, QDialog, QVBoxLayout, QProgressDialog

class FileUploadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, file_transfer, client_id, local_path, remote_path):
        super().__init__()
        self.file_transfer = file_transfer
        self.client_id = client_id
        self.local_path = local_path
        self.remote_path = remote_path
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        try:
            # Validate file exists
            if not os.path.exists(self.local_path):
                self.finished.emit(False, "Local file does not exist")
                return

            # Read file content
            with open(self.local_path, 'rb') as f:
                content = f.read()

            # Set up PowerShell script
            filename = os.path.basename(self.local_path)
            if not self.remote_path:
                self.remote_path = f"$env:TEMP\\{filename}"
            elif self.remote_path.endswith('\\') or self.remote_path.endswith('/'):
                self.remote_path = self.remote_path + filename
            elif os.path.splitext(self.remote_path)[1] == '':
                self.remote_path = os.path.join(self.remote_path, filename).replace('\\', '\\\\')

            ps_script = f"""
            $ErrorActionPreference = 'Stop'
            try {{
                $path = '{self.remote_path}'
                [System.IO.File]::WriteAllBytes($path, [byte[]]({','.join(str(b) for b in content)}))
                if (Test-Path $path) {{
                    $fileInfo = Get-Item $path
                    Write-Output "SUCCESS|$($fileInfo.Length)|$path"
                }} else {{
                    Write-Error "File verification failed"
                }}
                exit 0
            }} catch {{
                Write-Error "ERROR|$_"
                exit 1
            }}
            """

            self.progress.emit(f"Uploading {filename}...")
            
            if not self.file_transfer.server_manager.send_command(self.client_id, ps_script):
                self.finished.emit(False, "Failed to send upload command")
                return

            # Process response with timeout
            max_attempts = 5
            success_message = None
            
            for _ in range(max_attempts):
                response = self.file_transfer.server_manager.get_client_response(self.client_id)
                if not response:
                    time.sleep(0.1)
                    continue
                    
                data = response.get('data', '').strip()
                if not data:
                    continue
                    
                if data.startswith("SUCCESS|"):
                    _, size, path = data.split("|")
                    success_message = f"File uploaded successfully to {path} ({size} bytes)"
                    break
                elif data.startswith("ERROR|"):
                    self.finished.emit(False, data.split("|")[1])
                    return
                elif "error" in data.lower():
                    self.finished.emit(False, data)
                    return

            if success_message:
                self.finished.emit(True, success_message)
            else:
                self.finished.emit(False, "Upload failed - no confirmation received")

        except Exception as e:
            self.finished.emit(False, f"Upload failed: {str(e)}")

class FileTransfer:
    def __init__(self, server_manager):
        self.server_manager = server_manager
        self.logger = logging.getLogger(__name__)
        
    def upload_to_target(self, client_id: str, local_path: str, remote_path: Optional[str] = None) -> Tuple[bool, str]:
        """Upload file to target with minimal connection impact"""
        try:
            if not os.path.exists(local_path):
                return False, "Local file does not exist"

            filename = os.path.basename(local_path)
            if not remote_path:
                remote_path = f"$env:TEMP\\{filename}"
            elif remote_path.endswith('\\') or remote_path.endswith('/'):
                remote_path = remote_path + filename
            elif os.path.splitext(remote_path)[1] == '':
                remote_path = os.path.join(remote_path, filename).replace('\\', '\\\\')

            # Read file in chunks to reduce memory usage
            chunk_size = 1024 * 1024  # 1MB chunks
            total_chunks = os.path.getsize(local_path) // chunk_size + 1

            # First command: Create directory and prepare file
            prep_command = f"""
            $ErrorActionPreference = 'Stop'
            try {{
                $path = '{remote_path}'
                $directory = Split-Path -Parent $path
                if (!(Test-Path $directory)) {{
                    New-Item -ItemType Directory -Force -Path $directory | Out-Null
                }}
                if (Test-Path $path) {{
                    Remove-Item $path -Force
                }}
                Write-Output "READY"
            }} catch {{
                Write-Error $_
                exit 1
            }}
            """

            if not self.server_manager.send_command(client_id, prep_command):
                return False, "Failed to prepare upload"

            # Wait for ready signal
            for _ in range(10):  # 1-second timeout
                response = self.server_manager.get_client_response(client_id)
                if response and response.get('data', '').strip() == "READY":
                    break
                time.sleep(0.1)
            else:
                return False, "Failed to get ready signal"

            # Upload file in chunks
            with open(local_path, 'rb') as f:
                chunk_num = 0
                while chunk := f.read(chunk_size):
                    chunk_num += 1
                    chunk_b64 = base64.b64encode(chunk).decode()
                    
                    # Write chunk command
                    chunk_command = f"""
                    try {{
                        $chunk = [System.Convert]::FromBase64String('{chunk_b64}')
                        Add-Content -Path '{remote_path}' -Value $chunk -Encoding Byte
                        Write-Output "CHUNK_{chunk_num}"
                    }} catch {{
                        Write-Error $_
                        exit 1
                    }}
                    """

                    if not self.server_manager.send_command(client_id, chunk_command):
                        return False, f"Failed to send chunk {chunk_num}"

                    # Wait for chunk confirmation
                    for _ in range(10):
                        response = self.server_manager.get_client_response(client_id)
                        if response and response.get('data', '').strip() == f"CHUNK_{chunk_num}":
                            break
                        time.sleep(0.1)
                    else:
                        return False, f"Failed to confirm chunk {chunk_num}"

            # Verify file
            verify_command = f"""
            try {{
                if (Test-Path '{remote_path}') {{
                    $fileInfo = Get-Item '{remote_path}'
                    Write-Output "SUCCESS|$($fileInfo.Length)|{remote_path}"
                }} else {{
                    throw "File verification failed"
                }}
            }} catch {{
                Write-Error $_
                exit 1
            }}
            """

            if not self.server_manager.send_command(client_id, verify_command):
                return False, "Failed to verify upload"

            # Process verification response
            for _ in range(10):
                response = self.server_manager.get_client_response(client_id)
                if not response:
                    time.sleep(0.1)
                    continue
                    
                data = response.get('data', '').strip()
                if data.startswith("SUCCESS|"):
                    _, size, path = data.split("|")
                    return True, f"File uploaded successfully to {path} ({size} bytes)"
                    
            return False, "Upload verification failed"

        except Exception as e:
            self.logger.error(f"Upload error: {str(e)}")
            return False, f"Upload failed: {str(e)}"

    def download_from_target(self, client_id: str, remote_path: str, local_path: str) -> bool:
        """Download file from target"""
        try:
            ps_script = f"""
            if (Test-Path '{remote_path}') {{
                Copy-Item '{remote_path}' -Destination '{local_path}' -Force
                Write-Output "File downloaded successfully"
            }} else {{
                Write-Error "File not found"
            }}
            """
            
            if not self.server_manager.send_command(client_id, ps_script):
                return False
            
            response = self.server_manager.get_client_response(client_id)
            return response and "successfully" in response.get('data', '').lower()
            
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            return False

    def list_remote_files(self, client_id: str, remote_path: str) -> Optional[List[Dict]]:
        """List files in remote directory"""
        try:
            ps_script = f"""
            Get-ChildItem '{remote_path}' | Select-Object Name, Length, LastWriteTime | ConvertTo-Json
            """
            
            if not self.server_manager.send_command(client_id, ps_script):
                return None
            
            response = self.server_manager.get_client_response(client_id)
            if response and response.get('data'):
                return json.loads(response.get('data', ''))
                
            return None
            
        except Exception as e:
            self.logger.error(f"List files error: {e}")
            return None