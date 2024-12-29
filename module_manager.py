import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import importlib.resources
import base64


@dataclass
class PSModule:
    name: str
    description: str
    author: str
    version: str
    requires_admin: bool
    supported_os: List[str]
    code: str
    help_text: str
    arguments: List[Dict]

class ModuleManager:
    """Manages PowerShell post-exploitation modules"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.modules_dir = Path(os.path.abspath("modules"))
        self.loaded_modules = {}
        self._load_modules()

    def _load_modules(self):
        """Load all modules from the modules directory"""
        try:
            # Create default module directories if they don't exist
            categories = [
                "collection", "credentials", "persistence",
                "lateral_movement", "exfil", "recon"
            ]
            
            self.logger.info(f"Loading modules from: {self.modules_dir}")
            
            # Ensure base modules directory exists
            if not self.modules_dir.exists():
                self.logger.warning(f"Creating modules directory: {self.modules_dir}")
                self.modules_dir.mkdir(parents=True, exist_ok=True)

            # Load modules from each category
            for category in categories:
                category_path = self.modules_dir / category
                self.logger.debug(f"Checking category: {category} at {category_path}")
                
                if category_path.exists():
                    for ps1_file in category_path.glob("*.ps1"):
                        try:
                            self.logger.debug(f"Found PS1 file: {ps1_file}")
                            content = ps1_file.read_text(encoding='utf-8')
                            self.logger.debug(f"Read content from {ps1_file}")
                            metadata = self._parse_metadata(content)
                            if metadata:
                                self.logger.info(f"Successfully parsed metadata for {ps1_file}")
                                metadata['category'] = category
                                metadata['path'] = str(ps1_file)
                                self.loaded_modules[metadata['name']] = metadata
                                self.logger.info(f"Loaded module: {metadata['name']}")
                            else:
                                self.logger.warning(f"No metadata found in {ps1_file}")
                        except Exception as e:
                            self.logger.error(f"Failed to load module {ps1_file}: {str(e)}")
                else:
                    self.logger.debug(f"Category directory not found: {category_path}")

            self.logger.info(f"Successfully loaded {len(self.loaded_modules)} modules")

        except Exception as e:
            self.logger.error(f"Failed to load modules: {str(e)}")

    def _parse_metadata(self, content: str) -> Optional[Dict]:
        """Parse module metadata from comment block"""
        try:
            metadata = {}
            # Look for metadata between <# and #>
            match = re.search(r'<#(.*?)#>', content, re.DOTALL)
            if match:
                metadata_text = match.group(1)
                # Parse each metadata field
                fields = {
                    'Module': 'name',
                    'Description': 'description', 
                    'Author': 'author',
                    'Version': 'version',
                    'RequiresAdmin': 'requires_admin',
                    'SupportedOS': 'supported_os',
                    'Arguments': 'arguments',
                    'Help': 'help'
                }
                
                for field, key in fields.items():
                    field_match = re.search(f'{field}:\s*(.*?)(?=\n[A-Za-z]|$)', metadata_text)
                    if field_match:
                        value = field_match.group(1).strip()
                        
                        if key == 'requires_admin':
                            metadata[key] = value.lower() == 'true'
                        elif key == 'supported_os':
                            metadata[key] = [os.strip() for os in value.split(',')]
                        elif key == 'arguments':
                            args = []
                            if value:  # Check if there are any arguments
                                for arg in value.split(','):
                                    if ':' in arg:
                                        name, arg_type = arg.strip().split(':')
                                        args.append({'name': name.strip(), 'type': arg_type.strip()})
                            metadata[key] = args
                        else:
                            metadata[key] = value

                # Extract the actual PowerShell code (everything after the metadata block)
                code_match = re.search(r'#>(.*)', content, re.DOTALL)
                if code_match:
                    metadata['code'] = code_match.group(1).strip()
                else:
                    metadata['code'] = ""

                return metadata
                
            return None

        except Exception as e:
            self.logger.error(f"Error parsing metadata: {e}")
            return None

    def create_module_template(self, category: str, name: str) -> Path:
        """Create a new module template"""
        try:
            template = '''<#
Module: {name}
Description: Module description here
Author: Your name
Version: 1.0
RequiresAdmin: false
SupportedOS: Windows
Arguments: target:string, port:int
Help: Detailed help text here
#>

function Invoke-{name} {{
    param(
        [Parameter(Mandatory=$true)]
        [string]$target,
        
        [Parameter(Mandatory=$true)]
        [int]$port
    )

    try {{
        # Module code here
        
        # Return results
        return @{{
            "Status" = "Success"
            "Data" = $null
        }}
    }}
    catch {{
        return @{{
            "Status" = "Error"
            "Message" = $_.Exception.Message
        }}
    }}
}}
'''
            
            module_path = self.modules_dir / category / f"{name}.ps1"
            module_path.write_text(template.format(name=name))
            return module_path
        except Exception as e:
            self.logger.error(f"Error creating module template: {str(e)}")
            raise

    def execute_module(self, module_name: str, arguments: Dict = None) -> str:
        """Get module execution command with proper PowerShell encoding"""
        try:
            if module_name not in self.loaded_modules:
                raise ValueError(f"Module {module_name} not found")
                
            module = self.loaded_modules[module_name]
            code = module['code']
            
            # Format arguments if any
            args_str = ""
            if arguments:
                args_str = " ".join([f"-{k} '{v}'" for k, v in arguments.items()])
                
            # Combine code and execution into single command
            ps_command = f"{code}\nInvoke-{module_name} {args_str}"
            
            # Convert to Base64 for reliable transmission
            ps_bytes = ps_command.encode('utf-16le')
            ps_b64 = base64.b64encode(ps_bytes).decode()
            
            # Return PowerShell command that will decode and execute
            return f'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand {ps_b64}'

        except Exception as e:
            self.logger.error(f"Error preparing module: {str(e)}")
            raise

    def get_module_info(self, module_name: str) -> Optional[Dict]:
        """Get detailed module information"""
        if module_name not in self.loaded_modules:
            return None
            
        module_info = self.loaded_modules[module_name]
        # Convert arguments list to dict format if needed
        if 'arguments' in module_info and isinstance(module_info['arguments'], list):
            args_dict = {}
            for arg in module_info['arguments']:
                if isinstance(arg, dict) and 'name' in arg and 'type' in arg:
                    args_dict[arg['name']] = {'type': arg['type']}
            module_info['arguments'] = args_dict
        
        return module_info

    def get_module_list(self) -> List[Dict]:
        """Get list of available modules"""
        return [
            {
                "name": info.get("name", name),
                "description": info.get("description", ""),
                "category": info.get("category", "unknown"),
                "requires_admin": info.get("requires_admin", False),
                "author": info.get("author", "Unknown")
            }
            for name, info in self.loaded_modules.items()
        ]

    def validate_arguments(self, module_name: str, arguments: Dict) -> bool:
        """Validate module arguments"""
        try:
            module = self.loaded_modules.get(module_name)
            if not module:
                return False

            required_args = {arg['name']: arg['type'] for arg in module.get('arguments', [])}
            
            # Check all required arguments are present
            for arg_name, arg_type in required_args.items():
                if arg_name not in arguments:
                    return False
                    
                # Validate argument type
                value = arguments[arg_name]
                try:
                    if arg_type == 'int':
                        int(value)
                    elif arg_type == 'bool':
                        str(value).lower() in ('true', 'false')
                    # Add more type validations as needed
                except:
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Error validating arguments: {str(e)}")
            return False