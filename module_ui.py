# module_ui.py

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import base64
import threading
from pathlib import Path
from typing import Dict
import logging
from module_manager import ModuleManager

class ModuleUI(ttk.Frame):
    def __init__(self, parent, server_manager):
        super().__init__(parent)
        self.server_manager = server_manager
        self.module_manager = ModuleManager()
        self.setup_ui()

    def setup_ui(self):
        """Setup module interface"""
        # Module list
        list_frame = ttk.LabelFrame(self, text="Available Modules", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Module tree
        self.modules_tree = ttk.Treeview(
            list_frame,
            columns=("Name", "Description", "Admin"),
            show="headings",
            selectmode="browse"
        )

        for col, width in [("Name", 150), ("Description", 300), ("Admin", 50)]:
            self.modules_tree.heading(col, text=col)
            self.modules_tree.column(col, width=width)

        self.modules_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Execute button
        ttk.Button(
            self,
            text="Execute Module",
            command=self._execute_module,
            style="Success.TButton"
        ).pack(pady=5)

        # Output
        output_frame = ttk.LabelFrame(self, text="Output", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.module_output = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            font=("Consolas", 10)
        )
        self.module_output.pack(fill=tk.BOTH, expand=True)

        # Populate modules
        self._populate_modules()

    def _setup_modules_tab(self):
        """Setup modules tab within client session"""
        modules = ttk.Frame(self.session_notebook)
        self.session_notebook.add(modules, text="Modules")

        # Categories frame
        categories_frame = ttk.LabelFrame(modules, text="Categories", padding=5)
        categories_frame.pack(fill=tk.X, pady=5)

        self.category_var = tk.StringVar(value="all")
        categories = [
            ("All", "all"),
            ("Collection", "collection"),
            ("Credentials", "credentials"),
            ("Persistence", "persistence"),
            ("Lateral Movement", "lateral_movement"),
            ("Reconnaissance", "recon"),
            ("Exfiltration", "exfil")
        ]

        for text, value in categories:
            ttk.Radiobutton(
                categories_frame,
                text=text,
                value=value,
                variable=self.category_var,
                command=self._filter_modules
            ).pack(side=tk.LEFT, padx=5)

        # Module list frame
        list_frame = ttk.Frame(modules)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Module tree
        self.modules_tree = ttk.Treeview(
            list_frame,
            columns=("Name", "Description", "Admin"),
            show="headings",
            selectmode="browse"
        )

        for col, width in [("Name", 150), ("Description", 300), ("Admin", 50)]:
            self.modules_tree.heading(col, text=col)
            self.modules_tree.column(col, width=width)

        self.modules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.modules_tree.bind("<<TreeviewSelect>>", self._on_module_select)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.modules_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.modules_tree.configure(yscrollcommand=scrollbar.set)

        # Module details frame
        details_frame = ttk.LabelFrame(modules, text="Module Details", padding=5)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.module_details = scrolledtext.ScrolledText(
            details_frame,
            height=5,
            font=("Consolas", 10)
        )
        self.module_details.pack(fill=tk.BOTH, expand=True, pady=5)

        # Module arguments frame
        self.args_frame = ttk.LabelFrame(modules, text="Arguments", padding=5)
        self.args_frame.pack(fill=tk.X, pady=5)

        # Execute button
        ttk.Button(
            modules,
            text="Execute Module",
            command=self._execute_selected_module,
            style="Success.TButton"
        ).pack(pady=5)

        # Populate modules list
        self._populate_modules()

    def _setup_categories(self, parent):
        """Setup module categories"""
        categories_frame = ttk.LabelFrame(parent, text="Categories", padding=5)
        categories_frame.pack(fill=tk.X, pady=5)

        self.category_var = tk.StringVar(value="all")
        categories = [
            ("All", "all"),
            ("Collection", "collection"),
            ("Credentials", "credentials"),
            ("Persistence", "persistence"),
            ("Lateral Movement", "lateral_movement"),
            ("Reconnaissance", "recon"),
            ("Exfiltration", "exfil")
        ]

        for text, value in categories:
            ttk.Radiobutton(
                categories_frame,
                text=text,
                value=value,
                variable=self.category_var,
                command=self._filter_modules
            ).pack(side=tk.LEFT, padx=5)

    def _setup_module_list(self, parent):
        """Setup module list interface"""
        list_frame = ttk.LabelFrame(parent, text="Available Modules", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Search
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.module_search = ttk.Entry(search_frame)
        self.module_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.module_search.bind('<KeyRelease>', self._filter_modules)

        # Module tree
        self.modules_tree = ttk.Treeview(
            list_frame,
            columns=("Name", "Description", "Author", "Admin"),
            show="headings",
            selectmode="browse"
        )

        for col, width in [("Name", 150), ("Description", 300), ("Author", 100), ("Admin", 50)]:
            self.modules_tree.heading(col, text=col)
            self.modules_tree.column(col, width=width)

        self.modules_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.modules_tree.bind("<<TreeviewSelect>>", self._on_module_select)

    def _setup_execution_frame(self, parent):
        """Setup module execution interface"""
        exec_label_frame = ttk.LabelFrame(parent, text="Module Execution", padding=5)
        exec_label_frame.pack(fill=tk.BOTH, expand=True)

        # Module info
        info_frame = ttk.Frame(exec_label_frame)
        info_frame.pack(fill=tk.X, pady=5)

        self.module_info = scrolledtext.ScrolledText(
            info_frame,
            height=5,
            font=("Consolas", 10)
        )
        self.module_info.pack(fill=tk.X)

        # Arguments frame
        args_frame = ttk.LabelFrame(exec_label_frame, text="Arguments", padding=5)
        args_frame.pack(fill=tk.X, pady=5)

        self.args_frame = ttk.Frame(args_frame)
        self.args_frame.pack(fill=tk.X)

        # Options
        options_frame = ttk.Frame(exec_label_frame)
        options_frame.pack(fill=tk.X, pady=5)

        self.bypass_amsi = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Bypass AMSI",
            variable=self.bypass_amsi
        ).pack(side=tk.LEFT)

        self.run_hidden = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Run Hidden",
            variable=self.run_hidden
        ).pack(side=tk.LEFT)

        # Execute button
        ttk.Button(
            exec_label_frame,
            text="Execute Module",
            command=self._execute_module,
            style="Success.TButton"
        ).pack(pady=5)

        # Output
        output_frame = ttk.LabelFrame(exec_label_frame, text="Output", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.module_output = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            font=("Consolas", 10)
        )
        self.module_output.pack(fill=tk.BOTH, expand=True)


    def _filter_modules(self, event=None):
        """Filter modules based on category and search"""
        try:
            category = self.category_var.get()
            search = self.module_search.get().lower()

            # Clear current list
            for item in self.modules_tree.get_children():
                self.modules_tree.delete(item)

            # Get modules
            modules = self.module_manager.list_modules(
                category if category != "all" else None
            )

            # Apply search filter
            for module in modules:
                if search and not (
                    search in module["name"].lower() or 
                    search in module["description"].lower()
                ):
                    continue

                self.modules_tree.insert("", "end", values=(
                    module["name"],
                    module["description"],
                    module["author"],
                    "Yes" if module["requires_admin"] else "No"
                ))

        except Exception as e:
            self.logger.error(f"Error filtering modules: {e}")

    def _on_module_select(self, event):
        """Handle module selection"""
        try:
            selection = self.modules_tree.selection()
            if not selection:
                return

            # Get module info
            module_name = self.modules_tree.item(selection[0])["values"][0]
            module_info = self.module_manager.get_module_info(module_name)

            if not module_info:
                return

            # Update info display
            info_text = f"""Name: {module_info['name']}
Description: {module_info['description']}
Author: {module_info['author']}
Version: {module_info['version']}
Requires Admin: {'Yes' if module_info['requires_admin'] else 'No'}
Supported OS: {', '.join(module_info['supported_os'])}

Help:
{module_info['help']}"""

            self.module_info.delete(1.0, tk.END)
            self.module_info.insert(tk.END, info_text)

            # Clear existing argument widgets
            for widget in self.args_frame.winfo_children():
                widget.destroy()

            # Create argument inputs
            self.arg_inputs = {}
            for i, arg in enumerate(module_info['arguments']):
                ttk.Label(
                    self.args_frame,
                    text=f"{arg['name']}:"
                ).grid(row=i, column=0, padx=5, pady=2)

                if arg['type'] == 'bool':
                    self.arg_inputs[arg['name']] = tk.BooleanVar()
                    ttk.Checkbutton(
                        self.args_frame,
                        variable=self.arg_inputs[arg['name']]
                    ).grid(row=i, column=1, padx=5, pady=2)
                else:
                    self.arg_inputs[arg['name']] = ttk.Entry(self.args_frame)
                    self.arg_inputs[arg['name']].grid(
                        row=i, column=1, padx=5, pady=2, sticky=tk.EW
                    )

        except Exception as e:
            self.logger.error(f"Error handling module selection: {e}")
            
    def _populate_modules(self):
        """Populate the modules tree initially"""
        try:
            modules = self.module_manager.get_module_list()
            for module in modules:
                self.modules_tree.insert("", "end", values=(
                    module["name"],
                    module["description"],
                    module.get("author", "Unknown"),
                    "Yes" if module["requires_admin"] else "No"
                ))
        except Exception as e:
            self.logger.error(f"Error populating modules: {e}")
            
    def _execute_module(self):
        try:
            selection = self.modules_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "No module selected")
                return

            module_name = self.modules_tree.item(selection[0])["values"][0]
            client_selection = self.master.master.clients_tree.selection()
            if not client_selection:
                messagebox.showwarning("Warning", "No client selected")
                return

            client_values = self.master.master.clients_tree.item(client_selection[0])["values"]
            client_id = f"{client_values[0]}:{client_values[1]}"

            command = self.module_manager.execute_module(module_name)
            
            if self.server_manager.send_command(client_id, command):
                self.module_output.insert(tk.END, f"\n[*] Executing {module_name}...\n")
                
                # Create screenshots directory
                screenshots_dir = Path("screenshots")
                screenshots_dir.mkdir(exist_ok=True)

                # Wait for and process response
                base64_data = []
                screenshot_mode = False
                
                while True:
                    response = self.server_manager.get_client_response(client_id, timeout=30)
                    if not response:
                        break
                        
                    data = response.get('data', '').strip()
                    if data == 'SCREENSHOT_BEGIN':
                        screenshot_mode = True
                    elif data == 'SCREENSHOT_END':
                        screenshot_mode = False
                        # Process complete screenshot
                        if base64_data:
                            try:
                                # Combine and decode base64 data
                                image_data = base64.b64decode(''.join(base64_data))
                                
                                # Save screenshot
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"screenshot_{client_id.replace(':', '_')}_{timestamp}.png"
                                filepath = screenshots_dir / filename
                                
                                with open(filepath, 'wb') as f:
                                    f.write(image_data)
                                
                                self.module_output.insert(tk.END, f"\nScreenshot saved: {filepath}\n")
                                base64_data = []
                            except Exception as e:
                                self.module_output.insert(tk.END, f"\nError saving screenshot: {str(e)}\n")
                    elif screenshot_mode:
                        base64_data.append(data)
                    
            else:
                messagebox.showerror("Error", "Failed to send module command")

        except Exception as e:
            self.module_output.insert(tk.END, f"\nError: {str(e)}\n")
            self.module_output.see(tk.END)

    def _execute_selected_module(self):
        """Execute selected module on client"""
        try:
            if not self.current_client_id:
                messagebox.showwarning("Warning", "No client selected")
                return

            selection = self.modules_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "No module selected")
                return

            module_name = self.modules_tree.item(selection[0])["values"][0]
            
            # Get arguments if any
            arguments = {}
            for widget in self.args_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    name = widget.winfo_name()
                    arguments[name] = widget.get()

            # Execute module
            command = self.module_manager.execute_module(module_name)
            if self.server_manager.send_command(self.current_client_id, command):
                self.session_notebook.select(3)  # Switch to console tab
                self.console_output.configure(state='normal')
                self.console_output.insert(tk.END, f"\n[*] Executing {module_name}...\n", "system")
                self.console_output.configure(state='disabled')
                self.console_output.see(tk.END)
            else:
                messagebox.showerror("Error", "Failed to execute module")

        except Exception as e:
            self.logger.error(f"Error executing module: {e}")
            messagebox.showerror("Error", f"Failed to execute module: {e}")

    def _handle_module_response(self, client_id: str, module_name: str):
        """Handle module response with simplified output"""
        try:
            response = self.server_manager.get_client_response(client_id, timeout=30)
            if response:
                output = response.get('data', '')
                if output:
                    self.module_output.insert(tk.END, str(output) + '\n')
            else:
                self.module_output.insert(tk.END, "No response from client\n", "error")

            self.module_output.see(tk.END)

        except Exception as e:
            self.logger.error(f"Error handling module response: {e}")
            self.module_output.insert(tk.END, f"Error: {str(e)}\n", "error")
            self.module_output.see(tk.END)

        except Exception as e:
            self.logger.error(f"Error handling module response: {e}")

    def _handle_screenshot_output(self, data: dict):
        """Handle screenshot module output"""
        try:
            if 'ImageData' in data:
                screenshot_handler = ScreenshotHandler(Path("screenshots"))
                result = screenshot_handler.save_screenshot(data['ImageData'])
                
                # Add to screenshot list
                self.screenshot_list.insert("", 0, values=(
                    result['timestamp'],
                    f"{os.path.getsize(result['path']) / 1024:.1f} KB",
                    data.get('Resolution', 'Unknown')
                ))
                
                self.module_output.insert(tk.END, f"\nScreenshot saved: {result['filename']}\n")
        except Exception as e:
            self.logger.error(f"Error handling screenshot: {e}")
            self.module_output.insert(tk.END, f"\nError saving screenshot: {str(e)}\n")

    def _process_module_output(self, module_name: str, data: Dict):
        """Process and display module-specific output"""
        try:
            if module_name == "Capture-Screenshot":
                self._handle_screenshot_output(data)
            # Add handlers for other modules
            else:
                # Generic output handling
                self.module_output.insert(
                    tk.END,
                    f"\nOutput:\n{json.dumps(data, indent=2)}\n"
                )

        except Exception as e:
            self.logger.error(f"Error processing module output: {e}")

    def _process_module_output(self, module_name: str, data: Dict):
        """Process and display module-specific output"""
        try:
            if module_name == "Capture-Screenshot":
                self._handle_screenshot_output(data)
            # Add handlers for other modules
            else:
                # Generic output handling
                self.module_output.insert(
                    tk.END,
                    f"\nOutput:\n{json.dumps(data, indent=2)}\n"
                )

        except Exception as e:
            self.logger.error(f"Error processing module output: {e}")