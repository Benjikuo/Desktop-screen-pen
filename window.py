# window.py
# type: ignore

from PySide2.QtWidgets import QWidget, QApplication, QShortcut
from PySide2.QtGui import QCursor, QKeySequence
from PySide2.QtCore import Qt

from canva import Canva
from controller import Controller
from toolbar import Toolbar


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.canva = Canva(self)
        self.controller = Controller(self, self.canva)
        self.toolbar = Toolbar(self, self.controller)

        self.controller.toolbar = self.toolbar
        self.canva.toolbar = self.toolbar

        self.toolbar.raise_()
        self.showFullScreen()

        # shortcuts
        def shortcut(key, func):
            QShortcut(QKeySequence(key), self, activated=func)

        shortcut("1", lambda: self.controller.toggle_board())
        shortcut("2", lambda: self.controller.toggle_tool())
        shortcut("3", lambda: self.controller.toggle_size())
        shortcut("4", lambda: self.controller.toggle_shape())
        shortcut("5", lambda: self.controller.toggle_color())

        shortcut("6", lambda: self.controller.save())
        shortcut("7", lambda: self.controller.undo())
        shortcut("8", lambda: self.controller.redo())
        shortcut("9", lambda: self.controller.clear())
        shortcut("0", lambda: self.controller.quit())

        shortcut("W", lambda: self.controller.toggle_drawing_mode())
        shortcut("E", lambda: self.controller.toggle_eraser())
        shortcut("R", lambda: self.controller.toggle_pen())
        shortcut("Z", lambda: self.controller.toggle_tool())
        shortcut("X", lambda: self.controller.toggle_shape())
        shortcut("C", lambda: self.controller.toggle_color())

        shortcut("S", lambda: self.controller.save())
        shortcut("D", lambda: self.controller.undo())
        shortcut("F", lambda: self.controller.redo())
        shortcut("F", lambda: self.controller.clear())
        shortcut("Q", lambda: self.controller.quit())
        shortcut("Esc", lambda: self.controller.quit())
        shortcut("Ctrl+S", lambda: self.controller.save())
        shortcut("Ctrl+Z", lambda: self.controller.undo())
        shortcut("Ctrl+Y", lambda: self.controller.redo())
        shortcut("Ctrl+X", lambda: self.controller.clear())
        shortcut("Ctrl+R", lambda: self.controller.quit())

        shortcut("T", lambda: self.controller.set_pen(color="white"))
        shortcut("G", lambda: self.controller.set_pen(color="orange"))
        shortcut("B", lambda: self.controller.set_pen(color="blue"))
        shortcut(
            "V", lambda: self.controller.set_pen(size=2, shape="rect", color="red")
        )

        shortcut("Shift+W", lambda: self.controller.toggle_drawing_mode(reverse=True))
        shortcut("Shift+2", lambda: self.controller.toggle_tool(reverse=True))
        shortcut("Shift+3", lambda: self.controller.toggle_size(reverse=True))
        shortcut("Shift+4", lambda: self.controller.toggle_shape(reverse=True))
        shortcut("Shift+5", lambda: self.controller.toggle_color(reverse=True))
        shortcut("Shift+Z", lambda: self.controller.toggle_tool(reverse=True))
        shortcut("Shift+X", lambda: self.controller.toggle_shape(reverse=True))
        shortcut("Shift+C", lambda: self.controller.toggle_color(reverse=True))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        pos = self.mapFromGlobal(QCursor.pos())

        self.controller.adjust_size(delta, pos)

    def resizeEvent(self, event):
        self.canva.setGeometry(self.rect())
        self.toolbar.adjustSize()
        tw = self.toolbar.width()
        self.toolbar.move((self.width() - tw) // 2, 10)

    def closeEvent(self, event=None):
        QApplication.instance().quit()
