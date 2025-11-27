# type: ignore
from PySide2.QtCore import Qt, QRect, QPoint, QSize
from PySide2.QtGui import QColor, QIcon, QCursor, QKeySequence
from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QShortcut,
    QMenu,
    QOpenGLWidget,
)
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import os

HIGHLIGHT_ALPHA = 40
BUTTON_SIZE = 50
BAR_SPACE = 10


def get_icon(path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, "image", "toolbar", path)
    return QIcon(full_path)


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


class Canvas(QOpenGLWidget):
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
        self.last_used = None
        self.tool = "pen"
        self.settings = {
            "pen": {"size": 4, "type": "free", "color": 0},
            "highlight": {"size": 10, "type": "free", "color": 3},
            "eraser": {"size": 30, "type": None, "color": None},
        }

        self.start_pos = None
        self.last_pos = None
        self.current_stroke = []
        self.history = []

        self.setMouseTracking(True)
        self.eraser_pos = None
        self.size_popup_pos = None
        self.size_popup_value = None
        self.size_popup_timer = 0

    def initializeGL(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    @property
    def thickness(self):
        """從 settings 取得當前工具的粗細"""
        return self.settings[self.tool]["size"]

    @thickness.setter
    def thickness(self, value):
        """設定當前工具的粗細"""
        self.settings[self.tool]["size"] = value

    @property
    def shape(self):
        """從 settings 取得當前工具的形狀"""
        s = self.settings[self.tool]["type"]
        return s if s is not None else "free"

    @shape.setter
    def shape(self, value):
        """設定當前工具的形狀"""
        self.settings[self.tool]["type"] = value

    @property
    def pen_color(self):
        """從 settings 取得當前工具的顏色"""
        color_idx = self.settings[self.tool]["color"]
        if color_idx is None:
            return QColor(255, 255, 255, 255)

        r, g, b = self.color_cycle[color_idx]

        if self.tool == "highlight":
            a = HIGHLIGHT_ALPHA
        else:
            a = 255

        return QColor(r, g, b, a)

    def paintGL(self):
        r, g, b, a = self.board_color
        glClearColor(r / 255.0, g / 255.0, b / 255.0, a / 255.0)
        glClear(GL_COLOR_BUFFER_BIT)

        for item in self.history:
            self.draw_item(item)

        if self.drawing_mode:
            current_shape = self.shape

            if self.tool in ["pen", "highlight"] and self.current_stroke:
                self.draw_item(
                    {
                        "type": "pen",
                        "points": self.current_stroke,
                        "color": self.pen_color,
                        "width": self.thickness,
                    }
                )

            elif current_shape == "line" and self.start_pos and self.last_pos:
                self.draw_item(
                    {
                        "type": "line",
                        "start": self.start_pos,
                        "end": self.last_pos,
                        "color": self.pen_color,
                        "width": self.thickness,
                    }
                )

            elif current_shape == "rect" and self.start_pos and self.last_pos:
                rect = QRect(self.start_pos, self.last_pos).normalized()
                self.draw_item(
                    {
                        "type": "rect",
                        "rect": rect,
                        "color": self.pen_color,
                        "width": self.thickness,
                    }
                )

        if self.tool == "eraser" and self.eraser_pos:
            self.draw_circle_gl(
                self.eraser_pos,
                self.thickness / 2,
                QColor(255, 120, 0, 255),
                2,
            )

        if self.size_popup_value is not None:
            self.draw_circle_gl(
                self.size_popup_pos,
                self.size_popup_value / 2,
                QColor(255, 200, 80, 255),
                2,
            )

        if self.size_popup_timer > 0:
            self.size_popup_timer -= 1
        else:
            self.size_popup_value = None
            self.size_popup_pos = None

        if self.drawing_mode:
            glLineWidth(2)
            r, g, b, a = (255, 120, 0, 225)
            glColor4f(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

            glBegin(GL_LINE_LOOP)
            glVertex2f(0, 0)
            glVertex2f(self.width(), 0)
            glVertex2f(self.width(), self.height())
            glVertex2f(0, self.height())
            glEnd()

    def draw_item(self, item):
        shape = item["type"]
        color = item["color"]
        width = item["width"]

        r, g, b, a = (
            color.red() / 255.0,
            color.green() / 255.0,
            color.blue() / 255.0,
            color.alpha() / 255.0,
        )
        glColor4f(r, g, b, a)
        glLineWidth(width)

        if shape == "pen":
            pts = item["points"]
            if len(pts) > 1:
                glBegin(GL_LINE_STRIP)
                for p in pts:
                    glVertex2f(p.x(), p.y())
                glEnd()

                # 繪製端點圓形使線條更平滑
                glPointSize(width)
                glBegin(GL_POINTS)
                for p in pts:
                    glVertex2f(p.x(), p.y())
                glEnd()

        elif shape == "line":
            start = item["start"]
            end = item["end"]

            glBegin(GL_LINES)
            glVertex2f(start.x(), start.y())
            glVertex2f(end.x(), end.y())
            glEnd()

            glPointSize(width)
            glBegin(GL_POINTS)
            glVertex2f(start.x(), start.y())
            glVertex2f(end.x(), end.y())
            glEnd()

        elif shape == "rect":
            rect = item["rect"]

            glBegin(GL_LINE_LOOP)
            glVertex2f(rect.left(), rect.top())
            glVertex2f(rect.right(), rect.top())
            glVertex2f(rect.right(), rect.bottom())
            glVertex2f(rect.left(), rect.bottom())

            glEnd()

    def draw_circle_gl(self, pos, radius, color, width):
        """使用OpenGL繪製圓圈"""
        r, g, b, a = (
            color.red() / 255.0,
            color.green() / 255.0,
            color.blue() / 255.0,
            color.alpha() / 255.0,
        )
        glColor4f(r, g, b, a)
        glLineWidth(width)

        segments = 32
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            x = pos.x() + radius * math.cos(theta)
            y = pos.y() + radius * math.sin(theta)
            glVertex2f(x, y)
        glEnd()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing_mode:
            pos = event.pos()
            self.start_pos = pos
            self.last_pos = pos
            self.current_stroke = [pos]

        elif event.button() == Qt.MiddleButton:
            self.window().close()

        elif event.button() == Qt.RightButton:
            if self.board_color != (0, 0, 0, 0):
                self.board_color = (0, 0, 0, 0)
                self.drawing_mode = False
            else:
                self.board_color = (0, 0, 0, 50)
                self.drawing_mode = True

            self.update()

    def mouseMoveEvent(self, event):
        if self.tool == "eraser":
            self.eraser_pos = event.pos()
            self.update()

        if event.buttons() != Qt.LeftButton or not self.drawing_mode:
            return

        pos = event.pos()

        if self.tool == "eraser":
            self.erase_at(pos)
        else:
            current_shape = self.shape
            if current_shape == "free":
                self.current_stroke.append(pos)
            elif current_shape in ("line", "rect"):
                self.last_pos = pos

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self.drawing_mode:
            return

        current_shape = self.shape

        if self.tool in ["pen", "highlight"] and len(self.current_stroke) > 1:
            self.history.append(
                {
                    "type": "pen",
                    "points": self.current_stroke[:],
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )

        elif current_shape == "line" and self.start_pos and self.last_pos:
            self.history.append(
                {
                    "type": "line",
                    "start": self.start_pos,
                    "end": self.last_pos,
                    "color": self.pen_color,
                    "width": self.thickness,
                }
            )

        elif current_shape == "rect" and self.start_pos and self.last_pos:
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

    def set(self, tool=None, size=None, shape=None, color=None):
        if tool != self.last_used["tool"] and "eraser" not in tool:
            self.last_used = tool

        for key, value in (("size", size), ("type", shape), ("color", color)):
            if value is not None:
                self.settings[self.tool][key] = value

        self.tool = tool

        # 橡皮擦隱藏游標
        if tool == "eraser":
            self.setCursor(Qt.BlankCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def set_rec(self):
        self.set("pen", shape="rect", color="red")

    def set_high(self):
        self.set_tool("highlight")

    def set_pen(self):
        self.set_tool("pen")

    def set_last(self):
        if self.last_used["tool"] and self.last_used["tool"] != self.tool:
            self.set_tool(self.last_used["tool"])

    def set_color_tuple(self, rgb_tuple):
        try:
            color_idx = self.color_cycle.index(rgb_tuple)
            self.settings[self.tool]["color"] = color_idx
        except ValueError:
            pass
        self.update()

    def save(self):
        pass

    def undo(self):
        if self.history:
            self.history.pop()
            self.update()

    def redo(self):
        pass

    def clear(self):
        self.history = []
        self.update()

    def close(self):
        pass

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

    def show_size_popup(self, pos, size):
        self.size_popup_pos = pos
        self.size_popup_value = size
        self.size_popup_timer = 10
        self.update()

    def toggle_board(self):
        self.drawing_mode = True

        if self.board_color == (0, 0, 0, 50):
            self.board_color = (0, 0, 0, 255)
        else:
            self.board_color = (0, 0, 0, 50)

        if self.tool == "eraser":
            self.setCursor(Qt.BlankCursor)
        else:
            self.setCursor(Qt.CrossCursor)

        self.update()

    def toggle_eraser(self):
        if self.tool == "eraser":
            # 恢復上次使用的工具
            if self.last_used["tool"]:
                self.set_tool(self.last_used["tool"])
        else:
            self.set_tool("eraser")

    def toggle_shape(self):
        if self.tool != "pen":
            self.set_tool("pen")
        else:
            self.set_tool("highlight")
        self.update()

    def toggle_color(self):
        self.color_index = (self.color_index + 1) % len(self.color_cycle)
        self.settings[self.tool]["color"] = self.color_index
        self.set_tool("pen")
        self.update()


class Toolbar(QFrame):

    def __init__(self, parent, canvas):
        super().__init__(parent)
        self.win = parent
        self.canvas = canvas

        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self.setStyleSheet(
            """
            QFrame {
                background-color: rgba(40,40,40,255);
                border-radius:10px;
            }
            QPushButton {
                background-color: rgba(70,70,70,255);
                padding: 6px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(100,100,100,255);
            }

            QPushButton:pressed {
                background-color: rgba(255,140,0,100);
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(BAR_SPACE, BAR_SPACE, BAR_SPACE, BAR_SPACE)
        layout.setSpacing(BAR_SPACE)

        def button(icon_path, scale):
            btn = QPushButton()
            btn.setIcon(get_icon(icon_path))
            btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
            btn.setIconSize(QSize(BUTTON_SIZE * scale, BUTTON_SIZE * scale))
            layout.addWidget(btn)
            return btn

        btn_board = button("board.svg", 0.8)
        btn_board.clicked.connect(canvas.toggle_board)

        btn_tool = button("tools/pen.svg", 0.8)
        btn_size = button(" ", 0.8)
        btn_shape = button(" ", 0.8)
        btn_color = button(" ", 0.8)
        btn_save = button("save.svg", 0.8)
        btn_undo = button("undo.svg", 0.9)
        btn_redo = button("redo.svg", 0.9)
        btn_clear = button("clear.svg", 0.8)

        btn_close = button("close.svg", 0.9)
        btn_close.clicked.connect(self.window().close)

        # pen_menu = QMenu(self)
        # pen_menu.addAction(
        #     "普通筆",
        #     lambda: (
        #         canvas.set_tool("pen"),
        #         canvas.set_thickness(4),
        #         self.update_size_menu(),
        #     ),
        # )
        # pen_menu.addAction(
        #     "螢光筆",
        #     lambda: (
        #         canvas.set_tool("highlight"),
        #         canvas.set_thickness(20),
        #         self.update_size_menu(),
        #     ),
        # )

        # btn_shape = add_btn("tools/pen.svg", 1)
        # shape_menu = QMenu(self)
        # shape_menu.addAction("自由筆", lambda: canvas.set_shape("free"))
        # shape_menu.addAction("直線", lambda: canvas.set_shape("line"))
        # shape_menu.addAction("矩形", lambda: canvas.set_shape("rect"))
        # btn_shape.setMenu(shape_menu)

        # self.size_label = QPushButton(f"{canvas.thickness}px")
        # self.size_label.setFixedSize(60, 40)
        # self.size_label.setStyleSheet("font-size: 16px; color: white;")
        # layout.addWidget(self.size_label)

        # self.update_size_menu()

        # self.color_btn = QPushButton()
        # self.color_btn.setFixedSize(40, 40)
        # r, g, b = canvas.color_cycle[canvas.color_index]
        # self.color_btn.setStyleSheet(
        #     f"background-color: rgb({r},{g},{b}); border-radius:6px;"
        # )
        # layout.addWidget(self.color_btn)

        # color_menu = QMenu(self)
        # colors = {
        #     "白": (255, 255, 255),
        #     "灰": (136, 136, 136),
        #     "紅": (255, 0, 0),
        #     "橙": (255, 136, 0),
        #     "黃": (255, 255, 0),
        #     "綠": (0, 255, 0),
        #     "藍": (0, 128, 255),
        #     "紫": (170, 85, 255),
        # }

        # for name, rgb in colors.items():
        #     color_menu.addAction(
        #         name,
        #         lambda _, c=rgb: (canvas.set_color_tuple(c), self.update_color_btn()),
        #     )
        # self.color_btn.setMenu(color_menu)

        # btn_undo = add_btn("tools/undo.svg", 40)
        # btn_undo.clicked.connect(canvas.undo)

        # btn_clear = add_btn("tools/clear.svg", 40)
        # btn_clear.clicked.connect(canvas.clear)

        # btn_save = add_btn("tools/save.svg", 40)

        # btn_close = add_btn("tools/close.svg", 40)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            if self.canvas.board_color != (0, 0, 0, 0):
                self.canvas.board_color = (0, 0, 0, 0)
                self.canvas.drawing_mode = False
                self.canvas.setAttribute(Qt.WA_TransparentForMouseEvents, True)

            else:
                self.canvas.board_color = (0, 0, 0, 50)
                self.canvas.drawing_mode = True
                self.win.setAttribute(Qt.WA_TransparentForMouseEvents, False)

            self.canvas.update()

        elif event.button() == Qt.MiddleButton:
            self.window().close()

    def update_color_btn(self):
        """更新顏色按鈕的顯示"""
        color_idx = self.canvas.settings[self.canvas.tool]["color"]
        if color_idx is not None:
            r, g, b = self.canvas.color_cycle[color_idx]
            self.color_btn.setStyleSheet(
                f"background-color: rgb({r},{g},{b}); border-radius:6px;"
            )

    def update_size_menu(self):
        """根據當前工具更新大小選單"""
        size_menu = QMenu(self)

        # 根據工具類型選擇對應的圖示資料夾
        tool_map = {
            "pen": "pen_size",
            "highlight": "highlight_size",
            "eraser": "eraser_size",
        }

        icon_folder = tool_map.get(self.canvas.tool, "pen_size")

        # 大小對應的圖示編號 (1-5 對應不同大小)
        size_icon_map = {
            2: 1,
            4: 1,
            6: 2,
            8: 2,
            10: 3,
            15: 4,
            20: 4,
            30: 5,
        }

        for size in [2, 4, 6, 8, 10, 15, 20, 30]:
            icon_num = size_icon_map.get(size, 1)
            icon_path = f"{icon_folder}/{icon_folder} ({icon_num}).svg"

            action = size_menu.addAction(get_icon(icon_path), f"{size}px")
            action.triggered.connect(
                lambda checked=False, v=size: (
                    self.canvas.set_thickness(v),
                    self.size_label.setText(f"{v}px"),
                )
            )

        self.size_label.setMenu(size_menu)


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.canvas = Canvas(self)
        self.toolbar = Toolbar(self, self.canvas)
        self.toolbar.raise_()

        def shortcut(key, func):
            QShortcut(QKeySequence(key), self, activated=func)

        shortcut("W", self.canvas.toggle_board)
        shortcut("E", self.canvas.toggle_eraser)
        shortcut("D", self.canvas.set_last)
        shortcut("R", self.canvas.set_rec)
        shortcut("F", self.canvas.set_pen)
        shortcut("V", self.canvas.set_high)
        shortcut("C", self.canvas.toggle_color)
        shortcut("S", self.canvas.toggle_shape)
        shortcut("X", self.canvas.clear)

        self.showFullScreen()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        change = 2

        if delta > 0:
            new_size = min(50, self.canvas.thickness + change)
        else:
            new_size = max(2, self.canvas.thickness - change)

        # self.canvas.set_thickness(new_size)
        # self.toolbar.size_label.setStyleSheet("font-size: 20px; color: white;")
        # self.toolbar.size_label.setText(f"{new_size}px")
        # self.canvas.show_size_popup(self.mapFromGlobal(QCursor.pos()), new_size)

    def mouse_through(self, enable):
        if enable:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            print("mouse through")
        else:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def resizeEvent(self, event=None):
        self.canvas.setGeometry(self.rect())
        self.toolbar.adjustSize()
        self.toolbar.move((self.width() - self.toolbar.width()) // 2, 20)

    def closeEvent(self, event=None):
        QApplication.instance().quit()


if __name__ == "__main__":
    app = QApplication([])
    w = Window()
    w.show()
    app.exec_()
