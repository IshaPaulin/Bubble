# recorder.py
import os
import json
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QListWidget, QComboBox, QTextEdit,
                               QScrollArea, QFrame, QListWidgetItem)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QImage
import pyautogui
import pygetwindow as gw
from PIL import Image
import mss
import requests

class StepItem(QFrame):
    """Widget to display a single captured step"""
    def __init__(self, step_data, step_number):
        super().__init__()
        self.step_data = step_data
        self.initUI(step_number)
        
    def initUI(self, step_number):
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout()
        
        # Step number and timestamp
        info_layout = QVBoxLayout()
        
        step_label = QLabel(f"Step {step_number}")
        step_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(step_label)
        
        time_label = QLabel(self.step_data['timestamp'])
        time_label.setStyleSheet("font-size: 11px; color: #aaa;")
        info_layout.addWidget(time_label)
        
        # Window info
        if 'window' in self.step_data:
            window_label = QLabel(f"Window: {self.step_data['window']}")
            window_label.setStyleSheet("font-size: 11px; color: #ccc;")
            info_layout.addWidget(window_label)
        
        # Actions (keyboard/mouse)
        if 'actions' in self.step_data and self.step_data['actions']:
            actions_text = ", ".join(self.step_data['actions'])
            action_label = QLabel(f"Actions: {actions_text}")
            action_label.setStyleSheet("font-size: 11px; color: #9cf;")
            action_label.setWordWrap(True)
            info_layout.addWidget(action_label)
        
        layout.addLayout(info_layout, stretch=3)
        
        # Thumbnail (if screenshot exists)
        if 'screenshot' in self.step_data:
            thumbnail = QLabel()
            pixmap = QPixmap(self.step_data['screenshot'])
            thumbnail.setPixmap(pixmap.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumbnail.setStyleSheet("border: 1px solid #666;")
            layout.addWidget(thumbnail, stretch=1)
        
        self.setLayout(layout)


class StepsRecorderWindow(QWidget):
    # Signal for external capture trigger
    capture_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.steps = []
        self.output_dir = "recordings"
        self.current_session_dir = None
        
        # Create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Steps Recorder")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📝 Steps Recorder")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Status indicator
        self.status_label = QLabel("⚪ Ready to record")
        self.status_label.setStyleSheet("font-size: 13px; padding: 8px; background-color: #3d3d3d; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Start Recording")
        self.btn_start.clicked.connect(self.start_recording)
        self.btn_start.setStyleSheet("padding: 12px; font-size: 14px;")
        controls_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹️ Stop Recording")
        self.btn_stop.clicked.connect(self.stop_recording)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("padding: 12px; font-size: 14px;")
        controls_layout.addWidget(self.btn_stop)
        
        self.btn_capture = QPushButton("📸 Capture Now (F9)")
        self.btn_capture.clicked.connect(self.capture_step)
        self.btn_capture.setEnabled(False)
        self.btn_capture.setStyleSheet("padding: 12px; font-size: 14px; background-color: #4a4a4a;")
        controls_layout.addWidget(self.btn_capture)
        
        layout.addLayout(controls_layout)
        
        # Steps counter
        self.steps_counter = QLabel("Steps captured: 0")
        self.steps_counter.setStyleSheet("font-size: 13px; color: #aaa;")
        layout.addWidget(self.steps_counter)
        
        # Steps list
        steps_label = QLabel("Captured Steps:")
        steps_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(steps_label)
        
        # Scroll area for steps
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #555; background-color: #2b2b2b; }")
        
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.steps_container)
        
        layout.addWidget(scroll, stretch=1)
        
        # Export section
        export_layout = QHBoxLayout()
        
        self.btn_export = QPushButton("📄 Export Report")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("padding: 10px; font-size: 13px;")
        export_layout.addWidget(self.btn_export)
        
        self.btn_clear = QPushButton("🗑️ Clear All")
        self.btn_clear.clicked.connect(self.clear_steps)
        self.btn_clear.setStyleSheet("padding: 10px; font-size: 13px;")
        export_layout.addWidget(self.btn_clear)
        
        layout.addLayout(export_layout)
        
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
        """)
        
        self.setMinimumSize(700, 600)
    
    def start_recording(self):
        """Start recording session"""
        self.recording = True
        
        # Create session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_dir = os.path.join(self.output_dir, f"session_{timestamp}")
        os.makedirs(self.current_session_dir, exist_ok=True)
        
        # Update UI
        self.status_label.setText("🔴 Recording... Press F9 to capture")
        self.status_label.setStyleSheet("font-size: 13px; padding: 8px; background-color: #4a2020; border-radius: 5px; color: #ff6b6b;")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_capture.setEnabled(True)
        
        print("Recording started - Press F9 to capture steps")
    
    def stop_recording(self):
        """Stop recording session"""
        self.recording = False
        
        # Update UI
        self.status_label.setText("⚪ Recording stopped")
        self.status_label.setStyleSheet("font-size: 13px; padding: 8px; background-color: #3d3d3d; border-radius: 5px;")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_capture.setEnabled(False)
        self.btn_export.setEnabled(True)
        
        print("Recording stopped")
    
    def capture_step(self):
        """Capture current screen state"""
        if not self.recording:
            return
        
        try:
            # Hide this window before capturing (so it doesn't appear in screenshot)
            self.hide()
            QTimer.singleShot(200, self._do_capture)  # Wait 200ms for window to hide
            
        except Exception as e:
            print(f"Error capturing step: {e}")
            self.show()  # Make sure to show window again

    def _do_capture(self):
        """Actually perform the capture after window is hidden"""
        try:
            # Get active window
            try:
                active_window = gw.getActiveWindow()
                window_title = active_window.title if active_window else "Unknown"
            except:
                window_title = "Unknown"
            
            # Take screenshot
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[1])  # Primary monitor
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                
                # Save screenshot
                screenshot_path = os.path.join(self.current_session_dir, 
                                              f"step_{len(self.steps)+1}.png")
                img.save(screenshot_path)
            
            # Create step data
            step_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'window': window_title,
                'screenshot': screenshot_path,
                'actions': []
            }
            
            self.steps.append(step_data)
            
            # Add to UI
            step_widget = StepItem(step_data, len(self.steps))
            self.steps_layout.addWidget(step_widget)
            
            # Update counter
            self.steps_counter.setText(f"Steps captured: {len(self.steps)}")
            
            print(f"Step {len(self.steps)} captured: {window_title}")
            
            # Show window again
            self.show()
            
        except Exception as e:
            print(f"Error in _do_capture: {e}")
            self.show()
       
    def clear_steps(self):
        """Clear all captured steps"""
        # Clear UI
        while self.steps_layout.count():
            child = self.steps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear data
        self.steps = []
        self.steps_counter.setText("Steps captured: 0")
        self.btn_export.setEnabled(False)
        
        print("All steps cleared")
    
    def export_report(self):
        """Generate HTML report with LLM summary"""
        if not self.steps:
            print("No steps to export")
            return
        
        print("Generating report with LLM summary...")
        
        # Generate summary using Ollama
        summary = self.generate_llm_summary()
        
        # Create HTML report
        html_path = os.path.join(self.current_session_dir, "report.html")
        self.create_html_report(html_path, summary)
        
        # Save JSON data
        json_path = os.path.join(self.current_session_dir, "steps_data.json")
        with open(json_path, 'w') as f:
            json.dump(self.steps, f, indent=2)
        
        print(f"Report exported to: {html_path}")
        
        # Open the report
        os.startfile(html_path)
        
        # Clear steps after export
        self.clear_steps()
        
    def generate_llm_summary(self):
        """Generate summary using Ollama"""
        try:
            # Prepare prompt
            steps_text = "\n".join([
                f"Step {i+1} ({step['timestamp']}): {step['window']}"
                for i, step in enumerate(self.steps)
            ])
            
            prompt = f"""Analyze these recorded steps and provide:
1. A brief summary of what was accomplished
2. A checklist of the main actions taken

Recorded Steps:
{steps_text}

Please format your response as:
SUMMARY: [brief summary]
CHECKLIST:
- [action 1]
- [action 2]
etc."""
            
            # Call Ollama API
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30)
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                return "Could not generate summary"
                
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Error generating summary"
    
    def create_html_report(self, path, summary):
        """Create HTML report file"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Steps Recording Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2b2b2b; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .step {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .step-number {{ font-weight: bold; color: #2b2b2b; font-size: 18px; }}
        .timestamp {{ color: #666; font-size: 12px; }}
        .screenshot {{ max-width: 100%; border: 1px solid #ddd; margin-top: 10px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 Steps Recording Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Total Steps: {len(self.steps)}</p>
    </div>
    
    <div class="summary">
        <h2>🤖 AI-Generated Summary</h2>
        <pre>{summary}</pre>
    </div>
    
    <h2>Detailed Steps</h2>
"""
        
        # Add each step
        for i, step in enumerate(self.steps):
            html += f"""
    <div class="step">
        <div class="step-number">Step {i+1}</div>
        <div class="timestamp">{step['timestamp']}</div>
        <p><strong>Window:</strong> {step['window']}</p>
        <img src="{os.path.basename(step['screenshot'])}" class="screenshot" />
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)