from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QLineEdit, QScrollArea,
                           QGridLayout, QStackedWidget, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

class ModuleCard(QFrame):
    clicked = pyqtSignal(dict)
    
    def __init__(self, module_data):
        super().__init__()
        self.module_data = module_data
        self.setup_ui()
        self.setFixedHeight(180)
        
    def setup_ui(self):
        # Get category-specific gradient
        gradients = {
            'collection': 'stop:0 #38B2AC, stop:1 #319795',  # Teal
            'credentials': 'stop:0 #F56565, stop:1 #E53E3E',  # Red
            'persistence': 'stop:0 #9F7AEA, stop:1 #805AD5',  # Purple
            'lateral_movement': 'stop:0 #4299E1, stop:1 #3182CE',  # Blue
            'recon': 'stop:0 #48BB78, stop:1 #38A169',  # Green
            'exfil': 'stop:0 #ED8936, stop:1 #DD6B20'   # Orange
        }
        gradient = gradients.get(self.module_data.get('category', 'default'), 'stop:0 #718096, stop:1 #4A5568')
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {gradient});
                border-radius: 15px;
                padding: 20px;
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2D3748, stop:1 #1A202C);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Module name and category
        header_layout = QHBoxLayout()
        
        name = QLabel(self.module_data.get('name', 'Unknown Module'))
        name.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(name)
        
        category = QLabel(self.module_data.get('category', '').title())
        category.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            background-color: rgba(0, 0, 0, 0.2);
            padding: 5px 10px;
            border-radius: 10px;
            font-size: 12px;
        """)
        header_layout.addWidget(category)
        header_layout.addStretch()
        
        # Admin badge if required
        if self.module_data.get('requires_admin', False):
            admin_badge = QLabel("Requires Admin")
            admin_badge.setStyleSheet("""
                color: #FFD700;
                background-color: rgba(0, 0, 0, 0.3);
                padding: 5px 10px;
                border-radius: 10px;
                font-size: 12px;
            """)
            header_layout.addWidget(admin_badge)
            
        layout.addLayout(header_layout)
        
        # Description
        desc = QLabel(self.module_data.get('description', 'No description available'))
        desc.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Footer with author and version
        footer_layout = QHBoxLayout()
        
        author = QLabel(f"👤 {self.module_data.get('author', 'Unknown')}")
        author.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px;")
        footer_layout.addWidget(author)
        
        footer_layout.addStretch()
        
        version = QLabel(f"v{self.module_data.get('version', '1.0')}")
        version.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px;")
        footer_layout.addWidget(version)
        
        layout.addStretch()
        layout.addLayout(footer_layout)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.module_data)

class ModuleDetails(QFrame):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a2234;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Module header
        self.header = QLabel("Select a module")
        self.header.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.header)
        
        # Module description
        self.description = QLabel("")
        self.description.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 16px;")
        self.description.setWordWrap(True)
        layout.addWidget(self.description)
        
        # Arguments section
        self.args_frame = QFrame()
        self.args_frame.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.args_layout = QVBoxLayout(self.args_frame)
        
        args_header = QLabel("Arguments")
        args_header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.args_layout.addWidget(args_header)
        
        layout.addWidget(self.args_frame)
        
        # Execute button
        self.execute_btn = QPushButton("▶️ Execute Module")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38B2AC, stop:1 #319795);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #319795, stop:1 #2C7A7B);
            }
        """)
        layout.addWidget(self.execute_btn)
        
    def update_module(self, module_data):
        """Update module details display"""
        self.header.setText(module_data.get('name', 'Unknown Module'))
        self.description.setText(module_data.get('description', 'No description available'))
        
        # Clear and rebuild arguments
        for i in reversed(range(self.args_layout.count())):
            self.args_layout.itemAt(i).widget().setParent(None)
            
        for arg in module_data.get('arguments', []):
            arg_layout = QHBoxLayout()
            
            label = QLabel(arg.get('name', ''))
            label.setStyleSheet("color: white;")
            arg_layout.addWidget(label)
            
            input_field = QLineEdit()
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #2d3748;
                    border: none;
                    padding: 8px;
                    border-radius: 5px;
                    color: white;
                }
                QLineEdit:focus {
                    background-color: #3d4758;
                }
            """)
            arg_layout.addWidget(input_field)
            
            self.args_layout.addLayout(arg_layout)

class ModulesPage(QWidget):
    def __init__(self, module_manager):
        super().__init__()
        self.module_manager = module_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with search
        header_layout = QHBoxLayout()
        
        header = QLabel("Modules")
        header.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        header_layout.addWidget(header)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search modules...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a2234;
                border: none;
                padding: 10px;
                border-radius: 10px;
                color: white;
                font-size: 14px;
                min-width: 300px;
            }
            QLineEdit:focus {
                background-color: #2d3748;
            }
        """)
        self.search_input.textChanged.connect(self.filter_modules)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        
        layout.addLayout(header_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Modules grid
        self.modules_scroll = QScrollArea()
        self.modules_scroll.setWidgetResizable(True)
        self.modules_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        modules_widget = QWidget()
        self.modules_layout = QGridLayout(modules_widget)
        self.modules_layout.setSpacing(20)
        
        self.modules_scroll.setWidget(modules_widget)
        content_layout.addWidget(self.modules_scroll, stretch=2)
        
        # Module details
        self.module_details = ModuleDetails()
        content_layout.addWidget(self.module_details, stretch=1)
        
        layout.addLayout(content_layout)
        
        # Load modules
        self.load_modules()
        
    def load_modules(self):
        """Load and display modules"""
        try:
            modules = self.module_manager.get_module_list()
            
            # Clear existing modules
            for i in reversed(range(self.modules_layout.count())):
                self.modules_layout.itemAt(i).widget().setParent(None)
            
            # Add module cards
            for i, module in enumerate(modules):
                card = ModuleCard(module)
                card.clicked.connect(self.show_module_details)
                self.modules_layout.addWidget(card, i // 2, i % 2)
                
        except Exception as e:
            logging.error(f"Failed to load modules: {e}")
            
    def filter_modules(self, text):
        """Filter modules based on search text"""
        search = text.lower()
        for i in range(self.modules_layout.count()):
            widget = self.modules_layout.itemAt(i).widget()
            if isinstance(widget, ModuleCard):
                name = widget.module_data.get('name', '').lower()
                desc = widget.module_data.get('description', '').lower()
                widget.setVisible(search in name or search in desc)
                
    def show_module_details(self, module_data):
        """Show selected module details"""
        self.module_details.update_module(module_data)