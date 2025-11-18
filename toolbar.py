# toolbar.py
from PySide2.QtWidgets import QFrame, QPushButton, QHBoxLayout, QMenu
from PySide2.QtGui import QColor
from PySide2.QtCore import Qt


class Toolbar(QFrame):
    def __init__(self, parent, canvas):
        super().__init__(parent)
        self.canvas = canvas

        self.setFixedHeight(60)

        self.setStyleSheet(
            """
            QFrame {
                background-color: rgba(34,34,34,220);
                border-radius: 10px;
            }
            QPushButton {
                color: white;
                font-family: 'Segoe UI Emoji';
                font-size: 18px;
                border: none;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,40);
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # -------------------------------------------------------
        # 工具按鈕生成函式
        # -------------------------------------------------------
        def add_btn(text):
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            layout.addWidget(btn)
            return btn

        # -------------------------------------------------------
        # 黑板
        # -------------------------------------------------------
        btn_board = add_btn("📘 黑板")
        btn_board.clicked.connect(canvas.toggle_board)

        # -------------------------------------------------------
        # 橡皮擦 ▼
        # -------------------------------------------------------
        btn_eraser = add_btn("🧽 樣皮擦 ▼")
        eraser_menu = QMenu(self)

        eraser_menu.addAction(
            "畫筆橡皮擦（圓）",
            lambda: (
                canvas.set_tool("eraser"),
                canvas.set_erase_type("circle"),
                canvas.set_pen_size(30),
            ),
        )

        eraser_menu.addAction(
            "矩形橡皮擦（框選）",
            lambda: (
                canvas.set_tool("eraser"),
                canvas.set_erase_type("rect"),
                canvas.set_pen_size(15),
            ),
        )

        btn_eraser.setMenu(eraser_menu)

        # -------------------------------------------------------
        # 筆刷 ▼
        # -------------------------------------------------------
        btn_brush = add_btn("✏️ 筆刷 ▼")
        brush_menu = QMenu(self)

        brush_menu.addAction(
            "普通筆（4px）",
            lambda: (
                canvas.set_tool("brush"),
                canvas.set_brush_type("pen"),
                canvas.set_pen_color((255, 255, 255)),
                canvas.set_pen_size(4),
            ),
        )

        brush_menu.addAction(
            "螢光筆（10px 黃）",
            lambda: (
                canvas.set_tool("brush"),
                canvas.set_brush_type("highlighter"),
                canvas.set_pen_color((255, 255, 0)),
                canvas.set_pen_size(10),
            ),
        )

        brush_menu.addAction(
            "自由筆", lambda: (canvas.set_tool("brush"), canvas.set_brush_type("free"))
        )

        btn_brush.setMenu(brush_menu)

        # -------------------------------------------------------
        # 形狀 ▼
        # -------------------------------------------------------
        btn_shape = add_btn("⬛ 形狀 ▼")
        shape_menu = QMenu(self)

        shape_menu.addAction(
            "自由筆", lambda: (canvas.set_tool("brush"), canvas.set_shape("free"))
        )

        shape_menu.addAction(
            "直線", lambda: (canvas.set_tool("shape"), canvas.set_shape("line"))
        )

        shape_menu.addAction(
            "矩形", lambda: (canvas.set_tool("shape"), canvas.set_shape("rect"))
        )

        btn_shape.setMenu(shape_menu)

        # -------------------------------------------------------
        # 大小 ▼（固定 2 / 4 / 6 / 8 / 10）
        # -------------------------------------------------------
        btn_size = add_btn("📏 大小 ▼")
        size_menu = QMenu(self)

        for s in [2, 4, 6, 8, 10]:
            size_menu.addAction(f"{s}px", lambda _, v=s: (canvas.set_pen_size(v)))

        btn_size.setMenu(size_menu)

        # -------------------------------------------------------
        # 顏色 ▼
        # -------------------------------------------------------
        btn_color = add_btn("🎨 顏色 ▼")
        color_menu = QMenu(self)

        colors = {
            "白 ⬜": (255, 255, 255),
            "紅 🟥": (255, 0, 0),
            "橙 🟧": (255, 136, 0),
            "黃 🟨": (255, 255, 0),
            "綠 🟩": (0, 255, 0),
            "藍 🟦": (0, 128, 255),
            "紫 🟪": (170, 85, 255),
            "灰 ⬜": (136, 136, 136),
        }

        for name, rgb in colors.items():
            color_menu.addAction(name, lambda _, c=rgb: (canvas.set_pen_color(c)))

        btn_color.setMenu(color_menu)

        # -------------------------------------------------------
        # Undo / Redo / Clear / Close
        # -------------------------------------------------------
        btn_undo = add_btn("↩ 返回")
        btn_undo.clicked.connect(canvas.undo)

        btn_redo = add_btn("↪ 重做")
        btn_redo.clicked.connect(canvas.redo)

        btn_clear = add_btn("🧹 清除")
        btn_clear.clicked.connect(canvas.clear)

        btn_close = add_btn("❌ 關閉")
        btn_close.clicked.connect(parent.close)
