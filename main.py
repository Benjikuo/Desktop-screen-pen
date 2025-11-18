# main.py
import sys
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtCore import Qt

from canvas import Canvas
from toolbar import Toolbar


class WhiteboardWindow(QWidget):
    def __init__(self):
        super().__init__()

        # ----------- Window 樣式 -----------
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ----------- 建立 Canvas + Toolbar -----------
        self.canvas = Canvas(self)
        self.toolbar = Toolbar(self, self.canvas)

        # 先顯示，確保大小正確
        self.showFullScreen()

        # 手動 trigger 一次 layout
        self.position_ui()

    # ---------------------------------------------------------
    # 視窗調整時：Canvas 填滿、Toolbar 置中
    # ---------------------------------------------------------
    def resizeEvent(self, event):
        self.position_ui()

    def position_ui(self):
        # Canvas 全螢幕鋪滿
        self.canvas.setGeometry(self.rect())

        # Toolbar 寬度根據內容自動調整
        self.toolbar.adjustSize()
        tw = self.toolbar.width()

        # 置中上方 (y=10)
        self.toolbar.move((self.width() - tw) // 2, 10)

    # ---------------------------------------------------------
    # 關閉
    # ---------------------------------------------------------
    def closeEvent(self, event):
        QApplication.instance().quit()


# ---------------------------------------------------------
# 主程式
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = WhiteboardWindow()
    w.show()
    sys.exit(app.exec_())
