# handnav.py
import cv2
try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    NEW_API = True
except ImportError:
    import mediapipe as mp
    NEW_API = False

import pyautogui
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QComboBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
import numpy as np

class HandNavigationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.tracking = False
        self.cap = None
        self.hand_detector = None
        
        # Scroll settings
        self.scroll_sensitivity = 20
        self.prev_y = None
        self.scroll_threshold = 0.02
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Hand Navigation")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("👋 Hand Navigation")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Camera preview
        self.camera_label = QLabel("Camera Preview")
        self.camera_label.setStyleSheet("""
            background-color: #1a1a1a;
            border: 2px solid #555;
            border-radius: 5px;
            min-height: 300px;
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camera_label)
        
        # Status
        self.status_label = QLabel("⚪ Camera inactive")
        self.status_label.setStyleSheet("font-size: 13px; padding: 8px; background-color: #3d3d3d; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        # Gesture mode selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Gesture Mode:")
        mode_label.setStyleSheet("font-size: 14px;")
        mode_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Scroll", "Mouse Move (coming soon)"])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Sensitivity control
        sensitivity_layout = QHBoxLayout()
        sensitivity_label = QLabel("Scroll Sensitivity:")
        sensitivity_label.setStyleSheet("font-size: 14px;")
        sensitivity_layout.addWidget(sensitivity_label)
        
        self.sensitivity_combo = QComboBox()
        self.sensitivity_combo.addItems(["Low", "Medium", "High"])
        self.sensitivity_combo.setCurrentIndex(1)
        self.sensitivity_combo.currentTextChanged.connect(self.on_sensitivity_changed)
        sensitivity_layout.addWidget(self.sensitivity_combo)
        sensitivity_layout.addStretch()
        layout.addLayout(sensitivity_layout)
        
        # Instructions
        instructions = QLabel(
            "📌 Instructions:\n"
            "• Show your open palm to the camera\n"
            "• Move hand UP to scroll UP\n"
            "• Move hand DOWN to scroll DOWN\n"
            "• Keep hand steady when not scrolling"
        )
        instructions.setStyleSheet("""
            font-size: 12px; 
            color: #aaa; 
            background-color: #3d3d3d; 
            padding: 10px; 
            border-radius: 5px;
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Start Tracking")
        self.btn_start.clicked.connect(self.start_tracking)
        self.btn_start.setStyleSheet("padding: 12px; font-size: 14px;")
        controls_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹️ Stop Tracking")
        self.btn_stop.clicked.connect(self.stop_tracking)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("padding: 12px; font-size: 14px;")
        controls_layout.addWidget(self.btn_stop)
        
        layout.addLayout(controls_layout)
        
        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("margin-top: 10px; padding: 8px;")
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: white;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666;
            }
            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        self.setMinimumSize(500, 700)
        
    def on_sensitivity_changed(self, value):
        if value == "Low":
            self.scroll_sensitivity = 10
        elif value == "Medium":
            self.scroll_sensitivity = 20
        else:
            self.scroll_sensitivity = 30
        print(f"Scroll sensitivity: {value} ({self.scroll_sensitivity})")
    
    def start_tracking(self):
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.status_label.setText("❌ Could not access camera")
                return
            
            self.tracking = True
            self.prev_y = None
            
            # Update UI
            self.status_label.setText("🟢 Tracking active")
            self.status_label.setStyleSheet("font-size: 13px; padding: 8px; background-color: #204a20; border-radius: 5px; color: #6bff6b;")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            
            # Start timer
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(30)
            
            print("Hand tracking started (using simple color detection)")
            
        except Exception as e:
            print(f"Error starting tracking: {e}")
            self.status_label.setText(f"❌ Error: {e}")
    
    def stop_tracking(self):
        self.tracking = False
        
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        if self.cap:
            self.cap.release()
        
        self.camera_label.setText("Camera Preview")
        
        self.status_label.setText("⚪ Camera inactive")
        self.status_label.setStyleSheet("font-size: 13px; padding: 8px; background-color: #3d3d3d; border-radius: 5px;")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        print("Hand tracking stopped")
    
    def update_frame(self):
        if not self.tracking or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # Flip frame
        frame = cv2.flip(frame, 1)
        
        # Simple hand detection using skin color
        hand_center = self.detect_hand_simple(frame)
        
        if hand_center:
            # Draw circle at hand center
            cv2.circle(frame, hand_center, 15, (0, 255, 0), -1)
            cv2.putText(frame, "Hand Detected", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Process scroll
            hand_y = hand_center[1] / frame.shape[0]  # Normalize to 0-1
            self.process_scroll(hand_y)
        else:
            self.prev_y = None
            cv2.putText(frame, "No hand detected", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        self.display_frame(frame)
    
    def detect_hand_simple(self, frame):
        """Simple hand detection using skin color in HSV"""
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Skin color range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        # Create mask
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Blur to reduce noise
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Only process if contour is large enough
            if cv2.contourArea(largest_contour) > 5000:
                # Get center of mass
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
        
        return None
    
    def process_scroll(self, current_y):
        if self.prev_y is None:
            self.prev_y = current_y
            return
        
        delta_y = current_y - self.prev_y
        
        if abs(delta_y) > self.scroll_threshold:
            scroll_amount = int(-delta_y * self.scroll_sensitivity * 100)
            
            if scroll_amount != 0:
                pyautogui.scroll(scroll_amount)
                print(f"Scrolling: {scroll_amount}")
        
        self.prev_y = current_y
    
    def display_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.camera_label.width(), 
            self.camera_label.height(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.camera_label.setPixmap(scaled_pixmap)
    
    def closeEvent(self, event):
        self.stop_tracking()
        event.accept()