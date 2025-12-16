# type: ignore
from PySide2.QtCore import Qt, QPoint
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


class Pen:
    def __init__(self):
        self.tool = "pen"
        self.size = 4
        self.shape = "free"
        self.color = "white"


class Canva(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.drawing_mode = True
        self.board_color = (0, 0, 0, 50)
        self.setCursor(Qt.CrossCursor)

        self.tool = "pen"
        self.tools = {
            "pen": {"size": 4, "shape": "free", "color": "white"},
            "highlight": {"size": 12, "shape": "free", "color": "yellow"},
            "eraser": {"size": 30, "shape": "free", "color": None},
            "crop_eraser": {"size": 40, "shape": "rect", "color": None},
        }
        self.shape = "free"
        self.thickness = 4
        self.color = "white"
        self.pen_color = QColor(255, 255, 255)

        self.start_pos = None
        self.last_pos = None
        self.current_stroke = []

        self.strokes = []
        self.history = []
        self.history_index = -1

        self.eraser_pos = None
        self.setMouseTracking(True)

        self.size_popup_pos = None
        self.size_popup_value = None
        self.size_popup_timer = 0

        self.add_history_snapshot()

    def snapshot(self):
        """建立當前畫面的完整快照。"""
        return {
            "strokes": [
                {
                    "type": s["type"],
                    "points": s.get("points", []),
                    "start": s.get("start"),
                    "end": s.get("end"),
                    "rect": s.get("rect"),
                    "color": s["color"],
                    "width": s["width"],
                }
                for s in self.strokes
            ],
            "tool": self.tool,
            "tool_state": {t: self.tools[t].copy() for t in self.tools},
        }

    def restore(self, snap):
        """載入快照內容。"""
        self.strokes = [
            {
                "type": s["type"],
                "points": s.get("points", []),
                "start": s.get("start"),
                "end": s.get("end"),
                "rect": s.get("rect"),
                "color": s["color"],
                "width": s["width"],
            }
            for s in snap["strokes"]
        ]

        self.tool = snap["tool"]
        self.tools = {t: snap["tool_state"][t].copy() for t in snap["tool_state"]}

        cfg = self.tools[self.tool]
        self.shape = cfg["shape"]
        self.thickness = cfg["size"]
        if cfg["color"]:
            r, g, b, a = cfg["color"]
            self.pen_color = QColor(r, g, b, a)

        self.update()

    def add_history_snapshot(self):
        """加入新的歷史紀錄。"""
        snap = self.snapshot()
        self.history = self.history[: self.history_index + 1]
        self.history.append(snap)
        self.history_index += 1

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

        # finalize stroke
        if self.shape == "free" and len(self.current_stroke) > 1:
            self.strokes.append(
                {
                    "type": "pen",
                    "points": self.current_stroke[:],
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )

        elif self.shape == "line":
            self.strokes.append(
                {
                    "type": "line",
                    "start": self.start_pos,
                    "end": self.last_pos,
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )

        elif self.shape == "rect":
            rect = Qrect(self.start_pos, self.last_pos).normalized()
            self.strokes.append(
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

        self.add_history_snapshot()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 背景
        self.draw_background(p)

        # 歷史筆畫
        for item in self.strokes:
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
                rect = Qrect(self.start_pos, self.last_pos).normalized()
                preview = {
                    "type": "rect",
                    "rect": rect,
                    "color": self.pen_color,
                    "width": self.thickness,
                }

            if preview:
                self.draw_item(p, preview)

        # 橡皮擦圈
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

            self.size_popup_timer -= 1
            if self.size_popup_timer <= 0:
                self.size_popup_value = None
                self.size_popup_pos = None

        # 邊框
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

    def last_tool(self):
        pass

    def set_tool(self, tool):
        self.tool = tool
        cfg = self.tools[tool]

        self.shape = cfg["shape"]

        self.thickness = cfg["size"]

        if cfg["color"] is None:
            self.setCursor(Qt.BlankCursor)
        else:
            r, g, b, a = cfg["color"]
            self.pen_color = QColor(r, g, b, a)
            self.setCursor(Qt.CrossCursor)

        self.update()

    def set_size(self, size):
        self.thickness = size
        self.tools[self.tool]["size"] = size

    def set_shape(self, shape):
        self.shape = shape
        self.tools[self.tool]["shape"] = shape

    def set_color(self, color):
        self.color = color
        if color == "white":
            rgb = (255, 255, 255)
        elif color == "red":
            rgb = (248, 49, 47)
        elif color == "orange":
            rgb = (255, 103, 35)
        elif color == "yellow":
            rgb = (255, 176, 46)
        elif color == "green":
            rgb = (0, 210, 106)
        elif color == "blue":
            rgb = (0, 166, 237)
        elif color == "purple":
            rgb = (199, 144, 241)
        else:
            print("Error: Invalid color")

        r, g, b = rgb
        self.pen_color = QColor(r, g, b)
        self.tools[self.tool]["color"] = (r, g, b, 255)
        self.update()

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.restore(self.history[self.history_index])
            self.update()

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore(self.history[self.history_index])
            self.update()

    def clear(self):
        self.strokes = []
        self.update()
        self.add_history_snapshot()
