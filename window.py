# type: ignore
from PySide2.QtCore import Qt
from PySide2.QtGui import QCursor, QKeySequence
from PySide2.QtWidgets import QWidget, QApplication, QShortcut

from canva import Canva
from toolbar import Toolbar


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.canvas = Canva(self)
        self.toolbar = Toolbar(self, self.canvas, self.closeEvent)
        self.toolbar.raise_()

        self.build_shortcuts()
        self.showFullScreen()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        change = 2

        if delta > 0:
            self.canvas.thickness = min(50, self.canvas.thickness + change)
        else:
            self.canvas.thickness = max(2, self.canvas.thickness - change)

        self.toolbar.btn_size.update()

        pos = self.mapFromGlobal(QCursor.pos())
        self.canvas.show_size_popup(pos, self.canvas.thickness)
        self.canvas.update()

    def toggle_board(self):
        self.canvas.drawing_mode = True

        if self.canvas.board_color != (0, 0, 0, 50):
            self.canvas.board_color = (0, 0, 0, 50)
        else:
            self.canvas.board_color = (0, 0, 0, 255)

        if self.canvas.tool == "eraser":
            self.canvas.setCursor(Qt.BlankCursor)
        else:
            self.canvas.setCursor(Qt.CrossCursor)

        self.canvas.update()

    def build_shortcuts(self):
        def shortcut(key, func):
            QShortcut(QKeySequence(key), self, activated=func)

        colors = [
            (255, 255, 255),
            (255, 0, 0),
            (255, 136, 0),
            (255, 255, 0),
            (0, 255, 0),
            (0, 128, 255),
            (170, 85, 255),
        ]

        self.color_index = 0

        def next_color():
            self.color_index = (self.color_index + 1) % len(colors)
            rgb = colors[self.color_index]
            self.canvas.set_color_tuple(rgb)
            self.toolbar.btn_color.update()

        shortcut("W", self.toggle_board)
        shortcut("E", lambda: self.canvas.set_tool("eraser"))
        shortcut("F", lambda: self.canvas.set_tool("pen"))
        shortcut("C", next_color)
        shortcut("Ctrl+Z", self.canvas.undo)
        shortcut("Ctrl+Y", self.canvas.redo)
        shortcut("Shift+Z", self.canvas.redo)
        shortcut("X", self.canvas.clear)
        shortcut("Ctrl+R", self.closeEvent)
        shortcut("Esc", self.closeEvent)

    def resizeEvent(self, event):
        self.canvas.setGeometry(self.rect())

        self.toolbar.adjustSize()
        tw = self.toolbar.width()
        self.toolbar.move((self.width() - tw) // 2, 10)

    def closeEvent(self, event=None):
        QApplication.instance().quit()
