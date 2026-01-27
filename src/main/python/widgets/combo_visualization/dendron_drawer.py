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

    def draw_line_dendron(self, start: Point, end: Point, shorten: float) -> QPainterPath:
        """Draw straight line from start to end, shortened by shorten amount."""
        diff = end - start
        magnitude = abs(diff)
        if shorten and shorten < magnitude:
            diff = diff * (1 - shorten / magnitude)
        return self._create_line_path(start, diff)

    def _is_too_close_for_arc(self, diff: Point, x_first: bool) -> bool:
        """Check if points are too close to draw an arc."""
        return abs(diff.x) < self.arc_radius if x_first else abs(diff.y) < self.arc_radius

    def _create_arc_path(self, start: Point, diff: Point, x_first: bool,
                         shorten: float, arc_scale: float) -> QPainterPath:
        """Create the arc dendron path."""
        path = QPainterPath()
        path.moveTo(start.x, start.y)
        arc_x = copysign(self.arc_radius, diff.x)
        arc_y = copysign(self.arc_radius, diff.y)
        clockwise = (diff.x > 0) ^ (diff.y > 0)
        if x_first:
            self._add_horizontal_first_arc(path, diff, arc_x, arc_y, shorten, arc_scale, not clockwise)
        else:
            self._add_vertical_first_arc(path, diff, arc_x, arc_y, shorten, arc_scale, clockwise)
        return path

    def _add_horizontal_first_arc(self, path: QPainterPath, diff: Point,
                                  arc_x: float, arc_y: float, shorten: float,
                                  arc_scale: float, clockwise: bool):
        """Add horizontal line, arc, then vertical line to path."""
        h_len = arc_scale * diff.x - arc_x
        v_len = diff.y - arc_y - copysign(shorten, diff.y)
        path.lineTo(path.currentPosition().x() + h_len, path.currentPosition().y())
        self._add_arc_segment(path, arc_x, arc_y, clockwise)
        path.lineTo(path.currentPosition().x(), path.currentPosition().y() + v_len)

    def _add_vertical_first_arc(self, path: QPainterPath, diff: Point,
                                arc_x: float, arc_y: float, shorten: float,
                                arc_scale: float, clockwise: bool):
        """Add vertical line, arc, then horizontal line to path."""
        v_len = arc_scale * diff.y - arc_y
        h_len = diff.x - arc_x - copysign(shorten, diff.x)
        path.lineTo(path.currentPosition().x(), path.currentPosition().y() + v_len)
        self._add_arc_segment(path, arc_x, arc_y, clockwise)
        path.lineTo(path.currentPosition().x() + h_len, path.currentPosition().y())

    def _add_arc_segment(self, path: QPainterPath, arc_x: float, arc_y: float, clockwise: bool):
        """Add quadratic bezier curve approximating an arc."""
        cur = path.currentPosition()
        end_x, end_y = cur.x() + arc_x, cur.y() + arc_y
        ctrl_x = cur.x() if abs(arc_y) > abs(arc_x) * 0.5 else end_x
        ctrl_y = cur.y() if abs(arc_x) > abs(arc_y) * 0.5 else end_y
        if clockwise:
            ctrl_x = end_x if ctrl_x == cur.x() else cur.x()
            ctrl_y = end_y if ctrl_y == cur.y() else cur.y()
        path.quadTo(ctrl_x, ctrl_y, end_x, end_y)

    def _create_line_path(self, start: Point, diff: Point) -> QPainterPath:
        """Create a simple line path."""
        path = QPainterPath()
        path.moveTo(start.x, start.y)
        path.lineTo(start.x + diff.x, start.y + diff.y)
        return path

    def draw_tree_dendron(self, start: Point, row_groups: list) -> QPainterPath:
        """Draw tree-structured dendron with vertical trunk and horizontal branches.

        row_groups is a list of (row_y, corners, centers) tuples sorted by y.
        Each row has branches that curve to their key corners.
        """
        if not row_groups:
            return QPainterPath()

        path = QPainterPath()
        path.moveTo(start.x, start.y)
        trunk_x = start.x

        for row_y, corners, centers in row_groups:
            # Draw vertical line down to this row
            path.lineTo(trunk_x, row_y)

            # Draw horizontal branches for each key in this row
            corners_with_centers = sorted(zip(corners, centers), key=lambda x: x[0].x)
            for corner, center in corners_with_centers:
                path.moveTo(trunk_x, row_y)
                self._draw_curved_branch(path, trunk_x, row_y, corner)
            # Return to trunk for next row
            path.moveTo(trunk_x, row_y)

        return path

    def draw_grouped_dendron(self, start: Point, key_corners: list,
                             key_centers: list) -> QPainterPath:
        """Draw dendron with shared path that splits with curves to multiple keys.

        This draws from start point down to the row, then branches horizontally
        to each key corner with a curved ending.
        """
        if not key_corners:
            return QPainterPath()

        path = QPainterPath()
        path.moveTo(start.x, start.y)

        # Determine the y-level where we branch (average of key corners y)
        branch_y = sum(c.y for c in key_corners) / len(key_corners)

        # Draw vertical line to the branching point
        path.lineTo(start.x, branch_y)

        # Sort corners by x to draw branches left to right
        corners_with_centers = sorted(zip(key_corners, key_centers), key=lambda x: x[0].x)

        for corner, center in corners_with_centers:
            path.moveTo(start.x, branch_y)
            self._draw_curved_branch(path, start.x, branch_y, corner)

        return path

    def _draw_curved_branch(self, path: QPainterPath, trunk_x: float, trunk_y: float,
                            corner: Point):
        """Draw horizontal branch with curved ending to key corner."""
        r = self.arc_radius
        dx = corner.x - trunk_x
        dy = corner.y - trunk_y

        if abs(dx) < r * 2:
            # Too close horizontally, just draw a curved line
            path.quadTo(corner.x, trunk_y, corner.x, corner.y)
            return

        # Draw horizontal line toward the key, stopping before the curve
        if dx > 0:
            mid_x = corner.x - r
        else:
            mid_x = corner.x + r

        path.lineTo(mid_x, trunk_y)

        # Final curve bending toward the key corner
        # Use corner.x as control x, trunk_y as control y for smooth curve
        path.quadTo(corner.x, trunk_y, corner.x, corner.y)
