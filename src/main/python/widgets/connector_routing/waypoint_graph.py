# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF
from widgets.connector_routing.waypoint import Waypoint


class WaypointGraph:
    """Builds a graph of waypoints from gaps between keys."""

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.waypoints = []
        self._build_waypoints()

    def _build_waypoints(self):
        """Generate waypoints from gaps between adjacent keys."""
        threshold = self.avg_key_size * 1.5
        for i, rect1 in enumerate(self.key_rects):
            for rect2 in self.key_rects[i + 1:]:
                gap_point = self._find_gap_center(rect1, rect2, threshold)
                if gap_point and not self._point_inside_key(gap_point):
                    self.waypoints.append(Waypoint(gap_point, "gap"))

    def _find_gap_center(self, rect1, rect2, threshold):
        """Find the center point between two adjacent key edges."""
        c1, c2 = rect1.center(), rect2.center()
        dist = math.hypot(c1.x() - c2.x(), c1.y() - c2.y())
        if dist > threshold:
            return None
        dx = abs(c1.x() - c2.x())
        dy = abs(c1.y() - c2.y())
        if dx > dy:
            edge1_x = rect1.right() if c1.x() < c2.x() else rect1.left()
            edge2_x = rect2.left() if c1.x() < c2.x() else rect2.right()
            return QPointF((edge1_x + edge2_x) / 2, (c1.y() + c2.y()) / 2)
        else:
            edge1_y = rect1.bottom() if c1.y() < c2.y() else rect1.top()
            edge2_y = rect2.top() if c1.y() < c2.y() else rect2.bottom()
            return QPointF((c1.x() + c2.x()) / 2, (edge1_y + edge2_y) / 2)

    def _point_inside_key(self, point):
        """Check if a point is inside any key rectangle."""
        for rect in self.key_rects:
            if rect.contains(point):
                return True
        return False

    def find_nearest_waypoints(self, point, count=5):
        """Find the nearest waypoints to a given point."""
        if not self.waypoints:
            return []
        sorted_wps = sorted(self.waypoints, key=lambda w: w.distance_to(point))
        return sorted_wps[:count]
