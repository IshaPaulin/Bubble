# nightlight.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QSlider, QPushButton)
from PySide6.QtCore import Qt
import screen_brightness_control as sbc

class NightLightWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Night Light Control")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🌙 Night Light")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Brightness control
        brightness_label = QLabel("Brightness")
        brightness_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(brightness_label)
        
        brightness_container = QHBoxLayout()
        self.brightness_value_label = QLabel("100%")
        self.brightness_value_label.setStyleSheet("font-size: 14px; min-width: 50px;")
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(10)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        
        brightness_container.addWidget(self.brightness_slider)
        brightness_container.addWidget(self.brightness_value_label)
        layout.addLayout(brightness_container)
        
        # Warmth control (color temperature simulation)
        warmth_label = QLabel("Warmth (Color Temperature)")
        warmth_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(warmth_label)
        
        warmth_container = QHBoxLayout()
        self.warmth_value_label = QLabel("0%")
        self.warmth_value_label.setStyleSheet("font-size: 14px; min-width: 50px;")
        
        self.warmth_slider = QSlider(Qt.Horizontal)
        self.warmth_slider.setMinimum(0)
        self.warmth_slider.setMaximum(100)
        self.warmth_slider.setValue(0)
        self.warmth_slider.valueChanged.connect(self.on_warmth_changed)
        
        warmth_container.addWidget(self.warmth_slider)
        warmth_container.addWidget(self.warmth_value_label)
        layout.addLayout(warmth_container)
        
        # Info text
        info = QLabel("Note: Warmth control uses Windows Night Light API")
        info.setStyleSheet("font-size: 11px; color: #888; margin-top: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Preset buttons
        preset_label = QLabel("Quick Presets")
        preset_label.setStyleSheet("font-size: 14px; margin-top: 15px;")
        layout.addWidget(preset_label)
        
        preset_container = QHBoxLayout()
        
        btn_day = QPushButton("☀️ Day")
        btn_day.clicked.connect(lambda: self.apply_preset(100, 0))
        preset_container.addWidget(btn_day)
        
        btn_evening = QPushButton("🌆 Evening")
        btn_evening.clicked.connect(lambda: self.apply_preset(70, 50))
        preset_container.addWidget(btn_evening)
        
        btn_night = QPushButton("🌙 Night")
        btn_night.clicked.connect(lambda: self.apply_preset(40, 80))
        preset_container.addWidget(btn_night)
        
        layout.addLayout(preset_container)
        
        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("margin-top: 15px; padding: 8px;")
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: white;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #3d3d3d;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #5d5d5d;
                border: 1px solid #777;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #6d6d6d;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        
        self.setFixedWidth(400)

        # Reset button
        btn_reset = QPushButton("🔄 Reset to Normal")
        btn_reset.clicked.connect(self.reset_colors)
        btn_reset.setStyleSheet("margin-top: 10px; padding: 8px; background-color: #4a4a4a;")
        layout.addWidget(btn_reset)
        
        # Load current brightness
        try:
            current_brightness = sbc.get_brightness()[0]
            self.brightness_slider.setValue(current_brightness)
        except:
            print("Could not get current brightness")

    def on_brightness_changed(self, value):
        self.brightness_value_label.setText(f"{value}%")
        try:
            sbc.set_brightness(value)
        except Exception as e:
            print(f"Error setting brightness: {e}")
    
    def on_warmth_changed(self, value):
        self.warmth_value_label.setText(f"{value}%")
        # Windows Night Light control
        self.set_night_light(value)
    
    def set_night_light(self, strength):
        """
        Set color temperature using gamma ramps (0-100)
        Higher values = warmer (more orange/red)
        """
        try:
            import ctypes
            import ctypes.wintypes
            
            # Get device context for the screen
            hdc = ctypes.windll.user32.GetDC(None)
            
            if strength == 0:
                # Reset to normal (neutral color)
                gamma_array = (ctypes.c_ushort * 256)()
                for i in range(256):
                    gamma_array[i] = i * 256
                
                ctypes.windll.gdi32.SetDeviceGammaRamp(hdc, 
                    ctypes.byref(gamma_array * 3))
            else:
                # Calculate color shift based on strength
                # Reduce blue channel, keep red/green higher
                red_gamma = (ctypes.c_ushort * 256)()
                green_gamma = (ctypes.c_ushort * 256)()
                blue_gamma = (ctypes.c_ushort * 256)()
                
                # Strength affects how much blue light we reduce
                blue_reduction = strength / 100.0
                
                for i in range(256):
                    # Red channel - slightly boosted
                    red_value = min(65535, int(i * 256 * (1.0 + blue_reduction * 0.1)))
                    red_gamma[i] = red_value
                    
                    # Green channel - slightly reduced
                    green_value = int(i * 256 * (1.0 - blue_reduction * 0.2))
                    green_gamma[i] = green_value
                    
                    # Blue channel - heavily reduced for warmth
                    blue_value = int(i * 256 * (1.0 - blue_reduction * 0.6))
                    blue_gamma[i] = blue_value
                
                # Combine into one array (RGB)
                gamma_ramp = (ctypes.c_ushort * 768)()
                for i in range(256):
                    gamma_ramp[i] = red_gamma[i]
                    gamma_ramp[i + 256] = green_gamma[i]
                    gamma_ramp[i + 512] = blue_gamma[i]
                
                # Apply gamma ramp
                result = ctypes.windll.gdi32.SetDeviceGammaRamp(hdc, 
                    ctypes.byref(gamma_ramp))
                
                if result:
                    print(f"✓ Night Light strength set to: {strength}%")
                else:
                    print("✗ Failed to set gamma ramp")
            
            ctypes.windll.user32.ReleaseDC(None, hdc)
            
        except Exception as e:
            print(f"Error setting Night Light: {e}")

    def reset_colors(self):
        """Reset both brightness and color temperature"""
        self.brightness_slider.setValue(100)
        self.warmth_slider.setValue(0)
    
    def apply_preset(self, brightness, warmth):
        """Apply a preset configuration"""
        self.brightness_slider.setValue(brightness)
        self.warmth_slider.setValue(warmth)