# canvas.py
import math
from math import hypot
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QPainter, QImage, QColor, QPen, QCursor
from PySide2.QtCore import Qt, QRect, QPoint


def make_color(r, g, b, a=255):
    return QColor(r, g, b, a)


class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ----------- 畫布 Layer -----------
        self.layer = QImage(self.size(), QImage.Format_ARGB32)
        self.layer.fill(Qt.transparent)

        # ----------- Undo / Redo -----------
        self.undo_stack = []
        self.redo_stack = []

        # ----------- 工具設定 -----------
        self.current_tool = "brush"  # brush / eraser / rect_eraser / shape_line / shape_rect / free_shape
        self.brush_type = "pen"  # pen / highlighter / free
        self.erase_type = "circle"  # circle / rect
        self.shape_type = "free"  # free / line / rect
        self.pen_size = 4
        self.pen_color = make_color(255, 255, 255)

        # ----------- 黑板背景 -----------
        self.board_dark = False

        # ----------- 動態繪圖狀態 -----------
        self.last_pos = None
        self.start_pos = None
        self.preview_rect = None
        self.preview_line_end = None

        # ----------- 顯示筆刷預覽 -----------
        self.cursor_pos = QPoint(-100, -100)

        self.setMouseTracking(True)

    # ------------ Snapshot for Undo ------------
    def snapshot(self):
        self.undo_stack.append(self.layer.copy())
        self.redo_stack.clear()

    # ------------ Clear ------------
    def clear(self):
        self.snapshot()
        self.layer.fill(Qt.transparent)
        self.update()

    # ------------ Undo ------------
    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.layer.copy())
        self.layer = self.undo_stack.pop()
        self.update()

    # ------------ Redo ------------
    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.layer.copy())
        self.layer = self.redo_stack.pop()
        self.update()

    # ------------ Setters from Toolbar ------------
    def set_tool(self, tool):
        self.current_tool = tool

    def set_brush_type(self, t):
        self.brush_type = t

    def set_erase_type(self, t):
        self.erase_type = t

    def set_shape(self, t):
        self.shape_type = t

    def set_pen_size(self, s):
        self.pen_size = s

    def set_pen_color(self, rgb):
        r, g, b = rgb
        self.pen_color = QColor(r, g, b)

    # ------------ 黑板背景切換 ------------
    def toggle_board(self):
        self.board_dark = not self.board_dark
        self.update()

    # ------------ Resize Canvas ------------
    def resizeEvent(self, event):
        new = QImage(self.size(), QImage.Format_ARGB32)
        new.fill(Qt.transparent)

        p = QPainter(new)
        p.drawImage(0, 0, self.layer)
        p.end()

        self.layer = new

    # ------------ PaintEvent ------------
    def paintEvent(self, event):
        p = QPainter(self)

        # ------- 畫背景（黑板） -------
        if self.board_dark:
            p.fillRect(self.rect(), QColor(0, 0, 0, 200))
        else:
            p.fillRect(self.rect(), QColor(0, 0, 0, 50))

        # ------- 畫 layer -------
        p.drawImage(0, 0, self.layer)

        # ------- 預覽（形狀） -------
        if self.current_tool == "shape":
            if self.shape_type == "line" and self.start_pos and self.preview_line_end:
                pen = QPen(self.pen_color)
                pen.setWidth(self.pen_size)
                p.setPen(pen)
                p.drawLine(self.start_pos, self.preview_line_end)

            elif self.shape_type == "rect" and self.preview_rect:
                pen = QPen(self.pen_color)
                pen.setWidth(self.pen_size)
                p.setPen(pen)
                p.drawRect(self.preview_rect)

        # ------- 游標筆刷預覽 -------
        if self.current_tool in ("brush", "eraser"):
            pen = QPen(QColor(255, 255, 255, 120))
            pen.setWidth(2)
            p.setPen(pen)

            if self.current_tool == "eraser" and self.erase_type == "rect":
                s = self.pen_size * 2
                p.drawRect(
                    self.cursor_pos.x() - s // 2, self.cursor_pos.y() - s // 2, s, s
                )
            else:
                p.drawEllipse(self.cursor_pos, self.pen_size, self.pen_size)

        p.end()

    # ------------ Mouse Move Preview Tracking ------------
    def mouseMoveEvent(self, e):
        self.cursor_pos = e.pos()

        if e.buttons() & Qt.LeftButton:
            self.draw_move(e.pos())

        else:
            # 預覽形狀
            if self.current_tool == "shape" and self.start_pos:
                if self.shape_type == "line":
                    self.preview_line_end = e.pos()
                elif self.shape_type == "rect":
                    self.preview_rect = QRect(self.start_pos, e.pos()).normalized()
            self.update()

    # ------------ Mouse Press ------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.snapshot()
            self.last_pos = e.pos()
            self.start_pos = e.pos()

    # ------------ Mouse Release ------------
    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return

        # 形狀工具：真正畫上去
        if self.current_tool == "shape":
            p = QPainter(self.layer)
            pen = QPen(self.pen_color)
            pen.setWidth(self.pen_size)
            p.setPen(pen)

            if self.shape_type == "line":
                p.drawLine(self.start_pos, e.pos())

            elif self.shape_type == "rect":
                rect = QRect(self.start_pos, e.pos()).normalized()
                p.drawRect(rect)

            p.end()

        self.last_pos = None
        self.preview_rect = None
        self.preview_line_end = None
        self.update()

    # =============== Brush / Eraser Stroke ===============
    def draw_move(self, pos):
        if not self.last_pos:
            self.last_pos = pos

        p = QPainter(self.layer)

        # ----- 橡皮擦 -----
        if self.current_tool == "eraser":
            p.setCompositionMode(QPainter.CompositionMode_Clear)

            if self.erase_type == "circle":
                p.drawEllipse(pos, self.pen_size, self.pen_size)
            else:
                s = self.pen_size * 2
                p.drawRect(pos.x() - s // 2, pos.y() - s // 2, s, s)

            p.end()
            self.update()
            self.last_pos = pos
            return

        # ----- 筆刷 -----
        if self.current_tool == "brush":
            pen = QPen(self.pen_color)
            pen.setWidth(self.pen_size)
            pen.setCapStyle(Qt.RoundCap)

            # 螢光筆透明度
            if self.brush_type == "highlighter":
                pen.setColor(
                    QColor(
                        self.pen_color.red(),
                        self.pen_color.green(),
                        self.pen_color.blue(),
                        50,
                    )
                )

            p.setPen(pen)

            # 補間畫線（避免縫隙）
            dist = hypot(pos.x() - self.last_pos.x(), pos.y() - self.last_pos.y())
            steps = max(1, int(dist / (self.pen_size * 0.4)))

            for i in range(steps):
                t = i / steps
                ix = self.last_pos.x() + (pos.x() - self.last_pos.x()) * t
                iy = self.last_pos.y() + (pos.y() - self.last_pos.y()) * t
                p.drawPoint(int(ix), int(iy))

        p.end()
        self.update()
        self.last_pos = pos
