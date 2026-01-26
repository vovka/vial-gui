"""Arc-style dendron routing for combo visualization."""

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainterPath

ARC_RADIUS = 6.0


class ComboLineRouter:
    """Routes arc-style dendrons between combo labels and keys."""

    def __init__(self, obstacles, avg_size):
        self.obstacles = obstacles
        self.avg_size = avg_size
        self.arc_radius = min(ARC_RADIUS, avg_size * 0.12)

    def create_path(self, start, end, combo_key_rects, alignment):
        """Create a smooth arc path from start to end."""
        path = QPainterPath()
        path.moveTo(start)

        dx = end.x() - start.x()
        dy = end.y() - start.y()

        if abs(dx) < 0.1 and abs(dy) < 0.1:
            return path

        if abs(dx) < self.arc_radius * 2 or abs(dy) < self.arc_radius * 2:
            path.lineTo(end)
            return path

        self._draw_arc_curve(path, start, end, alignment)
        return path

    def _draw_arc_curve(self, path, start, end, alignment):
        """Draw a smooth cubic curve biased by alignment."""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        control = self.arc_radius * 3

        if alignment in ('top', 'bottom'):
            mid_y = (start.y() + end.y()) / 2.0
            y_sign = 1 if dy >= 0 else -1
            offset = QPointF(0.0, control * y_sign)
            ctrl1 = QPointF(start.x(), mid_y) + offset
            ctrl2 = QPointF(end.x(), mid_y) + offset
        else:
            mid_x = (start.x() + end.x()) / 2.0
            x_sign = 1 if dx >= 0 else -1
            offset = QPointF(control * x_sign, 0.0)
            ctrl1 = QPointF(mid_x, start.y()) + offset
            ctrl2 = QPointF(mid_x, end.y()) + offset

        path.cubicTo(ctrl1, ctrl2, end)
