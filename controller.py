# controller.py
# type: ignore

from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QColor
from PySide2.QtCore import Qt
from dataclasses import dataclass
from mss.tools import to_png
from mss import mss
import os


@dataclass
class BrushState:
    tool: str
    shape: str
    size: int
    color: QColor
    color_name: str
    round_cap: bool
    cursor: Qt.CursorShape


COLOR_MAP = {
    "white": QColor(255, 255, 255),
    "red": QColor(248, 49, 47),
    "orange": QColor(255, 103, 35),
    "yellow": QColor(255, 176, 46),
    "green": QColor(0, 210, 106),
    "blue": QColor(0, 166, 237),
    "purple": QColor(199, 144, 241),
}

tool_states = {
    "pen": BrushState(
        tool="pen",
        shape="free",
        size=4,
        color=QColor(255, 255, 255),
        color_name="white",
        round_cap=True,
        cursor=Qt.CrossCursor,
    ),
    "highlight": BrushState(
        tool="highlight",
        shape="line",
        size=14,
        color=QColor(255, 176, 46, 80),
        color_name="yellow",
        round_cap=False,
        cursor=Qt.IBeamCursor,
    ),
    "eraser": BrushState(
        tool="eraser",
        shape="free",
        size=30,
        color=QColor(0, 0, 0, 0),
        color_name="",
        round_cap=False,
        cursor=Qt.BlankCursor,
    ),
    "crop_eraser": BrushState(
        tool="crop_eraser",
        shape="rect",
        size=0,
        color=QColor(0, 0, 0, 0),
        color_name="",
        round_cap=False,
        cursor=Qt.CrossCursor,
    ),
}


class Controller:
    def __init__(self, window, canva):
        self.window = window
        self.canva = canva

        self.tool = "pen"

    def get_brush(self):
        return tool_states[self.tool]

    @property
    def size(self):
        return tool_states[self.tool].size

    @property
    def shape(self):
        return tool_states[self.tool].shape

    @property
    def color(self):
        c = tool_states[self.tool].color
        return c if c else QColor(255, 255, 255)

    @property
    def color_name(self):
        return tool_states[self.tool].color_name

    # wheel event
    def adjust_size(self, delta, pos):
        change = 2

        if delta > 0:
            tool_states[self.tool].size = min(50, self.size + change)
        else:
            tool_states[self.tool].size = max(2, self.size - change)

        self.canva.popup_value = self.size
        self.toolbar.update_icons()
        self.canva.update()

    # mode toggles
    def toggle_drawing_mode(self, reverse=False):
        board_list = [(0, 0, 0, 50), (0, 0, 0, 255), (0, 0, 0, 0)]

        i = board_list.index(self.canva.board_color)
        i = i - 1 if reverse else i + 1
        i %= len(board_list)

        self.canva.board_color = board_list[i]
        self.canva.update()

    def toggle_board(self):
        if self.canva.board_color != (0, 0, 0, 50):
            self.canva.board_color = (0, 0, 0, 50)
        else:
            self.canva.board_color = (0, 0, 0, 255)

        self.canva.update()

    def toggle_tool(self, reverse=False):
        tools = list(tool_states.keys())

        i = tools.index(self.tool)
        i = i - 1 if reverse else i + 1
        i %= len(tools)

        self.set_tool(tools[i])

    def toggle_size(self, reverse=False):
        sizes = [4, 6, 10, 14, 20, 30, 50]

        i = sizes.index(self.size)
        i = i - 1 if reverse else i + 1
        i %= len(sizes)

        self.set_size(sizes[i])

    def toggle_shape(self, reverse=False):
        shapes = ["free", "line", "rect"]

        i = shapes.index(self.shape)
        i = i - 1 if reverse else i + 1
        i %= len(shapes)

        self.set_shape(shapes[i])

    def toggle_color(self, reverse=False):
        if self.color_name == "":
            self.set_color("white")
            return

        colors = list(COLOR_MAP.keys())

        i = colors.index(self.color_name)
        i = i - 1 if reverse else i + 1
        i %= len(colors)

        self.set_color(colors[i])

    def toggle_eraser(self):
        if self.tool != "eraser":
            self.set_tool("eraser")
        else:
            self.set_tool("crop_eraser")

    def toggle_pen(self):
        if self.tool != "pen":
            self.set_tool("pen")
        else:
            self.set_tool("highlight")

    # direct brush settings
    def set_mode(self, mode: str):
        if mode == "view":
            self.canva.board_color = (0, 0, 0, 0)
        elif mode == "drawing" and self.canva.board_color == (0, 0, 0, 0):
            self.canva.board_color = (0, 0, 0, 50)

        self.canva.update()

    def set_pen(self, size=4, shape="free", color="white"):
        self.set_tool("pen")
        self.set_size(size)
        self.set_shape(shape)
        self.set_color(color)

    def set_tool(self, tool: str):
        if tool not in tool_states:
            raise ValueError(f"Invalid tool: {tool}")

        self.tool = tool
        self.toolbar.update_icons()
        self.canva.update()
        self.canva.setCursor(tool_states[self.tool].cursor)

    def set_size(self, size: int):
        if self.tool == "crop_eraser":
            self.set_tool("eraser")

        tool_states[self.tool].size = size
        self.toolbar.update_icons()

    def set_shape(self, shape: str):
        if self.tool == "crop_eraser":
            if shape == "free":
                self.set_tool("eraser")
            elif shape == "line":
                self.set_tool("pen")
        elif self.tool == "eraser":
            if shape == "rect":
                self.set_tool("crop_eraser")
            elif shape == "line":
                self.set_tool("pen")

        tool_states[self.tool].shape = shape
        self.toolbar.update_icons()

    def set_color(self, color_name: str):
        eraser_tool = ["eraser", "crop_eraser"]
        if self.tool in eraser_tool:
            self.set_tool("pen")

        if color_name not in COLOR_MAP:
            raise ValueError(f"Invalid color: {color_name}")

        tool_states[self.tool].color_name = color_name
        base = COLOR_MAP[color_name]
        color = QColor(base)

        if self.tool == "highlight":
            color.setAlpha(80)
        else:
            color.setAlpha(255)

        tool_states[self.tool].color = color
        self.toolbar.update_icons()

    # direct actions
    def save(self, back=None):
        old = self.canva.board_color
        if back == "black":
            self.canva.board_color = (0, 0, 0, 255)
        elif back == "trans":
            self.canva.board_color = (0, 0, 0, 0)
        elif self.canva.board_color == (0, 0, 0, 50):
            self.canva.board_color = (0, 0, 0, 0)

        self.toolbar.hide()
        self.canva.update()
        QApplication.processEvents()

        download = os.path.join(os.path.expanduser("~"), "Downloads")
        default_path = os.path.join(download, "screenshot.png")
        with mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            to_png(screenshot.rgb, screenshot.size, output=default_path)
        os.startfile(download)

        self.canva.board_color = old
        self.toolbar.show()
        self.canva.update()

    def undo(self):
        self.canva.undo()

    def redo(self):
        self.canva.redo()

    def clear(self):
        self.canva.clear()

    def quit(self):
        self.window.close()
