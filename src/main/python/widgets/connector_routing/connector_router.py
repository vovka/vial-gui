# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF
from widgets.connector_routing.waypoint_graph import WaypointGraph
from widgets.connector_routing.geometry_utils import GeometryUtils


class ConnectorRouter:
    """Routes connectors using orthogonal (horizontal/vertical) paths."""

    MAX_WAYPOINTS_TO_CHECK = 15  # Only check nearest waypoints

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.graph = WaypointGraph(key_rects, avg_key_size)

    def route(self, label_center, key_rect):
        """Find an orthogonal path from label center to the key."""
        key_waypoint = self._nearest_waypoint_to_key(key_rect)
        key_anchor = key_waypoint if key_waypoint is not None else label_center
        key_point = self._find_key_connection_point(key_rect, key_anchor)
        if key_waypoint is not None:
            path_to_gap = self._build_orthogonal_path(label_center, key_waypoint, key_rect)
            path_from_gap = self._normalize_path([key_waypoint, key_point])
            return self._normalize_path(path_to_gap[:-1] + path_from_gap)
        return self._build_orthogonal_path(label_center, key_point, key_rect)

    def _find_key_connection_point(self, key_rect, from_point):
        """Find the closest point on the key edge to connect to."""
        inset = min(key_rect.width(), key_rect.height()) * 0.25
        return self._closest_edge_point(key_rect, from_point, inset)

    def _closest_edge_point(self, rect, point, inset):
        """Find the closest point on rect edge, inset from corners."""
        cx, cy = rect.center().x(), rect.center().y()
        px, py = point.x(), point.y()
        left, right = rect.left() + inset, rect.right() - inset
        top, bottom = rect.top() + inset, rect.bottom() - inset
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

    def _build_orthogonal_path(self, start, end, target_key_rect):
        """Build an L-shaped or routed orthogonal path."""
        # Try simple L-shapes first (fast path)
        corner1 = QPointF(end.x(), start.y())
        corner2 = QPointF(start.x(), end.y())
        candidates = [
            self._normalize_path([start, corner1, end]),
            self._normalize_path([start, corner2, end]),
        ]
        candidates.extend(self._routed_path_candidates(start, end))
        zero_crossings = [path for path in candidates if self._path_cost(path, target_key_rect) == 0]
        if zero_crossings:
            return min(zero_crossings, key=lambda path: self._path_score(path, target_key_rect))
        best = min(candidates, key=lambda path: self._path_score(path, target_key_rect))
        return best

    def _path_crosses_keys(self, path, target_key_rect):
        """Quick check if path crosses any key (excluding target)."""
        for i in range(len(path) - 1):
            if self._segment_crosses_any_key(path[i], path[i + 1], target_key_rect):
                return True
        return False

    def _segment_crosses_any_key(self, p1, p2, target_key_rect):
        """Check if segment crosses any key (excluding target)."""
        for rect in self.key_rects:
            if rect == target_key_rect:
                continue
            if GeometryUtils.line_intersects_rect(p1, p2, rect):
                return True
        return False

    def _path_cost(self, path, target_key_rect):
        """Calculate how many keys a path crosses (excluding target)."""
        cost = 0
        for i in range(len(path) - 1):
            cost += self._segment_crossings(path[i], path[i + 1], target_key_rect)
        return cost

    def _path_score(self, path, target_key_rect):
        crossings = self._path_cost(path, target_key_rect)
        length = self._path_length(path)
        return (crossings, length, len(path))

    def _path_length(self, path):
        if len(path) < 2:
            return 0.0
        length = 0.0
        for i in range(len(path) - 1):
            length += GeometryUtils.distance(path[i], path[i + 1])
        return length

    def _segment_crossings(self, p1, p2, target_key_rect):
        """Count how many keys a segment crosses."""
        count = 0
        for rect in self.key_rects:
            if rect == target_key_rect:
                continue
            if GeometryUtils.line_intersects_rect(p1, p2, rect):
                count += 1
        return count

    def _routed_path_candidates(self, start, end):
        """Build candidate paths through gap waypoints."""
        candidates = []
        waypoint_positions = self._candidate_waypoints(start, end)
        for pos in waypoint_positions:
            for path in self._waypoint_path_variants(start, end, pos):
                candidates.append(self._normalize_path(path))
        start_wps = self._nearest_waypoint_positions(start)
        end_wps = self._nearest_waypoint_positions(end)
        for wp1 in start_wps:
            for wp2 in end_wps:
                if wp1 == wp2:
                    continue
                for path in self._two_waypoint_paths(start, end, wp1, wp2):
                    candidates.append(self._normalize_path(path))
        return candidates

    def _candidate_waypoints(self, start, end):
        wps = []
        for wp in self.graph.find_nearest_waypoints(start, count=8):
            wps.append(wp)
        for wp in self.graph.find_nearest_waypoints(end, count=8):
            wps.append(wp)
        seen = set()
        filtered = []
        for wp in wps:
            pos = wp.position
            key = (round(pos.x(), 2), round(pos.y(), 2))
            if key in seen:
                continue
            seen.add(key)
            filtered.append(pos)
        return filtered

    def _nearest_waypoint_to_key(self, key_rect):
        key_center = key_rect.center()
        perimeter = self.graph.find_nearest_waypoints(key_center, count=6, kind="perimeter")
        gap = self.graph.find_nearest_waypoints(key_center, count=6, kind="gap")
        corridor = self.graph.find_nearest_waypoints(key_center, count=6, kind="corridor")
        candidates = perimeter + gap + corridor
        if not candidates:
            return None
        for wp in candidates:
            if not key_rect.contains(wp.position):
                return wp.position
        return None

    def _nearest_waypoint_positions(self, point, max_count=4):
        return [wp.position for wp in self.graph.find_nearest_waypoints(point, count=max_count)]

    def _waypoint_path_variants(self, start, end, waypoint):
        """Generate different orthogonal path variants through waypoint."""
        mid_x, mid_y = waypoint.x(), waypoint.y()
        return [
            [start, QPointF(mid_x, start.y()), QPointF(mid_x, end.y()), end],
            [start, QPointF(start.x(), mid_y), QPointF(end.x(), mid_y), end],
            [start, QPointF(mid_x, start.y()), waypoint, QPointF(mid_x, end.y()), end],
            [start, QPointF(start.x(), mid_y), waypoint, QPointF(end.x(), mid_y), end],
        ]

    def _two_waypoint_paths(self, start, end, wp1, wp2):
        return [
            [
                start,
                QPointF(wp1.x(), start.y()),
                wp1,
                QPointF(wp1.x(), wp2.y()),
                wp2,
                QPointF(end.x(), wp2.y()),
                end,
            ],
            [
                start,
                QPointF(start.x(), wp1.y()),
                wp1,
                QPointF(wp2.x(), wp1.y()),
                wp2,
                QPointF(wp2.x(), end.y()),
                end,
            ],
        ]

    def _normalize_path(self, points):
        if not points:
            return points
        deduped = [points[0]]
        for pt in points[1:]:
            if GeometryUtils.distance(pt, deduped[-1]) > 0.01:
                deduped.append(pt)
        if len(deduped) < 3:
            return deduped
        simplified = [deduped[0]]
        for i in range(1, len(deduped) - 1):
            prev_pt = simplified[-1]
            curr_pt = deduped[i]
            next_pt = deduped[i + 1]
            if (abs(prev_pt.x() - curr_pt.x()) < 0.01 and abs(curr_pt.x() - next_pt.x()) < 0.01) or \
               (abs(prev_pt.y() - curr_pt.y()) < 0.01 and abs(curr_pt.y() - next_pt.y()) < 0.01):
                continue
            simplified.append(curr_pt)
        simplified.append(deduped[-1])
        return simplified
