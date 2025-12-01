from PySide2.QtWidgets import QApplication
from window import Window

if __name__ == "__main__":
    app = QApplication([])
    w = Window()
    w.show()
    app.exec_()
