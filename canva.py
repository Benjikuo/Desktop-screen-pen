# type: ignore
from PySide2.QtCore import Qt, QRect, QPoint
from PySide2.QtGui import QColor, QPainter, QPen
from PySide2.QtWidgets import QWidget
import math


def dist(a, b):
    return math.hypot(a.x() - b.x(), a.y() - b.y())


def line_hit(p, a, b, r):
    ax, ay = a.x(), a.y()
    bx, by = b.x(), b.y()
    px, py = p.x(), p.y()

    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab_len = abx * abx + aby * aby

    if ab_len == 0:
        return dist(p, a) <= r

    t = max(0, min(1, (apx * abx + apy * aby) / ab_len))
    cx = ax + t * abx
    cy = ay + t * aby

    return math.hypot(px - cx, py - cy) <= r


def rect_hit(p, rect, r):
    x = max(rect.left(), min(p.x(), rect.right()))
    y = max(rect.top(), min(p.y(), rect.bottom()))
    return math.hypot(p.x() - x, p.y() - y) <= r


class Canva(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.drawing_mode = True
        self.setCursor(Qt.CrossCursor)

        self.board_color = (0, 0, 0, 50)
        self.tool = "pen"
        self.shape = "free"
        self.thickness = 4
        self.pen_color = QColor(255, 255, 255)

        self.start_pos = None
        self.last_pos = None
        self.current_stroke = []

        self.history = []
        self.redo_stack = []

        self.eraser_pos = None
        self.setMouseTracking(True)

        self.size_popup_pos = None
        self.size_popup_value = None
        self.size_popup_timer = 0

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

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        self.draw_background(p)

        for item in self.history:
            self.draw_item(p, item)

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

        if self.tool == "eraser" and self.eraser_pos:
            pen = QPen(QColor(255, 120, 0))
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)

            r = self.thickness / 2
            p.drawEllipse(self.eraser_pos, r, r)

        if self.size_popup_value is not None:
            pen = QPen(QColor(255, 200, 80))
            pen.setWidth(2)
            p.setPen(pen)

            r = self.size_popup_value / 2
            p.drawEllipse(self.size_popup_pos, r, r)

            p.drawText(
                self.size_popup_pos + QPoint(20, -20),
                f"{self.size_popup_value}px",
            )

        if self.size_popup_timer > 0:
            self.size_popup_timer -= 1
        else:
            self.size_popup_value = None
            self.size_popup_pos = None

        if self.drawing_mode:
            pen = QPen(QColor(255, 120, 0))
            pen.setWidth(2)
            p.setPen(pen)
            p.drawRect(self.rect())

    def draw_background(self, painter):
        r, g, b, a = self.board_color
        painter.fillRect(self.rect(), QColor(r, g, b, a))

    def draw_item(self, painter, item):
        pen = QPen(item["color"])
        pen.setWidth(item["width"])
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        t = item["type"]

        if t == "pen":
            pts = item["points"]
            for i in range(1, len(pts)):
                painter.drawLine(pts[i - 1], pts[i])

        elif t == "line":
            painter.drawLine(item["start"], item["end"])

        elif t == "rect":
            painter.drawRect(item["rect"])

    def show_size_popup(self, pos, value):
        self.size_popup_pos = pos
        self.size_popup_value = value
        self.size_popup_timer = 10
        self.update()

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
        self.redo_stack.append(self.history.pop())
        self.update()

    def redo(self):
        if not self.redo_stack:
            return
        self.history.append(self.redo_stack.pop())
        self.update()

    def clear(self):
        if self.history:
            self.redo_stack.clear()
            self.history.append({"type": "clear_marker"})
            self.history.clear()
        self.update()

    def save_with_background(self, path):
        pix = self.grab()
        pix.save(path, "PNG")

    def save_transparent(self, path):
        old = self.board_color
        self.board_color = (0, 0, 0, 0)

        pix = self.grab()
        pix.save(path, "PNG")

        self.board_color = old
        self.update()

    def erase_at(self, pos):
        pass
