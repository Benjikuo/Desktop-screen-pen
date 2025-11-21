# type: ignore
from PySide2.QtCore import Qt, QRect, QPoint
from PySide2.QtGui import QColor, QPainter, QPen, QCursor, QKeySequence
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QShortcut,
    QMenu,
)
from PySide2.QtGui import QKeySequence
import math

HIGHLIGHT_ALPHA = 40  # 螢光筆透明度


def dist(a, b):
    return math.hypot(a.x() - b.x(), a.y() - b.y())


def line_hit(p, a, b, r):
    ax, ay = a.x(), a.y()
    bx, by = b.x(), b.y()
    px, py = p.x(), p.y()

    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab_len2 = abx * abx + aby * aby

    if ab_len2 == 0:
        return dist(p, a) <= r

    t = max(0, min(1, (apx * abx + apy * aby) / ab_len2))
    cx = ax + t * abx
    cy = ay + t * aby

    return math.hypot(px - cx, py - cy) <= r


def rect_hit(p, rect, r):
    x = max(rect.left(), min(p.x(), rect.right()))
    y = max(rect.top(), min(p.y(), rect.bottom()))
    return math.hypot(p.x() - x, p.y() - y) <= r


class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.drawing_mode = True
        self.setCursor(Qt.CrossCursor)

        # white / red / orange / yellow / green / blue / purple
        self.color_cycle = [
            (255, 255, 255),
            (255, 0, 0),
            (255, 136, 0),
            (255, 255, 0),
            (0, 255, 0),
            (0, 128, 255),
            (170, 85, 255),
        ]
        self.color_index = 0

        self.board_color = (0, 0, 0, 50)
        self.tool = "pen"
        self.settings = {
            "pen": {"size": 4, "shape": "free", "color": 1},
            "highlight": {"size": 10, "shape": "free", "color": 3},
            "eraser": {"size": 30, "shape": None, "color": None},
        }
        self.last_used_tool = {"tool": None, "size": None, "shape": None, "color": None}

        self.start_pos = None
        self.last_pos = None
        self.current_stroke = []
        self.history = []

        self.setMouseTracking(True)
        self.eraser_pos = None
        self.size_popup_pos = None
        self.size_popup_value = None
        self.size_popup_timer = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing_mode:
            pos = event.pos()
            self.start_pos = pos
            self.last_pos = pos
            self.current_stroke = [pos]

        elif event.button() == Qt.MiddleButton:
            self.window().close()

        elif event.button() == Qt.RightButton:
            self.toggle_board()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton or not self.drawing_mode:
            return

        pos = event.pos()

        if self.tool == "eraser":
            self.erase_at(pos)

        elif self.tool == "crop_eraser":
            self.erase_at(pos)

        else:
            if self.shape == "free":
                self.current_stroke.append(pos)
            elif self.shape in ("line", "rect"):
                self.last_pos = pos

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self.drawing_mode:
            return

        if self.tool == "pen" and len(self.current_stroke) > 1:
            self.history.append(
                {
                    "type": "pen",
                    "points": self.current_stroke[:],
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )

        elif self.tool == "line":
            self.history.append(
                {
                    "type": "line",
                    "start": self.start_pos,
                    "end": self.last_pos,
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )

        elif self.tool == "rect":
            rect = QRect(self.start_pos, self.last_pos).normalized()
            self.history.append(
                {
                    "type": "rect",
                    "rect": rect,
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )

        self.current_stroke = []
        self.start_pos = None
        self.last_pos = None
        self.update()

    def set_tool(self, tool):
        self.tool = tool

        # 橡皮擦隱藏游標
        if tool == "eraser":
            self.setCursor(Qt.BlankCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def set_thickness(self, size):
        self.thickness = size

    def set_shape(self, shape):
        self.shape = shape

    def set_color_tuple(self, rgb_tuple):
        r, g, b = rgb_tuple

        if self.tool == "highlight":

            a = HIGHLIGHT_ALPHA
        else:
            a = 255  # 一般筆

        self.pen_color = QColor(r, g, b, a)
        self.update()

    # ================= Tool Functions ===================

    def clear(self):
        self.history = []
        self.update()

    def undo(self):
        if self.history:
            self.history.pop()
            self.update()

    # =============== 橡皮擦（整筆刪除） ===============

    def erase_at(self, pos):
        r = self.thickness
        new_history = []

        for item in self.history:
            remove = False

            if item["type"] == "pen":
                for p in item["points"]:
                    if dist(pos, p) <= r:
                        remove = True
                        break

            elif item["type"] == "line":
                if line_hit(pos, item["start"], item["end"], r):
                    remove = True

            elif item["type"] == "rect":
                if rect_hit(pos, item["rect"], r):
                    remove = True

            if not remove:
                new_history.append(item)

        self.history = new_history
        self.update()

    # =============== 滾輪 popup ===============

    def show_size_popup(self, pos, size):
        self.size_popup_pos = pos
        self.size_popup_value = size
        self.size_popup_timer = 10
        self.update()

    # ================= Paint =========================

    def draw_item(self, painter, item):
        t = item["type"]
        pen = QPen(item["color"])
        pen.setWidth(item["width"])
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if t == "pen":
            pts = item["points"]
            for i in range(1, len(pts)):
                painter.drawLine(pts[i - 1], pts[i])

        elif t == "line":
            painter.drawLine(item["start"], item["end"])

        elif t == "rect":
            painter.drawRect(item["rect"])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r, g, b, a = self.board_color
        painter.fillRect(self.rect(), QColor(r, g, b, a))

        # 歷史筆畫
        for item in self.history:
            self.draw_item(painter, item)

        # 預覽
        if self.drawing_mode:
            if self.tool == "pen" and self.current_stroke:
                self.draw_item(
                    painter,
                    {
                        "type": "pen",
                        "points": self.current_stroke,
                        "color": self.pen_color,
                        "width": self.thickness,
                    },
                )

            elif self.tool == "line" and self.start_pos and self.last_pos:
                self.draw_item(
                    painter,
                    {
                        "type": "line",
                        "start": self.start_pos,
                        "end": self.last_pos,
                        "color": self.pen_color,
                        "width": self.thickness,
                    },
                )

            elif self.tool == "rect" and self.start_pos and self.last_pos:
                rect = QRect(self.start_pos, self.last_pos).normalized()
                self.draw_item(
                    painter,
                    {
                        "type": "rect",
                        "rect": rect,
                        "color": self.pen_color,
                        "width": self.thickness,
                    },
                )

        # 橡皮擦圈圈
        if self.tool == "eraser" and self.eraser_pos:
            pen = QPen(QColor(255, 120, 0, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            radius = self.thickness / 2
            painter.drawEllipse(self.eraser_pos, radius, radius)

        # 滾輪 popup
        if self.size_popup_value is not None:
            pen = QPen(QColor(255, 200, 80, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            radius = self.size_popup_value / 2
            painter.drawEllipse(self.size_popup_pos, radius, radius)
            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(
                self.size_popup_pos + QPoint(20, -20), f"{self.size_popup_value}px"
            )

        # popup timer
        if self.size_popup_timer > 0:
            self.size_popup_timer -= 1
        else:
            self.size_popup_value = None
            self.size_popup_pos = None

        # 外框
        if self.drawing_mode:
            pen = QPen(QColor(255, 120, 0, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self.rect())

    def toggle_board(self):
        self.drawing_mode = not self.drawing_mode
        self.setCursor(Qt.CrossCursor if self.drawing_mode else Qt.ArrowCursor)
        if not self.drawing_mode:
            self.board_color = (0, 0, 0, 0)
        else:
            self.board_color = (0, 0, 0, 50)
        self.update()

    def toggle_board(self):
        if self.canvas.board_color == (0, 0, 0, 50):
            self.canvas.board_color = (0, 0, 0, 255)
        else:
            self.canvas.board_color = (0, 0, 0, 50)

        self.canvas.drawing_mode = True

        if self.canvas.tool == "eraser":
            self.canvas.setCursor(Qt.BlankCursor)
        else:
            self.canvas.setCursor(Qt.CrossCursor)

        self.canvas.update()

    def shape_toggle(self):
        if self.canvas.tool != "pen":
            self.canvas.set_tool("pen")
        else:
            self.canvas.set_tool("highlight")
        if self.canvas.tool == "highlight":
            self.canvas.thickness = 20
        else:
            self.canvas.thickness = 6
        self.toolbar.size_label.setText(f"{self.canvas.thickness}px")
        self.canvas.set_color_tuple(self.color_cycle[self.color_index])

        self.canvas.update()

    def color_toggle(self):
        self.color_index = (self.color_index + 1) % len(self.color_cycle)
        self.canvas.set_color_tuple(self.color_cycle[self.color_index])
        self.canvas.set_tool("pen")
        # 更新 Toolbar 色塊
        r, g, b = self.color_cycle[self.color_index]
        self.toolbar.color_btn.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border-radius:6px;"
        )

    # =========================== Toolbar =============================


class Toolbar(QFrame):
    def __init__(self, parent, canvas):
        super().__init__(parent)
        self.canvas = canvas
        self.setFixedHeight(60)

        self.size_label = QPushButton()  # 只是 placeholder，避免報錯

        self.setStyleSheet(
            """
            QFrame {
                background-color: rgba(34,34,34,220);
                border-radius:10px;
            }
            QPushButton {
                color: white;
                font-family: 'Segoe UI Emoji';
                font-size: 22px;
                border: none;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,40);
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # -------------------------------------------------------
        # 工具按鈕生成（固定寬度，靠 emoji，無文字）
        # -------------------------------------------------------
        def add_btn(emoji, w=40):
            btn = QPushButton(emoji)
            btn.setFixedSize(w, 40)
            layout.addWidget(btn)
            return btn

        # -------------------------------------------------------
        # 📘 黑板（無下拉）
        # -------------------------------------------------------
        btn_board = add_btn("📘", 40)
        btn_board.clicked.connect(canvas.toggle_board)

        # -------------------------------------------------------
        # 🧽 橡皮擦 ▼
        # -------------------------------------------------------
        btn_eraser = add_btn("🧽", 60)
        eraser_menu = QMenu(self)

        eraser_menu.addAction(
            "圓形橡皮擦",
            lambda: (canvas.set_tool("eraser"),),
        )
        eraser_menu.addAction(
            "矩形橡皮擦",
            lambda: (canvas.set_tool("eraser"),),
        )
        btn_eraser.setMenu(eraser_menu)

        # -------------------------------------------------------
        # ✏️ 筆刷 ▼
        # -------------------------------------------------------
        btn_brush = add_btn("✏️ ▼", 60)
        brush_menu = QMenu(self)

        brush_menu.addAction(
            "普通筆",
            lambda: (
                canvas.set_tool("pen"),
                canvas.__setattr__("pen_size", 4),
                canvas.set_color_tuple((255, 255, 255)),
            ),
        )
        brush_menu.addAction(
            "螢光筆",
            lambda: (
                canvas.set_tool("pen"),
                canvas.__setattr__("pen_size", 20),
                canvas.set_color_tuple((255, 255, 0)),
            ),
        )
        btn_brush.setMenu(brush_menu)

        # -------------------------------------------------------
        # ⬛ 形狀 ▼
        # -------------------------------------------------------
        btn_shape = add_btn("⬛", 60)
        shape_menu = QMenu(self)

        shape_menu.addAction("自由筆", lambda: canvas.set_tool("pen"))
        shape_menu.addAction("直線", lambda: canvas.set_tool("line"))
        shape_menu.addAction("矩形", lambda: canvas.set_tool("rect"))

        btn_shape.setMenu(shape_menu)

        # -------------------------------------------------------
        # 📏 大小 ▼
        # -------------------------------------------------------
        btn_thickness = add_btn("📏", 60)
        size_menu = QMenu(self)

        for s in [2, 4, 6, 8, 10, 15, 20, 30]:
            size_menu.addAction(
                f"{s}px", lambda _, v=s: canvas.__setattr__("pen_size", v)
            )

        btn_thickness.setMenu(size_menu)

        # -------------------------------------------------------
        # 🎨 顏色 ▼
        # -------------------------------------------------------
        btn_color = add_btn("🎨", 60)
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
            color_menu.addAction(name, lambda _, c=rgb: canvas.set_color_tuple(c))

        btn_color.setMenu(color_menu)

        # -------------------------------------------------------
        # ↩ Undo
        # -------------------------------------------------------
        btn_undo = add_btn("↩", 40)
        btn_undo.clicked.connect(canvas.undo)

        # -------------------------------------------------------
        # 🧹 Clear
        # -------------------------------------------------------
        btn_clear = add_btn("🧹", 40)
        btn_clear.clicked.connect(canvas.clear)

        # -------------------------------------------------------
        # ❌ Close
        # -------------------------------------------------------
        btn_close = add_btn("❌", 40)
        btn_close.clicked.connect(self.window().close)


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.canvas = Canvas(self)
        self.toolbar = Toolbar(self, self.canvas)
        self.toolbar.raise_()

        self.build_shortcuts()
        self.showFullScreen()

    def build_shortcuts(self):

        def shortcut_func(key, func):
            QShortcut(QKeySequence(key), self, activated=func)

        shortcut_func("W", self.canvas.toggle_board)
        shortcut_func("E", self.canvas.toggle_eraser)
        shortcut_func("D", self.canvas.set_last)
        shortcut_func("R", self.canvas.set_rec)
        shortcut_func("F", self.canvas.set_pen)
        shortcut_func("V", self.canvas.set_high)
        shortcut_func("C", self.canvas.color_toggle)
        shortcut_func("S", self.canvas.shape_toggle)
        shortcut_func("X", self.canvas.clear)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        change = 2

        if delta > 0:
            self.canvas.thickness = min(50, self.canvas.thickness + change)
        else:
            self.canvas.thickness = max(2, self.canvas.thickness - change)

        self.toolbar.size_label.setStyleSheet("font-size: 20px; color: white;")
        self.toolbar.size_label.setText(f"{self.canvas.thickness}px")
        self.canvas.show_size_popup(
            self.mapFromGlobal(QCursor.pos()), self.canvas.thickness
        )

    def resizeEvent(self, event=None):
        self.canvas.setGeometry(self.rect())
        self.toolbar.adjustSize()
        self.toolbar.move((self.width() - self.toolbar.width()) // 2, 10)

    def closeEvent(self, evnet=None):
        QApplication.instance().quit()


if __name__ == "__main__":
    app = QApplication([])
    w = Window()
    w.show()
    app.exec_()
