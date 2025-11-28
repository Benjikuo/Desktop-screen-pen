# type: ignore
from PySide2.QtCore import Qt, QRect, QPoint, QSize, QBuffer, QByteArray
from PySide2.QtGui import QColor, QPainter, QPen, QCursor, QKeySequence, QIcon, QPixmap
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QShortcut,
    QMenu,
    QFileDialog,
)
import math
import os


# 讀取 SVG icon
def get_icon(path: str):
    base = os.path.dirname(os.path.abspath(__file__))
    full = os.path.join(base, "image", "toolbar", path)
    return QIcon(full)


# 工具函式
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


# ==============================
#     Canvas（含 Undo/Redo）
# ==============================
class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.drawing_mode = True
        self.setCursor(Qt.CrossCursor)

        self.board_color = (0, 0, 0, 50)
        self.tool = "pen"
        self.thickness = 8
        self.shape = "free"
        self.pen_color = QColor(255, 255, 255)

        self.start_pos = None
        self.last_pos = None
        self.current_stroke = []

        self.history = []  # undo stack
        self.redo_stack = []  # redo stack

        self.eraser_pos = None
        self.setMouseTracking(True)

        self.size_popup_pos = None
        self.size_popup_value = None
        self.size_popup_timer = 0

    # ======================
    # Mouse Events
    # ======================
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.drawing_mode = not self.drawing_mode
            if not self.drawing_mode:
                self.setCursor(Qt.ArrowCursor)
                self.board_color = (0, 0, 0, 0)
            else:
                self.setCursor(Qt.CrossCursor)
                self.board_color = (0, 0, 0, 50)
            self.update()
            return

        if not self.drawing_mode:
            return

        pos = event.pos()

        if event.button() == Qt.LeftButton:

            if self.tool == "eraser":
                self.erase_at(pos)
                return

            self.start_pos = pos
            self.last_pos = pos
            self.current_stroke = [pos]

        if event.button() == Qt.MiddleButton:
            self.window().close()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self.eraser_pos = pos

        if not self.drawing_mode:
            self.update()
            return

        if self.tool == "eraser":
            if event.buttons() & Qt.LeftButton:
                self.erase_at(pos)
            self.update()
            return

        if not (event.buttons() & Qt.LeftButton):
            self.update()
            return

        if self.shape == "free":
            self.current_stroke.append(pos)
        else:
            self.last_pos = pos

        self.update()

    def mouseReleaseEvent(self, event):
        if not self.drawing_mode or event.button() != Qt.LeftButton:
            return

        if self.tool == "eraser":
            return

        # push to undo stack
        if self.shape == "free" and len(self.current_stroke) > 1:
            self.history.append(
                {
                    "type": "pen",
                    "points": self.current_stroke[:],
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )
            self.redo_stack.clear()

        elif self.shape == "line":
            self.history.append(
                {
                    "type": "line",
                    "start": self.start_pos,
                    "end": self.last_pos,
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )
            self.redo_stack.clear()

        elif self.shape == "rect":
            rect = QRect(self.start_pos, self.last_pos).normalized()
            self.history.append(
                {
                    "type": "rect",
                    "rect": rect,
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )
            self.redo_stack.clear()

        self.current_stroke = []
        self.start_pos = None
        self.last_pos = None
        self.update()

    # ======================
    # Drawing
    # ======================
    def draw_background(self, painter):
        r, g, b, a = self.board_color
        painter.fillRect(self.rect(), QColor(r, g, b, a))

    def draw_item(self, painter, item):
        pen = QPen(item["color"])
        pen.setWidth(item["width"])
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if item["type"] == "pen":
            pts = item["points"]
            for i in range(1, len(pts)):
                painter.drawLine(pts[i - 1], pts[i])

        elif item["type"] == "line":
            painter.drawLine(item["start"], item["end"])

        elif item["type"] == "rect":
            painter.drawRect(item["rect"])

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 背景
        self.draw_background(p)

        # 歷史筆畫
        for item in self.history:
            self.draw_item(p, item)

        # 預覽
        if self.drawing_mode and self.start_pos:
            preview = None

            if self.shape == "free" and len(self.current_stroke):
                preview = {
                    "type": "pen",
                    "points": self.current_stroke,
                    "color": self.pen_color,
                    "width": self.thickness,
                }

            elif self.shape == "line":
                preview = {
                    "type": "line",
                    "start": self.start_pos,
                    "end": self.last_pos,
                    "color": self.pen_color,
                    "width": self.thickness,
                }

            elif self.shape == "rect":
                rect = QRect(self.start_pos, self.last_pos).normalized()
                preview = {
                    "type": "rect",
                    "rect": rect,
                    "color": self.pen_color,
                    "width": self.thickness,
                }

            if preview:
                self.draw_item(p, preview)

        # 橡皮擦圈圈
        if self.tool == "eraser" and self.eraser_pos:
            pen = QPen(QColor(255, 120, 0))
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            r = self.thickness / 2
            p.drawEllipse(self.eraser_pos, r, r)

        # popup
        if self.size_popup_value is not None:
            pen = QPen(QColor(255, 200, 80))
            pen.setWidth(2)
            p.setPen(pen)
            r = self.size_popup_value / 2
            p.drawEllipse(self.size_popup_pos, r, r)
            p.drawText(
                self.size_popup_pos + QPoint(20, -20), f"{self.size_popup_value}px"
            )

        if self.size_popup_timer > 0:
            self.size_popup_timer -= 1
        else:
            self.size_popup_value = None
            self.size_popup_pos = None

        # 邊框
        if self.drawing_mode:
            pen = QPen(QColor(255, 120, 0))
            pen.setWidth(2)
            p.setPen(pen)
            p.drawRect(self.rect())

    # ======================
    # Tool / Undo / Redo
    # ======================
    def set_tool(self, tool):
        self.tool = tool
        if tool == "eraser":
            self.setCursor(Qt.BlankCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def set_color_tuple(self, rgb):
        r, g, b = rgb
        self.pen_color = QColor(r, g, b)
        self.update()

    def undo(self):
        if not self.history:
            return
        item = self.history.pop()
        self.redo_stack.append(item)
        self.update()

    def redo(self):
        if not self.redo_stack:
            return
        item = self.redo_stack.pop()
        self.history.append(item)
        self.update()

    def clear(self):
        if self.history:
            # 清空也要可 undo → push whole canvas snapshot
            self.redo_stack.clear()
            self.history.append({"type": "clear_marker"})
            self.history.clear()
        self.update()

    # ======================
    # Save Functions
    # ======================
    def save_with_background(self, path):
        pix = self.grab()
        pix.save(path, "PNG")

    def save_transparent(self, path):
        # 暫時把背景透明化
        old = self.board_color
        self.board_color = (0, 0, 0, 0)

        pix = self.grab()
        pix.save(path, "PNG")

        self.board_color = old
        self.update()


# ==============================
# 自繪按鈕：Size / Shape / Color
# ==============================


class SizeButton(QPushButton):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = canvas
        self.setFixedSize(52, 52)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 白色筆圈大小依 thickness
        r = min(18, self.canvas.thickness * 1.3)

        pen = QPen(QColor(255, 255, 255), 3)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        cx = self.width() // 2
        cy = self.height() // 2

        p.drawEllipse(QPoint(cx, cy), r, r)


class ShapeButton(QPushButton):
    def __init__(self, canvas, *args, **kwargs):
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
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QPoint(cx, cy), 5, 5)

        elif shape == "line":
            p.drawLine(cx - 12, cy - 12, cx + 12, cy + 12)

        elif shape == "rect":
            p.drawRect(cx - 12, cy - 12, 24, 24)


class ColorButton(QPushButton):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = canvas
        self.setFixedSize(52, 52)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 畫白色邊框 + 畫筆顏色方塊
        r, g, b, a = (
            self.canvas.pen_color.red(),
            self.canvas.pen_color.green(),
            self.canvas.pen_color.blue(),
            255,
        )

        pen = QPen(QColor(255, 255, 255), 3)
        p.setPen(pen)
        p.setBrush(QColor(r, g, b))

        size = 26
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2

        p.drawRect(x, y, size, size)


# ==============================
#          Toolbar
# ==============================
class Toolbar(QFrame):
    def __init__(self, parent, canvas, close_callback):
        super().__init__(parent)
        self.canvas = canvas
        self.close_callback = close_callback

        self.setFixedHeight(70)

        self.setStyleSheet(
            """
            QFrame {
                background-color: rgba(40,40,40,230);
                border-radius: 12px;
            }
            QPushButton {
                background-color: rgba(70,70,70,255);
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(95,95,95,255);
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 工具建立器
        def icon_btn(path, scale=0.8):
            btn = QPushButton()
            btn.setFixedSize(52, 52)
            btn.setIcon(get_icon(path))
            btn.setIconSize(QSize(int(52 * scale), int(52 * scale)))
            layout.addWidget(btn)
            return btn

        # ======================
        # A 版 Toolbar 排列開始
        # ======================

        # 1. Board
        btn_board = icon_btn("board.svg")
        btn_board.clicked.connect(parent.toggle_board)

        # 2. Pen
        btn_pen = icon_btn("tools/pen.svg")
        btn_pen.clicked.connect(lambda: self.set_pen())

        # 3. Size（自繪）
        self.btn_size = SizeButton(canvas)
        layout.addWidget(self.btn_size)

        size_menu = QMenu(self)
        for s in [2, 4, 6, 8, 10, 12, 15, 20, 30]:
            size_menu.addAction(
                f"{s}px",
                lambda _, v=s: (
                    setattr(canvas, "thickness", v),
                    canvas.update(),
                    self.btn_size.update(),
                ),
            )
        self.btn_size.setMenu(size_menu)

        # 4. Shape（自繪）
        self.btn_shape = ShapeButton(canvas)
        layout.addWidget(self.btn_shape)

        shape_menu = QMenu(self)
        shape_menu.addAction("自由筆", lambda: self.set_shape("free"))
        shape_menu.addAction("直線", lambda: self.set_shape("line"))
        shape_menu.addAction("矩形", lambda: self.set_shape("rect"))
        self.btn_shape.setMenu(shape_menu)

        # 5. Color（自繪）
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
                lambda _, c=rgb: (canvas.set_color_tuple(c), self.btn_color.update()),
            )
        self.btn_color.setMenu(color_menu)

        # 6. Save ▼
        btn_save = icon_btn("save.svg")
        menu_save = QMenu(self)
        menu_save.addAction("Save with Background", self.save_background)
        menu_save.addAction("Save Transparent", self.save_transparent)
        btn_save.setMenu(menu_save)

        # 7. Undo
        btn_undo = icon_btn("undo.svg")
        btn_undo.clicked.connect(canvas.undo)

        # 8. Redo
        btn_redo = icon_btn("redo.svg")
        btn_redo.clicked.connect(canvas.redo)

        # 9. Clear
        btn_clear = icon_btn("clear.svg")
        btn_clear.clicked.connect(canvas.clear)

        # 10. Close
        btn_close = icon_btn("close.svg")
        btn_close.clicked.connect(self.close_callback)

    # ======================
    # Toolbar functions
    # ======================
    def set_pen(self):
        self.canvas.set_tool("pen")
        self.canvas.shape = "free"
        self.btn_shape.update()

    def set_shape(self, shape):
        self.canvas.shape = shape
        self.canvas.set_tool("pen")
        self.btn_shape.update()

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


# ==============================
#          Window
# ==============================
class Window(QWidget):
    def __init__(self):
        super().__init__()

        # 透明、置頂、無框
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 主要畫布
        self.canvas = Canvas(self)

        # 工具列
        self.toolbar = Toolbar(self, self.canvas, self.closeEvent)
        self.toolbar.raise_()

        self.build_shortcuts()
        self.showFullScreen()

    # ======================
    # 滑鼠滾輪：改大小
    # ======================
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        change = 2

        if delta > 0:
            self.canvas.thickness = min(50, self.canvas.thickness + change)
        else:
            self.canvas.thickness = max(2, self.canvas.thickness - change)

        # 更新自繪按鈕
        self.toolbar.btn_size.update()

        # 彈出大小圈
        pos = self.mapFromGlobal(QCursor.pos())
        self.canvas.show_size_popup(pos, self.canvas.thickness)
        self.canvas.update()

    # ======================
    # 背景切換
    # ======================
    def toggle_board(self):
        # 半透明 ↔ 全黑 ↔ 全透明
        if self.canvas.board_color == (0, 0, 0, 50):
            self.canvas.board_color = (0, 0, 0, 255)
        elif self.canvas.board_color == (0, 0, 0, 255):
            self.canvas.board_color = (0, 0, 0, 0)
        else:
            self.canvas.board_color = (0, 0, 0, 50)

        # 回復游標
        if self.canvas.tool == "eraser":
            self.canvas.setCursor(Qt.BlankCursor)
        else:
            self.canvas.setCursor(Qt.CrossCursor)

        self.canvas.update()

    # ======================
    # 調整 toolbar 位置
    # ======================
    def resizeEvent(self, event):
        self.canvas.setGeometry(self.rect())

        self.toolbar.adjustSize()
        tw = self.toolbar.width()
        self.toolbar.move((self.width() - tw) // 2, 10)

    # ======================
    # 快捷鍵
    # ======================
    def build_shortcuts(self):
        def sc(key, func):
            QShortcut(QKeySequence(key), self, activated=func)

        # 顏色循環（白→紅→綠→藍…）
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

        # ===== 快捷鍵 =====
        sc("C", next_color)
        sc("Z", self.canvas.undo)
        sc("X", self.canvas.clear)
        sc("Shift+Z", self.canvas.redo)
        sc("E", lambda: self.canvas.set_tool("eraser"))
        sc("F", lambda: self.canvas.set_tool("pen"))
        sc("W", self.toggle_board)
        sc("Esc", self.closeEvent)

    def closeEvent(self, event=None):
        QApplication.instance().quit()


# ==============================
#              main
# ==============================
if __name__ == "__main__":
    app = QApplication([])
    w = Window()
    w.show()
    app.exec_()
