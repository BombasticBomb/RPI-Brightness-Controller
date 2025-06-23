import sys
import subprocess
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QSlider, QVBoxLayout, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class BrightnessControl(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brightness Control")
        self.setFixedSize(360, 230)

        self.set_gradient_theme()

        # Fonts
        label_font = QFont("Arial", 11, QFont.Weight.Bold)

        # Display selector label
        self.select_label = QLabel("Select Display:")
        self.select_label.setFont(label_font)
        self.select_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.select_label.setStyleSheet("""
            color: white;
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #006400, stop:1 #f0e130
            );
            padding: 4px;
            border-radius: 6px;
        """)

        # Display dropdown
        self.display_select = QComboBox()
        self.display_select.setFont(label_font)
        self.display_select.setStyleSheet("""
            color: white;
            background-color: #1c2a3a;
            padding: 4px;
            border: 1px solid #5f5f5f;
            border-radius: 4px;
        """)
        self.display_select.currentIndexChanged.connect(self.on_display_change)

        # Brightness label
        self.label = QLabel("Brightness: --")
        self.label.setFont(label_font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            color: white;
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #006400, stop:1 #f0e130
            );
            padding: 6px;
            border-radius: 6px;
        """)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(5)
        self.slider.setFixedHeight(30)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 10px;
                background: #006400;
                margin: 2px 0;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #cc0000;
                border: 1px solid #cc0000;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        self.last_value = -1

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self.select_label)
        layout.addWidget(self.display_select)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        self.setLayout(layout)

        # Detect displays
        self.displays = self.detect_displays()
        if self.displays:
            for name, bus in self.displays:
                self.display_select.addItem(name)
                self.display_select.setItemData(self.display_select.count() - 1, f"Bus {bus}", Qt.ItemDataRole.ToolTipRole)
            self.bus = self.displays[0][1]
            self.init_brightness()
        else:
            self.bus = None
            self.label.setText("No displays detected")
            self.slider.setEnabled(False)
            self.display_select.setEnabled(False)

        # 10ms polling
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_slider)
        self.timer.start(10)

    def set_gradient_theme(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e3c72,
                    stop:0.5 #2a5298,
                    stop:1 #1c2b5a
                );
            }
        """)

    def detect_displays(self):
        try:
            result = subprocess.run(
                ["ddcutil", "detect"],
                capture_output=True, text=True, check=True
            )
            displays = []
            blocks = result.stdout.strip().split("Display ")
            for block in blocks[1:]:
                bus_match = re.search(r'I2C bus:\s+/dev/i2c-(\d+)', block)
                drm_match = re.search(r'DRM connector:\s+([^\n]+)', block)
                mfg = re.search(r'Mfg id:\s+(\w+)', block)
                model = re.search(r'Model:\s+([^\n]+)', block)

                if bus_match:
                    bus = bus_match.group(1)
                    connector = drm_match.group(1).strip() if drm_match else f"Bus {bus}"
                    hdmi_match = re.search(r'HDMI-A-(\d+)', connector)
                    connector_name = f"HDMI {hdmi_match.group(1)}" if hdmi_match else connector
                    label = f"{mfg.group(1) if mfg else 'Unknown'} {model.group(1).strip() if model else ''} ({connector_name})"
                    displays.append((label.strip(), bus))
            return displays
        except Exception as e:
            print(f"[ERROR] Detecting displays: {e}")
            return []

    def init_brightness(self):
        if not self.bus:
            return
        try:
            result = subprocess.run(
                ["ddcutil", f"--bus={self.bus}", "getvcp", "10"],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                if "current value" in line:
                    value = int(line.split("current value =")[1].split(",")[0].strip())
                    self.slider.setValue(value)
                    self.last_value = value
                    self.label.setText(f"Brightness: {value}")
                    return
            self.label.setText("DDC not supported")
            self.slider.setEnabled(False)
        except Exception as e:
            self.label.setText("DDC not supported")
            self.slider.setEnabled(False)
            print(f"[ERROR] {e}")

    def check_slider(self):
        if not self.bus:
            return
        value = self.slider.value()
        if value != self.last_value:
            self.last_value = value
            self.label.setText(f"Brightness: {value}")
            try:
                subprocess.run(
                    ["ddcutil", f"--bus={self.bus}", "setvcp", "10", str(value)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                self.label.setText("DDC not supported")
                self.slider.setEnabled(False)

    def on_display_change(self, index):
        if 0 <= index < len(self.displays):
            self.bus = self.displays[index][1]
            self.slider.setEnabled(True)
            self.init_brightness()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrightnessControl()
    window.show()
    sys.exit(app.exec())
