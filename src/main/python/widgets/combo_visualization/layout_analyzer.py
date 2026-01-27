"""Keyboard layout analysis for combo visualization."""

import math


class ComboLayoutAnalyzer:
    """Analyzes keyboard layout for split detection and key clustering."""

    def __init__(self, key_rects):
        self.key_rects = key_rects
        self.keyboard_center = self._compute_center()
        self.split_gap = self._detect_split_gap()

    def _compute_center(self):
        """Compute the center X coordinate of the keyboard."""
        if not self.key_rects:
            return 0
        min_x = min(r.left() for r in self.key_rects)
        max_x = max(r.right() for r in self.key_rects)
        return (min_x + max_x) / 2

    def _detect_split_gap(self):
        """Detect gap between split keyboard halves."""
        if not self.key_rects:
            return None

        left = [r for r in self.key_rects if r.center().x() < self.keyboard_center]
        right = [r for r in self.key_rects if r.center().x() >= self.keyboard_center]

        if not left or not right:
            return None

        left_edge = max(r.right() for r in left)
        right_edge = min(r.left() for r in right)
        avg_width = sum(r.width() for r in self.key_rects) / len(self.key_rects)

        if right_edge - left_edge > avg_width * 0.5:
            return (left_edge, right_edge)
        return None

    def are_keys_adjacent(self, centers, threshold):
        """Check if all key centers form a connected cluster."""
        if len(centers) <= 1:
            return True

        visited = {0}
        stack = [0]
        while stack:
            i = stack.pop()
            for j in range(len(centers)):
                if j in visited:
                    continue
                dist = math.hypot(
                    centers[i].x() - centers[j].x(),
                    centers[i].y() - centers[j].y()
                )
                if dist <= threshold:
                    visited.add(j)
                    stack.append(j)
        return len(visited) == len(centers)
