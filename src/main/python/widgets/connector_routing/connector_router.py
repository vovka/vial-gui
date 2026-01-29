# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF
from widgets.connector_routing.geometry_utils import GeometryUtils


class ConnectorRouter:
    """Routes connectors through intersections along the direct path."""

    def __init__(self, key_rects, avg_key_size, gap_intersections=None):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.gap_intersections = gap_intersections or []
        self._max_distance = avg_key_size * 0.8  # Max distance from direct line

    def route(self, label_center, key_rect):
        """Find path from label to key through intersections along direct line."""
        key_point = self._find_key_connection_point(key_rect, label_center)

        if not self.gap_intersections:
            return [label_center, key_point]

        path = self._find_path_along_line(label_center, key_point, key_rect)
        return self._normalize_path(path)

    def _find_path_along_line(self, label_center, key_point, key_rect):
        """Find intersections close to the direct line and connect them."""
        # Find intersections close to the direct line from label to key
        nearby = self._find_intersections_near_line(label_center, key_point)

        if not nearby:
            return [label_center, key_point]

        # Sort by distance from label along the line direction
        nearby_sorted = self._sort_along_line(nearby, label_center, key_point)

        # Filter to keep only intersections that don't cross keys when connected
        filtered = self._filter_connectable(nearby_sorted, key_rect)

        if not filtered:
            return [label_center, key_point]

        # Build path: label -> first intersection (straight) -> ... -> key
        path = [label_center]
        for intersection in filtered:
            path.append(intersection)
        path.append(key_point)

        return path

    def _find_intersections_near_line(self, p1, p2):
        """Find intersections within max_distance of the line from p1 to p2."""
        result = []
        for intersection in self.gap_intersections:
            dist = self._point_to_line_distance(intersection, p1, p2)
            if dist <= self._max_distance:
                result.append(intersection)
        return result

    def _point_to_line_distance(self, point, line_start, line_end):
        """Calculate perpendicular distance from point to line segment."""
        dx = line_end.x() - line_start.x()
        dy = line_end.y() - line_start.y()
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            return GeometryUtils.distance(point, line_start)

        # Project point onto line
        t = max(0, min(1, ((point.x() - line_start.x()) * dx +
                          (point.y() - line_start.y()) * dy) / length_sq))

        proj_x = line_start.x() + t * dx
        proj_y = line_start.y() + t * dy

        return GeometryUtils.distance(point, QPointF(proj_x, proj_y))

    def _sort_along_line(self, intersections, line_start, line_end):
        """Sort intersections by their projection position along the line."""
        dx = line_end.x() - line_start.x()
        dy = line_end.y() - line_start.y()
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            return intersections

        def projection_t(p):
            return ((p.x() - line_start.x()) * dx +
                    (p.y() - line_start.y()) * dy) / length_sq

        return sorted(intersections, key=projection_t)

    def _filter_connectable(self, sorted_intersections, key_rect):
        """Keep only intersections where consecutive connections don't cross keys."""
        if not sorted_intersections:
            return []

        result = [sorted_intersections[0]]

        for i in range(1, len(sorted_intersections)):
            prev = result[-1]
            curr = sorted_intersections[i]
            # Only add if connection doesn't cross keys
            if not self._segment_crosses_keys(prev, curr, key_rect):
                result.append(curr)

        return result

    def _segment_crosses_keys(self, p1, p2, exclude_rect):
        """Check if segment crosses any key except excluded one."""
        for rect in self.key_rects:
            if rect == exclude_rect:
                continue
            if GeometryUtils.line_intersects_rect(p1, p2, rect):
                return True
        return False

    def _find_key_connection_point(self, key_rect, from_point):
        """Find the closest point on the key edge to connect to."""
        inset = min(key_rect.width(), key_rect.height()) * 0.25
        return self._closest_edge_point(key_rect, from_point, inset)

    def _closest_edge_point(self, rect, point, inset):
        """Find the closest point on rect edge, inset from corners."""
        cx, cy = rect.center().x(), rect.center().y()
        px, py = point.x(), point.y()
        left = rect.left() + inset
        right = rect.right() - inset
        top = rect.top() + inset
        bottom = rect.bottom() - inset
        candidates = []
        if py <= cy:
            candidates.append(QPointF(max(left, min(right, px)), rect.top()))
        if py >= cy:
            candidates.append(QPointF(max(left, min(right, px)), rect.bottom()))
        if px <= cx:
            candidates.append(QPointF(rect.left(), max(top, min(bottom, py))))
        if px >= cx:
            candidates.append(QPointF(rect.right(), max(top, min(bottom, py))))
        if not candidates:
            candidates.append(QPointF(cx, rect.top()))
        return min(candidates, key=lambda c: GeometryUtils.distance(c, point))

    def _normalize_path(self, points):
        """Remove duplicate and collinear points."""
        if not points:
            return points
        deduped = [points[0]]
        for pt in points[1:]:
            if GeometryUtils.distance(pt, deduped[-1]) > 0.01:
                deduped.append(pt)
        return deduped
