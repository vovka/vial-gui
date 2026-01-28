# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF
from widgets.connector_routing.waypoint_graph import WaypointGraph
from widgets.connector_routing.geometry_utils import GeometryUtils


class ConnectorRouter:
    """Routes connectors from labels to keys through gaps."""

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.graph = WaypointGraph(key_rects, avg_key_size)

    def route(self, label_center, key_rect):
        """Find a path from label center to the key."""
        key_point = self._find_key_connection_point(key_rect, label_center)
        if self._is_clear_path(label_center, key_point):
            return [label_center, key_point]
        path = self._find_path_through_gaps(label_center, key_point, key_rect)
        return path

    def _find_key_connection_point(self, key_rect, from_point):
        """Find the closest point on the key edge to connect to."""
        center = key_rect.center()
        dx = from_point.x() - center.x()
        dy = from_point.y() - center.y()
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return QPointF(key_rect.center().x(), key_rect.top())
        inset = min(key_rect.width(), key_rect.height()) * 0.25
        return self._closest_edge_point(key_rect, from_point, inset)

    def _closest_edge_point(self, rect, point, inset):
        """Find the closest point on rect edge, inset from corners."""
        cx, cy = rect.center().x(), rect.center().y()
        px, py = point.x(), point.y()
        left, right = rect.left() + inset, rect.right() - inset
        top, bottom = rect.top() + inset, rect.bottom() - inset
        candidates = self._build_edge_candidates(rect, px, py, cx, cy, left, right, top, bottom)
        if not candidates:
            candidates.append(QPointF(cx, rect.top()))
        return min(candidates, key=lambda c: GeometryUtils.distance(c, point))

    def _build_edge_candidates(self, rect, px, py, cx, cy, left, right, top, bottom):
        """Build list of candidate edge points."""
        candidates = []
        if py <= cy:
            candidates.append(QPointF(max(left, min(right, px)), rect.top()))
        if py >= cy:
            candidates.append(QPointF(max(left, min(right, px)), rect.bottom()))
        if px <= cx:
            candidates.append(QPointF(rect.left(), max(top, min(bottom, py))))
        if px >= cx:
            candidates.append(QPointF(rect.right(), max(top, min(bottom, py))))
        return candidates

    def _is_clear_path(self, start, end):
        """Check if straight path between two points crosses any key."""
        for rect in self.key_rects:
            if GeometryUtils.line_intersects_rect(start, end, rect):
                return False
        return True

    def _find_path_through_gaps(self, start, end, target_key_rect):
        """Find a path from start to end through gap waypoints."""
        if not self.graph.waypoints:
            return [start, end]
        best_wp = self._find_best_waypoint(start, end, target_key_rect)
        if best_wp is None:
            return [start, end]
        wp_pos = best_wp.position
        if self._is_clear_path(start, wp_pos) and \
           self._is_clear_path_to_key(wp_pos, end, target_key_rect):
            return [start, wp_pos, end]
        return [start, end]

    def _find_best_waypoint(self, start, end, target_key_rect):
        """Find the best waypoint to route through."""
        best, best_cost = None, float('inf')
        for wp in self.graph.waypoints:
            pos = wp.position
            if target_key_rect.contains(pos):
                continue
            cost = self._evaluate_waypoint(start, end, pos, target_key_rect)
            if cost is not None and cost < best_cost:
                best_cost, best = cost, wp
        return best

    def _evaluate_waypoint(self, start, end, pos, target_key_rect):
        """Evaluate waypoint cost, return None if invalid."""
        d1 = GeometryUtils.distance(start, pos)
        d2 = GeometryUtils.distance(pos, end)
        direct = GeometryUtils.distance(start, end)
        if (d1 + d2) - direct > self.avg_key_size * 2:
            return None
        if not self._is_clear_path(start, pos):
            return None
        if not self._is_clear_path_to_key(pos, end, target_key_rect):
            return None
        return d1 + d2

    def _is_clear_path_to_key(self, start, end, target_key_rect):
        """Check if path to key is clear (ignoring the target key)."""
        for rect in self.key_rects:
            if rect == target_key_rect:
                continue
            if GeometryUtils.line_intersects_rect(start, end, rect):
                return False
        return True
