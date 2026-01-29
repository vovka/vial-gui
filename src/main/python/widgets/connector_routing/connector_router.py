# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF
from widgets.connector_routing.geometry_utils import GeometryUtils


class ConnectorRouter:
    """Routes connectors using orthogonal paths through gap intersections."""

    def __init__(self, key_rects, avg_key_size, gap_intersections=None):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.gap_intersections = gap_intersections or []
        self._tolerance = avg_key_size * 0.25

    def route(self, label_center, key_rect):
        """Find an orthogonal path from label center to the key."""
        key_point = self._find_key_connection_point(key_rect, label_center)
        if not self.gap_intersections:
            return self._build_simple_path(label_center, key_point, key_rect)
        path = self._find_path_through_intersections(label_center, key_point, key_rect)
        return self._normalize_path(path)

    def _find_path_through_intersections(self, start, end, target_key_rect):
        """Find path from start to end through gap intersection points."""
        simple_path = self._build_simple_path(start, end, target_key_rect)
        simple_crossings = self._path_cost(simple_path, target_key_rect)
        waypoint_paths = []
        nearby_start = self._find_nearby_intersections(start, count=8)
        nearby_end = self._find_nearby_intersections(end, count=8)
        for wp in nearby_start + nearby_end:
            path = self._build_path_via_single_waypoint(start, end, wp)
            crossings = self._path_cost(path, target_key_rect)
            if crossings <= simple_crossings:
                waypoint_paths.append((path, crossings, self._path_length(path)))
        for wp_start in nearby_start[:4]:
            for wp_end in nearby_end[:4]:
                path = self._build_path_via_waypoints(start, end, wp_start, wp_end)
                crossings = self._path_cost(path, target_key_rect)
                if crossings <= simple_crossings:
                    waypoint_paths.append((path, crossings, self._path_length(path)))
        chain_path = self._find_chain_path(start, end, target_key_rect)
        if chain_path:
            crossings = self._path_cost(chain_path, target_key_rect)
            if crossings <= simple_crossings:
                waypoint_paths.append((chain_path, crossings, self._path_length(chain_path)))
        if waypoint_paths:
            waypoint_paths.sort(key=lambda x: (x[1], x[2]))
            return waypoint_paths[0][0]
        return simple_path

    def _find_chain_path(self, start, end, target_key_rect):
        """Find a path by chaining through aligned intersections."""
        if not self.gap_intersections:
            return None
        nearby_start = self._find_nearby_intersections(start, count=6)
        nearby_end = self._find_nearby_intersections(end, count=6)
        if not nearby_start:
            return None
        best_chain = None
        best_score = None
        for first_wp in nearby_start:
            for last_wp in nearby_end:
                chain = self._find_chain_between(first_wp, last_wp, max_depth=5)
                if not chain:
                    continue
                path = self._build_orthogonal_chain(start, chain, end)
                score = self._path_score(path, target_key_rect)
                if best_score is None or score < best_score:
                    best_score = score
                    best_chain = path
        return best_chain

    def _find_chain_between(self, start_wp, end_wp, max_depth):
        """Find a chain of waypoints from start_wp to end_wp."""
        if self._point_key(start_wp) == self._point_key(end_wp):
            return [start_wp]
        chain = [start_wp]
        current = start_wp
        visited = {self._point_key(start_wp)}
        target = end_wp
        for _ in range(max_depth):
            if GeometryUtils.distance(current, target) < self._tolerance * 2:
                chain.append(target)
                break
            best_next = self._find_best_next_waypoint(current, target, visited)
            if best_next is None:
                break
            chain.append(best_next)
            visited.add(self._point_key(best_next))
            current = best_next
        return chain if len(chain) > 1 else None

    def _find_best_next_waypoint(self, current, target, visited):
        """Find the best next waypoint moving toward target."""
        candidates = []
        for wp in self.gap_intersections:
            key = self._point_key(wp)
            if key in visited:
                continue
            if not self._is_good_step(current, wp, target):
                continue
            dist_to_target = GeometryUtils.distance(wp, target)
            candidates.append((wp, dist_to_target))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def _is_good_step(self, current, candidate, target):
        """Check if moving to candidate is a good step toward target."""
        current_dist = GeometryUtils.distance(current, target)
        candidate_dist = GeometryUtils.distance(candidate, target)
        return candidate_dist < current_dist

    def _build_orthogonal_chain(self, start, chain, end):
        """Build orthogonal path from start through chain waypoints to end."""
        if not chain:
            return self._build_simple_path(start, end, None)
        path = [start]
        for wp in chain:
            path.append(wp)
        path.append(end)
        return path

    def _point_key(self, p):
        """Create a hashable key for a point."""
        return (round(p.x(), 1), round(p.y(), 1))

    def _find_nearby_intersections(self, point, count=5):
        """Find the nearest gap intersection points."""
        if not self.gap_intersections:
            return []
        sorted_points = sorted(
            self.gap_intersections,
            key=lambda p: GeometryUtils.distance(p, point)
        )
        return sorted_points[:count]

    def _build_path_via_waypoints(self, start, end, wp_start, wp_end):
        """Build path: start -> wp_start -> wp_end -> end."""
        if self._point_key(wp_start) == self._point_key(wp_end):
            return self._build_path_via_single_waypoint(start, end, wp_start)
        return [start, wp_start, wp_end, end]

    def _build_path_via_single_waypoint(self, start, end, waypoint):
        """Build path: start -> waypoint -> end."""
        return [start, waypoint, end]

    def _build_simple_path(self, start, end, target_key_rect):
        """Build a simple L-shaped path."""
        corner1 = QPointF(end.x(), start.y())
        corner2 = QPointF(start.x(), end.y())
        path1 = self._normalize_path([start, corner1, end])
        path2 = self._normalize_path([start, corner2, end])
        score1 = self._path_score(path1, target_key_rect)
        score2 = self._path_score(path2, target_key_rect)
        return path1 if score1 <= score2 else path2

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

    def _path_score(self, path, target_key_rect):
        """Score a path: (crossings, length, num_segments)."""
        crossings = self._path_cost(path, target_key_rect)
        length = self._path_length(path)
        return (crossings, length, len(path))

    def _path_cost(self, path, target_key_rect):
        """Calculate how many keys a path crosses (excluding target)."""
        cost = 0
        for i in range(len(path) - 1):
            cost += self._segment_crossings(path[i], path[i + 1], target_key_rect)
        return cost

    def _segment_crossings(self, p1, p2, target_key_rect):
        """Count how many keys a segment crosses."""
        count = 0
        for rect in self.key_rects:
            if rect == target_key_rect:
                continue
            if GeometryUtils.line_intersects_rect(p1, p2, rect):
                count += 1
        return count

    def _path_length(self, path):
        """Calculate total path length."""
        if len(path) < 2:
            return 0.0
        total = 0.0
        for i in range(len(path) - 1):
            total += GeometryUtils.distance(path[i], path[i + 1])
        return total

    def _normalize_path(self, points):
        """Remove duplicate points and collinear intermediate points."""
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
            same_x = abs(prev_pt.x() - curr_pt.x()) < 0.01 and \
                     abs(curr_pt.x() - next_pt.x()) < 0.01
            same_y = abs(prev_pt.y() - curr_pt.y()) < 0.01 and \
                     abs(curr_pt.y() - next_pt.y()) < 0.01
            if same_x or same_y:
                continue
            simplified.append(curr_pt)
        simplified.append(deduped[-1])
        return simplified
