# SPDX-License-Identifier: GPL-2.0-or-later

from widgets.connector_routing.waypoint_graph import WaypointGraph


class ConnectorRouter:
    """Routes connectors through gap graph from keys to combo labels."""

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.graph = WaypointGraph(key_rects, avg_key_size)

    def route(self, label_center, key_rect):
        """Find a path from label center to the key using graph traversal."""
        key_center = key_rect.center()
        entry_wp = self._find_entry_waypoint(key_rect)
        if entry_wp is None:
            return [key_center, label_center]
        exit_wp = self._find_exit_waypoint(label_center)
        path = [key_center, entry_wp.position]
        if exit_wp and exit_wp != entry_wp:
            graph_path = self._traverse_graph_to_target(entry_wp, exit_wp)
            path.extend(graph_path)
            if not graph_path or graph_path[-1] != exit_wp.position:
                path.append(exit_wp.position)
        else:
            graph_path = self._traverse_graph(entry_wp, label_center)
            path.extend(graph_path)
        path.append(label_center)
        return path

    def _find_exit_waypoint(self, label_center):
        """Find the best exit waypoint near the label."""
        candidates = self.graph.find_nearest_waypoints(label_center, count=5)
        for wp in candidates:
            if len(wp.neighbors) >= 2:
                return wp
        return candidates[0] if candidates else None

    def _find_entry_waypoint(self, key_rect):
        """Find the best entry waypoint adjacent to the key, preferring connected ones."""
        key_center = key_rect.center()
        margin = self.avg_key_size * 0.5
        nearby = []
        for wp in self.graph.waypoints:
            if self._is_waypoint_adjacent(wp, key_rect, margin):
                nearby.append(wp)
        if nearby:
            connected = [wp for wp in nearby if len(wp.neighbors) >= 2]
            if connected:
                return min(connected, key=lambda w: w.distance_to(key_center))
            return min(nearby, key=lambda w: (-len(w.neighbors), w.distance_to(key_center)))
        candidates = self.graph.find_nearest_waypoints(key_center, count=10)
        for wp in candidates:
            if not key_rect.contains(wp.position) and len(wp.neighbors) >= 2:
                return wp
        for wp in candidates:
            if not key_rect.contains(wp.position):
                return wp
        return None

    def _is_waypoint_adjacent(self, wp, rect, margin):
        """Check if waypoint is adjacent to the rectangle (close but not inside)."""
        expanded = rect.adjusted(-margin, -margin, margin, margin)
        if not expanded.contains(wp.position):
            return False
        if rect.contains(wp.position):
            return False
        return True

    def _traverse_graph(self, start_wp, destination):
        """Traverse the graph from start waypoint toward destination."""
        path = []
        visited = {start_wp}
        current = start_wp
        while True:
            next_wp = self._select_next_waypoint(current, destination, visited)
            if next_wp is None:
                break
            path.append(next_wp.position)
            visited.add(next_wp)
            current = next_wp
            if current.is_leaf():
                break
        return path

    def _traverse_graph_to_target(self, start_wp, target_wp):
        """Traverse the graph from start waypoint to target waypoint using BFS."""
        if start_wp == target_wp:
            return []
        from collections import deque
        queue = deque([(start_wp, [])])
        visited = {start_wp}
        while queue:
            current, path = queue.popleft()
            for neighbor in current.neighbors:
                if neighbor == target_wp:
                    return path + [neighbor.position]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor.position]))
        return self._traverse_graph(start_wp, target_wp.position)

    def _select_next_waypoint(self, current, destination, visited):
        """Select the next waypoint, preferring ones closer to destination."""
        current_dist = current.distance_to(destination)
        closer = []
        farther = []
        for neighbor in current.neighbors:
            if neighbor in visited:
                continue
            neighbor_dist = neighbor.distance_to(destination)
            if neighbor_dist < current_dist:
                closer.append((neighbor, neighbor_dist))
            else:
                farther.append((neighbor, neighbor_dist))
        if closer:
            closer.sort(key=lambda x: x[1])
            return closer[0][0]
        if farther:
            farther.sort(key=lambda x: x[1])
            return farther[0][0]
        return None

