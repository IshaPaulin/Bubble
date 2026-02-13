# main.py
import sys
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, 
                               QVBoxLayout, QLabel)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QObject
from PySide6.QtGui import QMouseEvent
import keyboard
from nightlight import NightLightWindow
from recorder import StepsRecorderWindow
from handnav import HandNavigationWindow

class HotkeyListener(QObject):
    hotkey_pressed = Signal()
    f9_pressed = Signal()
    
    def __init__(self):
        super().__init__()
        
    def start(self):
        keyboard.add_hotkey('ctrl+shift+space', self.on_hotkey)
        keyboard.add_hotkey('f9', self.on_f9)
        
    def on_hotkey(self):
        self.hotkey_pressed.emit()
    
    def on_f9(self):
        self.f9_pressed.emit()

class FloatingMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder_window = None
        self.drag_position = QPoint()  # For dragging
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
        
        # Title (draggable area)
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
    
    # Add these methods for dragging
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        
    def setup_hotkey(self):
        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.hotkey_pressed.connect(self.toggle_visibility)
        self.hotkey_listener.f9_pressed.connect(self.on_f9_global)
        
        # Run keyboard listener in separate thread
        def run_listener():
            self.hotkey_listener.start()
            keyboard.wait()
            
        thread = threading.Thread(target=run_listener, daemon=True)
        thread.start()
        print("Hotkeys registered: Ctrl+Shift+Space (menu), F9 (capture)")
        
    def on_f9_global(self):
        """Handle global F9 press - hide menu during capture"""
        if self.recorder_window and self.recorder_window.recording:
            # Hide main menu before capture
            menu_was_visible = self.isVisible()
            if menu_was_visible:
                self.hide()
            
            # Capture after brief delay
            QTimer.singleShot(100, lambda: self._do_capture_and_restore(menu_was_visible))
    
    def _do_capture_and_restore(self, restore_menu):
        """Perform capture and restore menu visibility"""
        self.recorder_window.capture_step()
        
        # Restore menu after capture completes (wait for screenshot to finish)
        if restore_menu:
            QTimer.singleShot(500, self.show)
        
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
        if not self.recorder_window:
            self.recorder_window = StepsRecorderWindow()
        self.recorder_window.show()
        
    def open_nightlight(self):
        print("Opening Night Light controls...")
        self.nightlight_window = NightLightWindow()
        self.nightlight_window.show()
        
    def open_handtrack(self):
        print("Opening Hand Navigation...")
        self.handnav_window = HandNavigationWindow()
        self.handnav_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu = FloatingMenu()
    sys.exit(app.exec())