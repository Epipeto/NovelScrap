import sys 
from PySide6.QtCore import Qt

from PySide6.QtWidgets import QApplication, QLabel

if __name__ == "__main__":
    app = QApplication (sys.argv)
    label = QLabel ("Hello world!", alignment=Qt.Alignment.AlignCenter)

    label.show()
    sys.exit(app.exec())
