"""Draws trunk-and-branch style dendrons for vertically aligned keys."""

from PyQt5.QtGui import QPainterPath

from .point import Point


class TrunkDrawer:
    """Creates trunk-and-branch style dendron paths."""

    def __init__(self, arc_radius: float = 6.0):
        self.arc_radius = arc_radius

    def draw_trunk_with_branches(self, start: Point, key_points: list,
                                 shorten: float, go_right: bool = True) -> QPainterPath:
        """Draw vertical trunk with curved branches to each key corner."""
        if not key_points:
            return QPainterPath()
        path = QPainterPath()
        sorted_keys = sorted(key_points, key=lambda p: p.y)
        trunk_x = start.x
        path.moveTo(trunk_x, start.y)
        for key_point in sorted_keys:
            branch_y = key_point.y
            path.lineTo(trunk_x, branch_y)
            self._draw_branch_to_key(path, trunk_x, branch_y, key_point, shorten, go_right)
            path.moveTo(trunk_x, branch_y)
        return path

    def _draw_branch_to_key(self, path: QPainterPath, trunk_x: float, branch_y: float,
                            key_point: Point, shorten: float, go_right: bool):
        """Draw curved branch from trunk to key corner."""
        target_x = key_point.x + (shorten if go_right else -shorten)
        dx = target_x - trunk_x
        r = min(self.arc_radius, abs(dx) * 0.4)
        if go_right:
            self._draw_right_branch(path, trunk_x, branch_y, target_x, r)
        else:
            self._draw_left_branch(path, trunk_x, branch_y, target_x, r)

    def _draw_right_branch(self, path: QPainterPath, trunk_x: float, branch_y: float,
                           target_x: float, r: float):
        """Draw branch curving to the right."""
        path.lineTo(trunk_x, branch_y)
        path.quadTo(trunk_x, branch_y - r, trunk_x + r, branch_y - r)
        path.lineTo(target_x - r, branch_y - r)
        path.quadTo(target_x, branch_y - r, target_x, branch_y)

    def _draw_left_branch(self, path: QPainterPath, trunk_x: float, branch_y: float,
                          target_x: float, r: float):
        """Draw branch curving to the left."""
        path.lineTo(trunk_x, branch_y)
        path.quadTo(trunk_x, branch_y - r, trunk_x - r, branch_y - r)
        path.lineTo(target_x + r, branch_y - r)
        path.quadTo(target_x, branch_y - r, target_x, branch_y)
