# type: ignore
import math
from PySide2.QtCore import Qt, QRect, QPoint
from PySide2.QtGui import QColor, QCursor, QKeySequence
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QShortcut,
    QMenu,
)
from PySide2.QtOpenGL import QGLWidget

from OpenGL.GL import *
from OpenGL.GLU import *


# ====================== 工具函式 ======================


def make_color(r, g, b, a=255):
    return (r / 255, g / 255, b / 255, a / 255)


def dist(a, b):
    return math.hypot(a.x() - b.x(), a.y() - b.y())


# ====================== GPU Canvas ======================


class Canvas(QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tool = "pen"
        self.pen_size = 6
        self.pen_color = make_color(1, 1, 1, 1)

        self.highlight_mode = False

        self.history = []  # GPU strokes
        self.current_stroke = []

        self.start_pos = None
        self.last_pos = None
        self.drawing_mode = True

        self.board_color = (0, 0, 0, 0.20)

        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    # ========== OpenGL 初始化 ==========
    def initializeGL(self):
        glClearColor(0, 0, 0, 0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # ========== OpenGL 繪製 ==========
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # 畫背景
        glColor4f(*self.board_color)
        glBegin(GL_QUADS)
        glVertex2f(-1, -1)
        glVertex2f(1, -1)
        glVertex2f(1, 1)
        glVertex2f(-1, 1)
        glEnd()

        # 畫歷史筆畫
        for stroke in self.history:
            self.draw_gl_stroke(stroke)

        # 畫預覽筆畫
        if self.current_stroke:
            self.draw_gl_stroke(
                {
                    "color": self.pen_color,
                    "width": self.pen_size,
                    "points": self.current_stroke,
                }
            )

        # 橡皮擦指示圈
        if self.tool == "eraser" and self.last_pos:
            glColor4f(1, 0.5, 0, 1)
            glLineWidth(2)
            self.draw_circle(self.last_pos, self.pen_size / 2)

    # ========== 工具繪圖（OpenGL） ==========
    def draw_gl_stroke(self, stroke):
        glColor4f(*stroke["color"])
        glLineWidth(stroke["width"])
        glBegin(GL_LINE_STRIP)
        for p in stroke["points"]:
            x = (p.x() / self.width()) * 2 - 1
            y = 1 - (p.y() / self.height()) * 2
            glVertex2f(x, y)
        glEnd()

    def draw_circle(self, pos, r):
        cx = (pos.x() / self.width()) * 2 - 1
        cy = 1 - (pos.y() / self.height()) * 2
        glBegin(GL_LINE_LOOP)
        for i in range(32):
            th = i * math.pi * 2 / 32
            glVertex2f(
                cx + math.cos(th) * r / self.width() * 2,
                cy + math.sin(th) * r / self.height() * 2,
            )
        glEnd()

    # ========== 滑鼠事件 ==========
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.drawing_mode = not self.drawing_mode
            self.update()
            return

        if not self.drawing_mode:
            return

        if event.button() == Qt.LeftButton:
            pos = event.pos()

            if self.tool == "eraser":
                self.erase_at(pos)
                return

            self.current_stroke = [pos]
            self.start_pos = pos
            self.last_pos = pos

    def mouseMoveEvent(self, event):
        self.last_pos = event.pos()

        if not self.drawing_mode:
            self.update()
            return

        if self.tool == "eraser":
            if event.buttons() & Qt.LeftButton:
                self.erase_at(event.pos())
            self.update()
            return

        if event.buttons() & Qt.LeftButton:
            if self.tool == "pen":
                self.current_stroke.append(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.tool == "eraser":
            return

        if self.current_stroke:
            self.history.append(
                {
                    "type": "pen",
                    "color": self.pen_color,
                    "width": self.pen_size,
                    "points": list(self.current_stroke),
                }
            )

        self.current_stroke = []
        self.update()

    # ========== 橡皮擦（整筆刪除） ==========
    def erase_at(self, pos):
        r = self.pen_size
        new = []
        for stroke in self.history:
            remove = False
            for p in stroke["points"]:
                if dist(p, pos) <= r:
                    remove = True
                    break
            if not remove:
                new.append(stroke)
        self.history = new

    # ========== 外部 API ==========
    def set_tool(self, t):
        self.tool = t
        if t == "eraser":
            self.setCursor(Qt.BlankCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def clear(self):
        self.history = []
        self.update()

    def undo(self):
        if self.history:
            self.history.pop()
            self.update()

    def set_color_tuple(self, rgb):
        r, g, b = rgb
        a = 0.20 if self.highlight_mode else 1.0
        self.pen_color = make_color(r, g, b, a)
        self.update()


# ====================== Toolbar ======================


class Toolbar(QFrame):
    def __init__(self, parent, canvas, close_callback):
        super().__init__(parent)
        self.canvas = canvas

        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        def btn(icon, w=40):
            b = QPushButton(icon)
            b.setFixedSize(w, 40)
            layout.addWidget(b)
            return b

        btn_board = btn("📘")
        btn_board.clicked.connect(parent.toggle_board)

        eraser = btn("🧽")
        menu_e = QMenu(self)
        menu_e.addAction("橡皮擦", lambda: canvas.set_tool("eraser"))
        eraser.setMenu(menu_e)

        brush = btn("✏️")
        menu_b = QMenu(self)
        menu_b.addAction(
            "普通筆",
            lambda: (
                canvas.set_tool("pen"),
                setattr(canvas, "highlight_mode", False),
                setattr(canvas, "pen_size", 6),
                canvas.set_color_tuple((255, 255, 255)),
            ),
        )
        menu_b.addAction(
            "螢光筆",
            lambda: (
                canvas.set_tool("pen"),
                setattr(canvas, "highlight_mode", True),
                setattr(canvas, "pen_size", 20),
                canvas.set_color_tuple((255, 255, 0)),
            ),
        )
        brush.setMenu(menu_b)

        shapes = btn("⬛")
        menu_s = QMenu(self)
        menu_s.addAction("自由筆", lambda: canvas.set_tool("pen"))
        shapes.setMenu(menu_s)

        sizebtn = btn("📏")
        menu_sz = QMenu(self)
        for s in [2, 4, 6, 10, 15, 20, 30]:
            menu_sz.addAction(f"{s}px", lambda _, v=s: setattr(canvas, "pen_size", v))
        sizebtn.setMenu(menu_sz)

        colorbtn = btn("🎨")
        menu_c = QMenu(self)
        colors = {
            "白": (255, 255, 255),
            "紅": (255, 0, 0),
            "黃": (255, 255, 0),
            "綠": (0, 255, 0),
            "藍": (0, 128, 255),
            "紫": (170, 85, 255),
        }
        for name, rgb in colors.items():
            menu_c.addAction(name, lambda _, c=rgb: canvas.set_color_tuple(c))
        colorbtn.setMenu(menu_c)

        undo = btn("↩")
        undo.clicked.connect(canvas.undo)

        clear = btn("🧹")
        clear.clicked.connect(canvas.clear)

        close = btn("❌")
        close.clicked.connect(close_callback)


# ====================== Window ======================


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.canvas = Canvas(self)
        self.toolbar = Toolbar(self, self.canvas, self.closeEvent)
        self.toolbar.raise_()

        self.build_shortcuts()
        self.showFullScreen()

    def toggle_board(self):
        if self.canvas.board_color == (0, 0, 0, 0.20):
            self.canvas.board_color = (0, 0, 0, 0.80)
        else:
            self.canvas.board_color = (0, 0, 0, 0.20)
        self.canvas.update()

    def resizeEvent(self, event):
        self.canvas.setGeometry(self.rect())
        self.toolbar.adjustSize()
        self.toolbar.move((self.width() - self.toolbar.width()) // 2, 10)

    def build_shortcuts(self):

        def sc(k, fn):
            QShortcut(QKeySequence(f"Ctrl+{k}"), self, activated=fn)

        sc("Z", self.canvas.undo)
        sc("X", self.canvas.clear)
        sc("W", self.toggle_board)
        sc("F", lambda: self.canvas.set_tool("pen"))
        sc("E", lambda: self.canvas.set_tool("eraser"))
        sc("R", self.closeEvent)

    def closeEvent(self, e=None):
        QApplication.instance().quit()


# ====================== Main ======================

if __name__ == "__main__":
    app = QApplication([])
    w = Window()
    w.show()
    app.exec_()
