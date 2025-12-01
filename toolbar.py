# type: ignore
from PySide2.QtCore import Qt, QSize, QPoint
from PySide2.QtGui import QColor, QPainter, QPen, QIcon
from PySide2.QtWidgets import QPushButton, QFrame, QHBoxLayout, QMenu, QFileDialog
import os

from canva import Canva


def get_icon(path: str):
    base = os.path.dirname(os.path.abspath(__file__))
    full = os.path.join(base, "image", "toolbar", path)
    return QIcon(full)


class SizeButton(QPushButton):
    def __init__(self, canvas: Canva, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = canvas
        self.setFixedSize(52, 52)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = min(18, self.canvas.thickness / 2)
        pen = QPen(QColor(255, 255, 255), 3)

        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        cx = self.width() // 2
        cy = self.height() // 2
        p.drawEllipse(QPoint(cx, cy), r, r)


class ShapeButton(QPushButton):
    def __init__(self, canvas: Canva, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = canvas
        self.setFixedSize(52, 52)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(255, 255, 255), 3)
        p.setPen(pen)

        cx = self.width() // 2
        cy = self.height() // 2
        shape = self.canvas.shape

        if shape == "free":
            font = p.font()
            font.setFamily("Microsoft JhengHei")
            font.setPointSize(24)
            p.setFont(font)
            p.drawText(self.rect(), Qt.AlignCenter, "S")

        elif shape == "line":
            p.drawLine(cx - 12, cy - 12, cx + 12, cy + 12)

        elif shape == "rect":
            p.drawRect(cx - 12, cy - 12, 24, 24)


class ColorButton(QPushButton):
    def __init__(self, canvas: Canva, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = canvas
        self.setFixedSize(52, 52)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = self.canvas.pen_color.red()
        g = self.canvas.pen_color.green()
        b = self.canvas.pen_color.blue()

        pen = QPen(QColor(255, 255, 255), 3)
        p.setPen(pen)
        p.setBrush(QColor(r, g, b))

        size = 26
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        p.drawRect(x, y, size, size)


class Toolbar(QFrame):
    def __init__(self, parent, canvas: Canva, close_callback):
        super().__init__(parent)

        self.canvas = canvas
        self.close_callback = close_callback

        self.setFixedHeight(70)
        self.setStyleSheet(
            """
            QFrame { background-color: rgba(40,40,40,230); border-radius: 12px; }
            QPushButton { background-color: rgba(70,70,70,255); border-radius: 8px; }
            QPushButton:hover { background-color: rgba(95,95,95,255); }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        def icon_btn(path, scale=0.8):
            btn = QPushButton()
            btn.setFixedSize(52, 52)
            btn.setIcon(get_icon(path))
            btn.setIconSize(QSize(int(52 * scale), int(52 * scale)))
            layout.addWidget(btn)
            return btn

        btn_board = icon_btn("board.svg")
        btn_board.clicked.connect(parent.toggle_board)

        btn_pen = icon_btn(f"tools/{self.canvas.tool}.svg")
        pen_menu = QMenu(self)
        pen_menu.addAction("自由筆", lambda: self.select_pen("free"))
        pen_menu.addAction("螢光筆", lambda: self.select_pen("highlight"))
        btn_pen.setMenu(pen_menu)

        self.btn_size = SizeButton(canvas)
        layout.addWidget(self.btn_size)

        size_menu = QMenu(self)
        for s in [2, 4, 6, 8, 10, 12, 15, 20, 30]:
            size_menu.addAction(
                f"{s}px",
                lambda v=s: (self.set_thickness(v), self.btn_size.update()),
            )
        self.btn_size.setMenu(size_menu)

        self.btn_shape = ShapeButton(canvas)
        layout.addWidget(self.btn_shape)

        shape_menu = QMenu(self)
        shape_menu.addAction("自由筆", lambda: self.set_shape("free"))
        shape_menu.addAction("直線", lambda: self.set_shape("line"))
        shape_menu.addAction("矩形", lambda: self.set_shape("rect"))
        self.btn_shape.setMenu(shape_menu)

        self.btn_color = ColorButton(canvas)
        layout.addWidget(self.btn_color)

        color_menu = QMenu(self)
        colors = {
            "白": (255, 255, 255),
            "灰": (136, 136, 136),
            "紅": (255, 0, 0),
            "橙": (255, 136, 0),
            "黃": (255, 255, 0),
            "綠": (0, 255, 0),
            "藍": (0, 128, 255),
            "紫": (170, 85, 255),
        }
        for name, rgb in colors.items():
            color_menu.addAction(
                name,
                lambda c=rgb: (self.canvas.set_color_tuple(c), self.btn_color.update()),
            )
        self.btn_color.setMenu(color_menu)

        btn_save = icon_btn("save.svg")
        menu_save = QMenu(self)
        menu_save.addAction("Save with Background", self.save_background)
        menu_save.addAction("Save Transparent", self.save_transparent)
        btn_save.setMenu(menu_save)

        btn_undo = icon_btn("undo.svg")
        btn_undo.clicked.connect(canvas.undo)

        btn_redo = icon_btn("redo.svg")
        btn_redo.clicked.connect(canvas.redo)

        btn_clear = icon_btn("clear.svg")
        btn_clear.clicked.connect(canvas.clear)

        btn_close = icon_btn("close.svg")
        btn_close.clicked.connect(self.close_callback)

    def select_pen(self, mode):
        self.canvas.set_tool("pen")
        self.canvas.shape = "free"

        if mode == "free":
            self.canvas.thickness = 4

        elif mode == "highlight":
            self.canvas.thickness = 12
            c = self.canvas.pen_color
            self.canvas.pen_color = QColor(c.red(), c.green(), c.blue(), 120)

    def set_shape(self, shape):
        self.canvas.shape = shape
        self.canvas.set_tool("pen")
        self.btn_shape.update()

    def set_thickness(self, px):
        self.canvas.thickness = px
        self.canvas.update()

    def save_background(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save", "canvas.png", "PNG Files (*.png)"
        )
        if path:
            self.canvas.save_with_background(path)

    def save_transparent(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Transparent", "canvas.png", "PNG Files (*.png)"
        )
        if path:
            self.canvas.save_transparent(path)
