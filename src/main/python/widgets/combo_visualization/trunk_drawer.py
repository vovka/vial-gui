"""Draws trunk-and-branch style dendrons for vertically aligned keys."""

from PyQt5.QtGui import QPainterPath

from .point import Point


class TrunkDrawer:
    """Creates trunk-and-branch style dendron paths."""

    def __init__(self, arc_radius: float = 6.0):
        self.arc_radius = arc_radius

    def draw_trunk_with_branches(self, start: Point, key_points: list,
                                 shorten: float, go_right: bool = True) -> QPainterPath:
        """Draw vertical trunk with horizontal branches to each key."""
        if not key_points:
            return QPainterPath()
        path = QPainterPath()
        sorted_keys = sorted(key_points, key=lambda p: p.y)
        trunk_x = start.x
        path.moveTo(trunk_x, start.y)

        for key_point in sorted_keys:
            path.lineTo(trunk_x, key_point.y)
            target_x = key_point.x + (shorten if go_right else -shorten)
            self._draw_branch(path, trunk_x, key_point.y, target_x, go_right)
            path.moveTo(trunk_x, key_point.y)
        return path

    def _draw_branch(self, path: QPainterPath, trunk_x: float, y: float,
                     target_x: float, go_right: bool):
        """Draw horizontal branch with curved corners ending in a curl."""
        branch_length = abs(trunk_x - target_x)
        r = min(self.arc_radius, branch_length * 0.3)
        curl_r = min(self.arc_radius, branch_length * 0.2)
        if go_right:
            # Trunk is on right, branch goes left to key corner
            # Curve from trunk going up-left
            path.quadTo(trunk_x, y - r, trunk_x - r, y - r)
            # Horizontal line toward key
            path.lineTo(target_x + curl_r, y - r)
            # Final curl down to key corner (y is the top edge of key)
            path.quadTo(target_x, y - r, target_x, y)
        else:
            # Trunk is on left, branch goes right to key corner
            path.quadTo(trunk_x, y - r, trunk_x + r, y - r)
            path.lineTo(target_x - curl_r, y - r)
            path.quadTo(target_x, y - r, target_x, y)
