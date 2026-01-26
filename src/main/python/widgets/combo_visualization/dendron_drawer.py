"""Draws dendron paths connecting combo boxes to trigger keys."""

from math import copysign
from PyQt5.QtGui import QPainterPath

from .point import Point


class DendronDrawer:
    """Creates QPainterPath dendrons (connecting lines) for combos."""

    def __init__(self, arc_radius: float = 6.0):
        self.arc_radius = arc_radius

    def draw_arc_dendron(self, start: Point, end: Point, x_first: bool,
                         shorten: float, arc_scale: float = 1.0) -> QPainterPath:
        """Draw L-shaped path with rounded corner from start to end."""
        diff = end - start
        if self._is_too_close_for_arc(diff, x_first):
            return self.draw_line_dendron(start, end, shorten)
        return self._create_arc_path(start, diff, x_first, shorten, arc_scale)

    def draw_line_dendron(self, start: Point, end: Point,
                          shorten: float) -> QPainterPath:
        """Draw straight line from start to end, shortened by shorten amount."""
        diff = end - start
        magnitude = abs(diff)
        if shorten and shorten < magnitude:
            diff = diff * (1 - shorten / magnitude)
        return self._create_line_path(start, diff)

    def _is_too_close_for_arc(self, diff: Point, x_first: bool) -> bool:
        """Check if points are too close to draw an arc."""
        if x_first:
            return abs(diff.x) < self.arc_radius
        return abs(diff.y) < self.arc_radius

    def _create_arc_path(self, start: Point, diff: Point, x_first: bool,
                         shorten: float, arc_scale: float) -> QPainterPath:
        """Create the arc dendron path."""
        path = QPainterPath()
        path.moveTo(start.x, start.y)

        arc_x = copysign(self.arc_radius, diff.x)
        arc_y = copysign(self.arc_radius, diff.y)
        clockwise = (diff.x > 0) ^ (diff.y > 0)

        if x_first:
            self._add_horizontal_first_arc(path, diff, arc_x, arc_y,
                                           shorten, arc_scale, not clockwise)
        else:
            self._add_vertical_first_arc(path, diff, arc_x, arc_y,
                                         shorten, arc_scale, clockwise)
        return path

    def _add_horizontal_first_arc(self, path: QPainterPath, diff: Point,
                                  arc_x: float, arc_y: float, shorten: float,
                                  arc_scale: float, clockwise: bool):
        """Add horizontal line, arc, then vertical line to path."""
        h_length = arc_scale * diff.x - arc_x
        v_length = diff.y - arc_y - copysign(shorten, diff.y)
        path.lineTo(path.currentPosition().x() + h_length,
                    path.currentPosition().y())
        self._add_arc_segment(path, arc_x, arc_y, clockwise)
        path.lineTo(path.currentPosition().x(),
                    path.currentPosition().y() + v_length)

    def _add_vertical_first_arc(self, path: QPainterPath, diff: Point,
                                arc_x: float, arc_y: float, shorten: float,
                                arc_scale: float, clockwise: bool):
        """Add vertical line, arc, then horizontal line to path."""
        v_length = arc_scale * diff.y - arc_y
        h_length = diff.x - arc_x - copysign(shorten, diff.x)
        path.lineTo(path.currentPosition().x(),
                    path.currentPosition().y() + v_length)
        self._add_arc_segment(path, arc_x, arc_y, clockwise)
        path.lineTo(path.currentPosition().x() + h_length,
                    path.currentPosition().y())

    def _add_arc_segment(self, path: QPainterPath, arc_x: float,
                         arc_y: float, clockwise: bool):
        """Add quadratic bezier curve approximating an arc."""
        current = path.currentPosition()
        end_x = current.x() + arc_x
        end_y = current.y() + arc_y
        ctrl_x = current.x() if abs(arc_y) > abs(arc_x) * 0.5 else end_x
        ctrl_y = current.y() if abs(arc_x) > abs(arc_y) * 0.5 else end_y
        if clockwise:
            ctrl_x = end_x if ctrl_x == current.x() else current.x()
            ctrl_y = end_y if ctrl_y == current.y() else current.y()
        path.quadTo(ctrl_x, ctrl_y, end_x, end_y)

    def _create_line_path(self, start: Point, diff: Point) -> QPainterPath:
        """Create a simple line path."""
        path = QPainterPath()
        path.moveTo(start.x, start.y)
        path.lineTo(start.x + diff.x, start.y + diff.y)
        return path
