# handnav.py
import cv2
import pyautogui
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QComboBox, QCheckBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
import numpy as np

class HandNavigationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.tracking = False
        self.cap = None
        
        # Scroll settings
        self.scroll_sensitivity = 20
        self.prev_y = None
        self.scroll_threshold = 0.02
        
        # Detection zone (only detect in bottom half of frame)
        self.detection_zone = "bottom"  # "bottom", "left", "right", "full"
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Hand Navigation")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Make window semi-transparent
        self.setWindowOpacity(0.95)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title with minimize button
        title_layout = QHBoxLayout()
        title = QLabel("👋 Hand Navigation")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title)
        
        # Minimize window button
        btn_minimize = QPushButton("🔽 Minimize")
        btn_minimize.clicked.connect(self.minimize_window)
        btn_minimize.setStyleSheet("padding: 5px; font-size: 12px; max-width: 100px;")
        title_layout.addWidget(btn_minimize)
        
        layout.addLayout(title_layout)
        
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
        
        # Detection zone
        zone_layout = QHBoxLayout()
        zone_label = QLabel("Detection Zone:")
        zone_label.setStyleSheet("font-size: 14px;")
        zone_layout.addWidget(zone_label)
        
        self.zone_combo = QComboBox()
        self.zone_combo.addItems(["Bottom Half (recommended)", "Left Side", "Right Side", "Full Frame"])
        self.zone_combo.currentTextChanged.connect(self.on_zone_changed)
        zone_layout.addWidget(self.zone_combo)
        zone_layout.addStretch()
        layout.addLayout(zone_layout)
        
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
            "• Position your hand in the detection zone (green box)\n"
            "• Keep face and background out of detection zone\n"
            "• Move hand UP to scroll UP\n"
            "• Move hand DOWN to scroll DOWN\n"
            "• Minimize window while tracking to see better"
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
    
    def minimize_window(self):
        """Minimize to a small corner window"""
        self.showMinimized()
    
    def on_zone_changed(self, value):
        """Update detection zone"""
        if "Bottom" in value:
            self.detection_zone = "bottom"
        elif "Left" in value:
            self.detection_zone = "left"
        elif "Right" in value:
            self.detection_zone = "right"
        else:
            self.detection_zone = "full"
        print(f"Detection zone: {self.detection_zone}")
        
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
            
            print("Hand tracking started")
            
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
    
    def get_detection_mask(self, frame_shape):
        """Create mask for detection zone"""
        h, w = frame_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        if self.detection_zone == "bottom":
            # Bottom half only
            mask[h//2:, :] = 255
            zone_rect = (0, h//2, w, h)
        elif self.detection_zone == "left":
            # Left third
            mask[:, :w//3] = 255
            zone_rect = (0, 0, w//3, h)
        elif self.detection_zone == "right":
            # Right third
            mask[:, 2*w//3:] = 255
            zone_rect = (2*w//3, 0, w, h)
        else:
            # Full frame
            mask[:, :] = 255
            zone_rect = (0, 0, w, h)
        
        return mask, zone_rect
    
    def update_frame(self):
        if not self.tracking or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # Flip frame
        frame = cv2.flip(frame, 1)
        
        # Get detection zone
        zone_mask, zone_rect = self.get_detection_mask(frame.shape)
        
        # Draw detection zone
        cv2.rectangle(frame, (zone_rect[0], zone_rect[1]), 
                     (zone_rect[2], zone_rect[3]), (0, 255, 0), 2)
        cv2.putText(frame, "Detection Zone", (zone_rect[0] + 10, zone_rect[1] + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Detect hand in zone
        hand_center = self.detect_hand_in_zone(frame, zone_mask)
        
        if hand_center:
            # Draw circle at hand center
            cv2.circle(frame, hand_center, 15, (0, 255, 0), -1)
            cv2.putText(frame, "Hand Detected", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Process scroll
            hand_y = hand_center[1] / frame.shape[0]
            self.process_scroll(hand_y)
        else:
            self.prev_y = None
            cv2.putText(frame, "Show hand in green zone", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        self.display_frame(frame)
    
    def detect_hand_in_zone(self, frame, zone_mask):
        """Detect hand only in specified zone"""
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Skin color range (tuned to avoid brown backgrounds)
        lower_skin = np.array([0, 30, 60], dtype=np.uint8)
        upper_skin = np.array([20, 150, 255], dtype=np.uint8)
        
        # Create skin mask
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Apply zone mask
        skin_mask = cv2.bitwise_and(skin_mask, skin_mask, mask=zone_mask)
        
        # Morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        skin_mask = cv2.erode(skin_mask, kernel, iterations=1)
        skin_mask = cv2.dilate(skin_mask, kernel, iterations=2)
        skin_mask = cv2.GaussianBlur(skin_mask, (5, 5), 0)
        
        # Find contours
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Filter contours by area and shape
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                # Hand should be reasonably large but not too large (face)
                if 8000 < area < 50000:
                    # Check if contour is somewhat vertical (hand-like)
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = h / w if w > 0 else 0
                    
                    # Hand is usually taller than wide
                    if 0.8 < aspect_ratio < 3.0:
                        valid_contours.append(contour)
            
            if valid_contours:
                # Get largest valid contour
                largest_contour = max(valid_contours, key=cv2.contourArea)
                
                # Get center
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
                # print(f"Scrolling: {scroll_amount}")  # Commented to reduce spam
        
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