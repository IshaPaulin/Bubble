# main.py
import sys
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, 
                               QVBoxLayout, QLabel)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QObject
import keyboard
from nightlight import NightLightWindow

class HotkeyListener(QObject):
    hotkey_pressed = Signal()
    
    def __init__(self):
        super().__init__()
        
    def start(self):
        keyboard.add_hotkey('ctrl+shift+space', self.on_hotkey)
        
    def on_hotkey(self):
        self.hotkey_pressed.emit()

class FloatingMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setup_hotkey()
        
    def initUI(self):
        # Remove window frame, keep on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # Main container widget
        container = QWidget()
        container.setStyleSheet("""
            background-color: #2b2b2b;
            border-radius: 10px;
            border: 2px solid #555;
        """)
        
        # Layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Quick Menu")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        layout.addWidget(title)
        
        # Menu options
        btn_recorder = QPushButton("📝 Steps Recorder")
        btn_recorder.clicked.connect(self.open_recorder)
        layout.addWidget(btn_recorder)
        
        btn_nightlight = QPushButton("🌙 Night Light")
        btn_nightlight.clicked.connect(self.open_nightlight)
        layout.addWidget(btn_nightlight)
        
        btn_handtrack = QPushButton("👋 Hand Navigation")
        btn_handtrack.clicked.connect(self.open_handtrack)
        layout.addWidget(btn_handtrack)
        
        btn_close = QPushButton("✕ Close")
        btn_close.clicked.connect(self.toggle_visibility)
        layout.addWidget(btn_close)
        
        # Button styling
        button_style = """
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 12px;
                text-align: left;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """
        for btn in [btn_recorder, btn_nightlight, btn_handtrack, btn_close]:
            btn.setStyleSheet(button_style)
        
        # Set the container as the main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        
        self.setFixedWidth(270)
        self.hide()  # Start hidden
        
    def setup_hotkey(self):
        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.hotkey_pressed.connect(self.toggle_visibility)
        
        # Run keyboard listener in separate thread
        def run_listener():
            self.hotkey_listener.start()
            keyboard.wait()  # Keep thread alive
            
        thread = threading.Thread(target=run_listener, daemon=True)
        thread.start()
        print("Hotkey registered: Ctrl+Shift+Space")
        
    def toggle_visibility(self):
        print(f"Toggle called. Currently visible: {self.isVisible()}")
        if self.isVisible():
            self.hide()
        else:
            # Show at center of screen
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(screen.center().x() - self.width()//2, 
                     screen.center().y() - self.height()//2)
            self.show()
            self.activateWindow()
            self.raise_()
            print("Menu should be visible now")
    
    def open_recorder(self):
        print("Opening Steps Recorder...")
        
    def open_nightlight(self):
        print("Opening Night Light controls...")
        self.nightlight_window = NightLightWindow()
        self.nightlight_window.show()
        
    def open_handtrack(self):
        print("Opening Hand Navigation...")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu = FloatingMenu()
    sys.exit(app.exec())