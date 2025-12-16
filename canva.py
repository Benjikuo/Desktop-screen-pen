# canva.py
# type: ignore

from PySide2.QtGui import QColor, QPainter, QPen
from PySide2.QtCore import Qt, QPoint, QRect
from PySide2.QtWidgets import QWidget
import copy

from controller import BrushState


class Canva(QWidget):
    def __init__(self, window):
        super().__init__(window)

        self.setMouseTracking(True)

        self.board_color = (0, 0, 0, 50)

        self.current_brush: BrushState | None = None
        self.start_pos: QPoint | None = None
        self.last_pos: QPoint | None = None
        self.current_points: list[QPoint] = []

        self.strokes: list[dict] = []

        self.history = []
        self.history_index = -1
        self.add_history_snapshot()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        brush = self.window().controller.get_brush()
        self.begin_stroke(event.pos(), brush)

    def mouseMoveEvent(self, event):
        if not self.current_brush:
            return

        self.move_stroke(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        self.end_stroke()

    def begin_stroke(self, pos: QPoint, brush: BrushState):
        self.current_brush = brush
        self.start_pos = pos
        self.last_pos = pos
        self.current_points = [pos]

        if brush.tool == "eraser":
            self.erase_at(pos)

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
            self.current_points.append(pos)
        else:
            self.last_pos = pos

        self.update()

    def end_stroke(self):
        b = self.current_brush
        if not b:
            return

        if b.tool != "eraser":
            stroke = {
                "type": b.shape,
                "color": b.color,
                "width": b.size,
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

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        self.draw_background(p)

        for s in self.strokes:
            self.draw_stroke(p, s)

        if self.current_brush:
            self.draw_preview(p)

        if self.board_color != (0, 0, 0, 0):
            pen = QPen(QColor(255, 120, 0))
            pen.setWidth(2)
            p.setPen(pen)
            p.drawRect(self.rect())

    def draw_background(self, painter):
        r, g, b, a = self.board_color
        painter.fillRect(self.rect(), QColor(r, g, b, a))

    def _apply_cap_style(self, pen: QPen, round_cap: bool):
        pen.setCapStyle(Qt.RoundCap if round_cap else Qt.FlatCap)

    def draw_stroke(self, painter, s):
        pen = QPen(s["color"])
        pen.setWidth(s["width"])
        self._apply_cap_style(pen, bool(s.get("round_cap", False)))
        painter.setPen(pen)

        if s["type"] == "free":
            pts = s["points"]
            for i in range(1, len(pts)):
                painter.drawLine(pts[i - 1], pts[i])

        elif s["type"] == "line":
            painter.drawLine(s["start"], s["end"])

        elif s["type"] == "rect":
            painter.drawRect(s["rect"])

    def draw_preview(self, painter):
        b = self.current_brush
        if not b or b.tool == "eraser":
            return

        pen = QPen(b.color)
        pen.setWidth(b.size)
        self._apply_cap_style(pen, b.round_cap)
        painter.setPen(pen)

        if b.shape == "free" and len(self.current_points) > 1:
            for i in range(1, len(self.current_points)):
                painter.drawLine(self.current_points[i - 1], self.current_points[i])

        elif b.shape == "line":
            painter.drawLine(self.start_pos, self.last_pos)

        elif b.shape == "rect":
            rect = QRect(self.start_pos, self.last_pos).normalized()
            painter.drawRect(rect)

    def erase_at(self, pos):
        r = self.current_brush.size / 2
        self.strokes = [s for s in self.strokes if not self.stroke_hit(s, pos, r)]
        self.update()

    def stroke_hit(self, s, pos, r):
        if s["type"] == "free":
            return any((p - pos).manhattanLength() < r for p in s["points"])
        if s["type"] == "line":
            return False
        if s["type"] == "rect":
            return s["rect"].contains(pos)
        return False

    def snapshot(self):

        return copy.deepcopy(self.strokes)

    def restore(self, snap):
        self.strokes = snap
        self.update()

    def add_history_snapshot(self):
        snap = self.snapshot()
        self.history = self.history[: self.history_index + 1]
        self.history.append(snap)
        self.history_index += 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.restore(self.history[self.history_index])

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore(self.history[self.history_index])

    def clear(self):
        self.strokes.clear()
        self.history.clear()
        self.history_index = -1
        self.add_history_snapshot()
        self.update()
