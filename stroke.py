import sys
import random
import math
from math import hypot
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtGui import QPainter, QPixmap, QImage, QColor
from PySide2.QtCore import Qt


# ---------------------------------------------------
# 噴槍粒子筆刷 — 使用 QImage（可 setPixelColor）
# ---------------------------------------------------


def make_spray_brush(size, density=400):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    center = size / 2
    max_dist = center

    for _ in range(density):
        angle = random.random() * math.pi * 2
        dist = (random.random() ** 0.5) * max_dist  # 中心較密

        x = int(center + dist * math.cos(angle))
        y = int(center + dist * math.sin(angle))

        if 0 <= x < size and 0 <= y < size:
            alpha = max(30, 255 - int((dist / max_dist) * 255))
            img.setPixelColor(x, y, QColor(255, 255, 255, alpha))

    return QPixmap.fromImage(img)


# ---------------------------------------------------
# 測試畫布
# ---------------------------------------------------


class SprayCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spray Gun Test (PySide2)")
        self.resize(1200, 800)

        # 畫布
        self.canvas = QPixmap(self.size())
        self.canvas.fill(Qt.black)

        # 噴槍筆刷
        self.brush = make_spray_brush(80, density=500)

        # 間距
        self.spacing = 4
        self.accum_dist = 0
        self.last_pos = None

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.canvas)

    def resizeEvent(self, event):
        new = QPixmap(self.size())
        new.fill(Qt.black)
        p = QPainter(new)
        p.drawPixmap(0, 0, self.canvas)
        p.end()
        self.canvas = new

    def mousePressEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self.last_pos = e.pos()
            self.draw_stamp(e.pos())

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            dx = e.x() - self.last_pos.x()
            dy = e.y() - self.last_pos.y()
            dist = hypot(dx, dy)

            self.accum_dist += dist
            if self.accum_dist >= self.spacing:
                self.draw_stamp(e.pos())
                self.accum_dist = 0

            self.last_pos = e.pos()

    def draw_stamp(self, pos):
        p = QPainter(self.canvas)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)

        bw = self.brush.width()
        bh = self.brush.height()

        x = pos.x() - bw // 2
        y = pos.y() - bh // 2

        p.drawPixmap(x, y, self.brush)
        p.end()
        self.update()


# ---------------------------------------------------
# 主程式
# ---------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SprayCanvas()
    w.show()
    sys.exit(app.exec_())
