import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox,
    QCheckBox, QGroupBox, QProgressBar, QTextEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
import pillow_heif

# ---------------- Worker Thread ----------------
class ConverterThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, input_folder, output_folder, delete_original):
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.delete_original = delete_original

    def run(self):
        files = [f for f in os.listdir(self.input_folder) if f.lower().endswith(".heic")]
        total = len(files)
        converted = 0

        for i, file in enumerate(files, start=1):
            heic_path = os.path.join(self.input_folder, file)
            jpg_name = file.rsplit(".", 1)[0] + ".jpg"
            jpg_path = os.path.join(self.output_folder, jpg_name)

            if os.path.exists(jpg_path):
                self.log.emit(f"Skipped {file}, JPG already exists.")
                continue

            try:
                heif_file = pillow_heif.read_heif(heic_path)
                image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
                image.save(jpg_path, "JPEG")
                converted += 1
                self.log.emit(f"Converted {file} → {jpg_name}")
                if self.delete_original:
                    os.remove(heic_path)
                    self.log.emit(f"Deleted {file}")
            except Exception as e:
                self.log.emit(f"Error converting {file}: {e}")

            self.progress.emit(int(i / total * 100))

        self.finished.emit(converted)

# ---------------- Main GUI ----------------
class HEICConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HEIC to JPG Converter")
        self.setMinimumWidth(1000)

        # Default folders
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.default_input = os.path.join(base_dir, "HEIC")
        self.default_output = os.path.join(base_dir, "JPG")
        os.makedirs(self.default_input, exist_ok=True)
        os.makedirs(self.default_output, exist_ok=True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = QLabel("HEIC → JPG Converter")
        title.setFont(QFont("Arial", 20))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Input folder
        input_group = QGroupBox("Input Folder (HEIC)")
        input_layout = QHBoxLayout()
        self.input_path = QLineEdit(self.default_input)
        browse_in = QPushButton("Browse")
        browse_in.clicked.connect(self.browse_input)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(browse_in)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        self.delete_checkbox = QCheckBox("Delete HEIC after conversion")
        layout.addWidget(self.delete_checkbox)

        # Output folder
        output_group = QGroupBox("Output Folder (JPG)")
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit(self.default_output)
        browse_out = QPushButton("Browse")
        browse_out.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(browse_out)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        self.open_checkbox = QCheckBox("Open output folder after conversion")
        layout.addWidget(self.open_checkbox)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.log_text)

        # Convert button
        convert_btn = QPushButton("Start Conversion")
        convert_btn.setFont(QFont("Arial", 14))
        convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(convert_btn)

        self.setLayout(layout)

    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_path.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path.setText(folder)

    def start_conversion(self):
        input_folder = self.input_path.text()
        output_folder = self.output_path.text()

        if not os.path.exists(input_folder):
            QMessageBox.warning(self, "Error", "Input folder does not exist.")
            return

        os.makedirs(output_folder, exist_ok=True)
        delete_original = self.delete_checkbox.isChecked()

        # Disable UI while processing
        self.setEnabled(False)
        self.log_text.clear()
        self.progress_bar.setValue(0)

        self.thread = ConverterThread(input_folder, output_folder, delete_original)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.log.connect(self.update_log)
        self.thread.finished.connect(self.conversion_finished)
        self.thread.start()

    def update_log(self, text):
        self.log_text.append(text)

    def conversion_finished(self, converted_count):
        QMessageBox.information(self, "Done", f"Conversion complete! {converted_count} files converted.")
        self.setEnabled(True)
        if self.open_checkbox.isChecked():
            os.system(f'open "{self.output_path.text()}"')  # macOS


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HEICConverterApp()
    window.show()
    sys.exit(app.exec_())
