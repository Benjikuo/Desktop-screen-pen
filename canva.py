# canva.py
# type: ignore

from PySide2.QtGui import QColor, QPainter, QPen
from PySide2.QtCore import Qt, QPoint, QRect
from PySide2.QtGui import QPainterPath
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QFont
import copy
import math

from controller import BrushState


class Canva(QWidget):
    def __init__(self, window):
        super().__init__(window)

        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

        self.board_color = (0, 0, 0, 50)
        self.mouse_pos = None

        self.current_brush: BrushState | None = None
        self.start_pos: QPoint | None = None
        self.last_pos: QPoint | None = None
        self.current_points: list[QPoint] = []
        self.strokes: list[dict] = []

        self._eraser_changed = False

        self.history = []
        self.history_index = -1
        self.add_history_snapshot()

        self.popup_value = 0

    # mouse events
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            brush = self.controller.get_brush()
            self.begin_stroke(event.pos(), brush)

        elif event.button() == Qt.MiddleButton:
            self.controller.quit()

        elif event.button() == Qt.RightButton:
            self.controller.set_mode("view")

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()

        if event.buttons() & Qt.LeftButton:
            self.move_stroke(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_stroke()

    def leaveEvent(self, event):
        self.mouse_pos = None
        self.update()

    # stroke lifecycle
    def begin_stroke(self, pos: QPoint, brush: BrushState):
        self.current_brush = brush
        self.start_pos = pos
        self.last_pos = pos
        self.current_points = [pos]

        self.toolbar.hide()
        self.update()

    def move_stroke(self, pos: QPoint):
        b = self.current_brush
        if not b:
            return

        if b.tool == "eraser":
            self.erase_at(pos)
            return

        if b.shape == "free":
            if not self.current_points:
                self.current_points.append(pos)
            else:
                last = self.current_points[-1]
                if (pos - last).manhattanLength() >= self.current_brush.size / 4:
                    self.current_points.append(pos)
        else:
            self.last_pos = pos

        self.update()

    def end_stroke(self):
        b = self.current_brush
        if not b:
            return

        if b.tool == "eraser" and self._eraser_changed:
            self.add_history_snapshot()
            self._eraser_changed = False

        if b.tool == "crop_eraser":
            self.apply_crop_eraser()
            if self._eraser_changed:
                self.add_history_snapshot()
                self._eraser_changed = False

        elif b.tool != "eraser":
            stroke = {
                "shape": b.shape,
                "color": b.color,
                "size": b.size,
                "round_cap": b.round_cap,
            }

            if b.shape == "free":
                stroke["points"] = self.current_points[:]

            elif b.shape == "line":
                stroke["start"] = self.start_pos
                stroke["end"] = self.last_pos

            elif b.shape == "rect":
                stroke["rect"] = QRect(self.start_pos, self.last_pos).normalized()

            self.strokes.append(stroke)
            self.add_history_snapshot()

        self.current_brush = None
        self.current_points = []

        self.toolbar.show()
        self.update()

    # painting
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.draw_background(painter)

        for s in self.strokes:
            self.draw_stroke(painter, s)

        if self.current_brush:
            self.draw_preview(painter)

        self.draw_ui_overlay(painter)

        if self.board_color != (0, 0, 0, 0):
            pen = QPen(QColor(255, 120, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self.rect())

    def draw_background(self, painter):
        r, g, b, a = self.board_color
        painter.fillRect(self.rect(), QColor(r, g, b, a))

    def draw_stroke(self, painter, s):
        pen = QPen(s["color"])
        pen.setWidth(s["size"])
        self.apply_cap_style(pen, bool(s.get("round_cap", False)))
        painter.setPen(pen)

        if s["shape"] == "free":
            self.draw_free_curve(painter, s["points"])

        elif s["shape"] == "line":
            painter.drawLine(s["start"], s["end"])

        elif s["shape"] == "rect":
            painter.drawRect(s["rect"])

    def draw_preview(self, painter):
        b = self.current_brush
        if b.tool == "eraser":
            return

        if b.tool == "crop_eraser":
            pen = QPen(QColor(200, 200, 200))
            pen.setWidth(1)
            pen.setStyle(Qt.DashLine)
        else:
            pen = QPen(b.color)
            pen.setWidth(b.size)
            self.apply_cap_style(pen, b.round_cap)

        painter.setPen(pen)

        if b.shape == "free" and len(self.current_points) > 1:
            self.draw_free_curve(painter, self.current_points)

        elif b.shape == "line":
            painter.drawLine(self.start_pos, self.last_pos)

        elif b.shape == "rect":
            rect = QRect(self.start_pos, self.last_pos).normalized()
            painter.drawRect(rect)

    def draw_ui_overlay(self, p: QPainter):
        if self.mouse_pos and self.controller.tool == "eraser":
            pen = QPen(QColor(255, 120, 0))
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)

            r = self.controller.size / 2
            p.drawEllipse(self.mouse_pos, r, r)

        if self.mouse_pos and self.popup_value:
            pen = QPen(QColor(255, 200, 80))
            pen.setWidth(2)
            p.setPen(pen)

            r = self.popup_value / 2
            p.drawEllipse(self.mouse_pos, r, r)

            font = QFont("Microsoft JhengHei")
            font.setPixelSize(15)
            font.setBold(True)
            p.setFont(font)

            p.drawText(self.mouse_pos + QPoint(21, -21), f"{self.popup_value}px")

            self.popup_value = 0

    # pen functions
    def apply_cap_style(self, pen: QPen, round_cap: bool):
        pen.setCapStyle(Qt.RoundCap if round_cap else Qt.FlatCap)

    def draw_free_curve(self, painter, pts):
        if len(pts) < 2:
            return

        path = QPainterPath()
        path.moveTo(pts[0])

        for i in range(1, len(pts) - 1):
            mid = (pts[i] + pts[i + 1]) / 2
            path.quadTo(pts[i], mid)

        path.lineTo(pts[-1])
        painter.drawPath(path)

    # eraser functions
    def erase_at(self, pos):
        before = len(self.strokes)

        r = self.current_brush.size / 2
        self.strokes = [s for s in self.strokes if not self.stroke_hit(s, pos, r)]

        if len(self.strokes) != before:
            self._eraser_changed = True

        self.update()

    def stroke_hit(self, s, pos, r):
        if s["shape"] == "free":
            return any(
                math.hypot(p.x() - pos.x(), p.y() - pos.y()) < r for p in s["points"]
            )
        elif s["shape"] == "line":
            return self.line_hit(s["start"], s["end"], pos, r)
        elif s["shape"] == "rect":
            return self.rect_hit(s["rect"], pos, r)
        else:
            return False

    def line_hit(self, a, b, p, r):
        ax, ay = a.x(), a.y()
        bx, by = b.x(), b.y()
        px, py = p.x(), p.y()

        abx, aby = bx - ax, by - ay
        apx, apy = px - ax, py - ay
        ab_len2 = abx * abx + aby * aby

        if ab_len2 == 0:
            return math.hypot(px - ax, py - ay) <= r

        t = max(0, min(1, (apx * abx + apy * aby) / ab_len2))
        cx = ax + t * abx
        cy = ay + t * aby

        return math.hypot(px - cx, py - cy) <= r

    def rect_hit(self, rect, p, r):
        tl = rect.topLeft()
        tr = rect.topRight()
        bl = rect.bottomLeft()
        br = rect.bottomRight()

        return (
            self.line_hit(tl, tr, p, r)
            or self.line_hit(tr, br, p, r)
            or self.line_hit(br, bl, p, r)
            or self.line_hit(bl, tl, p, r)
        )

    # crop_eraser functions
    def apply_crop_eraser(self):
        before = len(self.strokes)

        crop_rect = QRect(self.start_pos, self.last_pos).normalized()
        self.strokes = [
            s for s in self.strokes if not self.stroke_intersect_rect(s, crop_rect)
        ]

        if len(self.strokes) != before:
            self._eraser_changed = True

    def stroke_intersect_rect(self, s, crop_rect: QRect):
        if s["shape"] == "free":
            return any(crop_rect.contains(p) for p in s["points"])
        elif s["shape"] == "line":
            line_rect = QRect(s["start"], s["end"]).normalized()
            return line_rect.intersects(crop_rect)
        elif s["shape"] == "rect":
            return s["rect"].intersects(crop_rect)
        return False

    # history
    def add_history_snapshot(self):
        self.history_index += 1
        self.history = self.history[: self.history_index]
        self.history.append(copy.deepcopy(self.strokes))

    def restore(self, snap):
        self.strokes = copy.deepcopy(snap)
        self.current_brush = None
        self.start_pos = None
        self.last_pos = None
        self.current_points = []

        self.toolbar.show()
        self.update()

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.restore(self.history[self.history_index])

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore(self.history[self.history_index])

    def clear(self):
        if not self.strokes:
            return

        self.strokes.clear()
        self.add_history_snapshot()
        self.update()
