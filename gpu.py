# type: ignore
import math
from PySide2.QtCore import Qt, QPoint
from PySide2.QtGui import QCursor, QKeySequence
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QPushButton,
    QHBoxLayout,
    QShortcut,
    QMenu,
)
from PySide2.QtOpenGL import QGLWidget
from OpenGL.GL import *


# ===================== Utils =====================


def dist(a, b):
    return math.hypot(a.x() - b.x(), a.y() - b.y())


def rgba(r, g, b, a=255):
    return (r / 255, g / 255, b / 255, a / 255)


# ===================== GPU Canvas =====================


class Canvas(QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # tool
        self.tool = "pen"
        self.pen_size = 6
        self.highlight_mode = False
        self.pen_color = rgba(255, 255, 255)

        # states
        self.history = []
        self.current_stroke = []
        self.drawing_mode = True
        self.board_color = (0, 0, 0, 0.15)

        self.last_pos = None
        self.start_pos = None

        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    # ---------- GPU init ----------
    def initializeGL(self):
        glClearColor(0, 0, 0, 0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        print("===== GPU Backend =====")
        print("Renderer:", glGetString(GL_RENDERER))
        print("Vendor:", glGetString(GL_VENDOR))
        print("Version:", glGetString(GL_VERSION))

    # ---------- GPU draw ----------
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # 背景
        glColor4f(*self.board_color)
        glBegin(GL_QUADS)
        glVertex2f(-1, -1)
        glVertex2f(1, -1)
        glVertex2f(1, 1)
        glVertex2f(-1, 1)
        glEnd()

        # 歷史筆畫
        for stroke in self.history:
            self.draw_stroke(stroke)

        # 預覽筆畫
        if self.current_stroke:
            self.draw_stroke(
                {
                    "color": self.pen_color,
                    "width": self.pen_size,
                    "points": self.current_stroke,
                }
            )

        # 橡皮擦圈
        if self.tool == "eraser" and self.last_pos:
            glColor4f(1, 0.5, 0, 1)
            glLineWidth(2)
            self.draw_circle(self.last_pos, self.pen_size / 2)

    # ---------- Draw GPU line ----------
    def draw_stroke(self, stroke):
        glColor4f(*stroke["color"])
        glLineWidth(stroke["width"])

        glBegin(GL_LINE_STRIP)
        for p in stroke["points"]:
            x = (p.x() / self.width()) * 2 - 1
            y = 1 - (p.y() / self.height()) * 2
            glVertex2f(x, y)
        glEnd()

    # ---------- Draw circle ----------
    def draw_circle(self, pos, r):
        cx = (pos.x() / self.width()) * 2 - 1
        cy = 1 - (pos.y() / self.height()) * 2

        glBegin(GL_LINE_LOOP)
        for i in range(32):
            th = (i / 32) * math.pi * 2
            glVertex2f(
                cx + math.cos(th) * r / self.width() * 2,
                cy + math.sin(th) * r / self.height() * 2,
            )
        glEnd()

    # ---------- Mouse ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.drawing_mode = not self.drawing_mode
            return

        if e.button() == Qt.LeftButton:
            if self.tool == "eraser":
                self.erase_at(e.pos())
                return

            self.current_stroke = [e.pos()]
            self.last_pos = e.pos()

    def mouseMoveEvent(self, e):
        self.last_pos = e.pos()

        if self.tool == "eraser":
            if e.buttons() & Qt.LeftButton:
                self.erase_at(e.pos())
            self.update()
            return

        if e.buttons() & Qt.LeftButton and self.tool == "pen":
            self.current_stroke.append(e.pos())
            self.update()

    def mouseReleaseEvent(self, e):
        if self.current_stroke:
            self.history.append(
                {
                    "color": self.pen_color,
                    "width": self.pen_size,
                    "points": list(self.current_stroke),
                }
            )
            self.current_stroke = []
            self.update()

    # ---------- Eraser ----------
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
        self.update()

    # ---------- API ----------
    def undo(self):
        if self.history:
            self.history.pop()
            self.update()

    def clear(self):
        self.history = []
        self.update()

    def set_tool(self, t):
        self.tool = t
        self.setCursor(Qt.BlankCursor if t == "eraser" else Qt.CrossCursor)

    def set_color_tuple(self, rgb):
        r, g, b = rgb
        a = 0.2 if self.highlight_mode else 1.0
        self.pen_color = (r / 255, g / 255, b / 255, a)
        self.update()


# ===================== Toolbar =====================


class Toolbar(QFrame):
    def __init__(self, parent, canvas, close_fn):
        super().__init__(parent)
        self.canvas = canvas

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        def btn(icon, w=40):
            b = QPushButton(icon)
            b.setFixedSize(w, 40)
            layout.addWidget(b)
            return b

        # 黑板
        b = btn("📘")
        b.clicked.connect(parent.toggle_board)

        # 橡皮擦
        e = btn("🧽")
        menu_e = QMenu(self)
        menu_e.addAction("橡皮擦", lambda _,: canvas.set_tool("eraser"))
        e.setMenu(menu_e)

        # 筆刷
        br = btn("✏️")
        menu_b = QMenu(self)
        menu_b.addAction(
            "普通筆",
            lambda _,: (
                canvas.set_tool("pen"),
                setattr(canvas, "highlight_mode", False),
                setattr(canvas, "pen_size", 6),
                canvas.set_color_tuple((255, 255, 255)),
            ),
        )
        menu_b.addAction(
            "螢光筆",
            lambda _,: (
                canvas.set_tool("pen"),
                setattr(canvas, "highlight_mode", True),
                setattr(canvas, "pen_size", 20),
                canvas.set_color_tuple((255, 255, 0)),
            ),
        )
        br.setMenu(menu_b)

        # 顏色
        c = btn("🎨")
        menu_c = QMenu(self)
        colors = {
            "白": (255, 255, 255),
            "紅": (255, 0, 0),
            "黃": (255, 255, 0),
            "綠": (0, 255, 0),
            "藍": (0, 128, 255),
        }
        for name, rgb in colors.items():
            menu_c.addAction(name, lambda _, c=rgb: canvas.set_color_tuple(c))
        c.setMenu(menu_c)

        # Undo
        u = btn("↩")
        u.clicked.connect(canvas.undo)

        # Clear
        cl = btn("🧹")
        cl.clicked.connect(canvas.clear)

        # Close
        x = btn("❌")
        x.clicked.connect(close_fn)


# ===================== Main Window =====================


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.canvas = Canvas(self)
        self.toolbar = Toolbar(self, self.canvas, self.closeEvent)
        self.toolbar.raise_()

        self.showFullScreen()
        self.build_shortcuts()

    def resizeEvent(self, e):
        self.canvas.setGeometry(self.rect())
        self.toolbar.adjustSize()
        self.toolbar.move((self.width() - self.toolbar.width()) // 2, 10)

    def toggle_board(self):
        if self.canvas.board_color[3] < 0.5:
            self.canvas.board_color = (0, 0, 0, 0.75)
        else:
            self.canvas.board_color = (0, 0, 0, 0.15)
        self.canvas.update()

    def build_shortcuts(self):

        def sc(k, fn):
            QShortcut(QKeySequence(f"Ctrl+{k}"), self, activated=fn)

        sc("Z", self.canvas.undo)
        sc("X", self.canvas.clear)
        sc("F", lambda: self.canvas.set_tool("pen"))
        sc("E", lambda: self.canvas.set_tool("eraser"))
        sc("W", self.toggle_board)
        sc("R", self.closeEvent)

    def closeEvent(self, e=None):
        QApplication.instance().quit()


# ===================== Main =====================

if __name__ == "__main__":
    app = QApplication([])
    w = Window()
    w.show()
    app.exec_()
