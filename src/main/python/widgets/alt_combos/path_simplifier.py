# SPDX-License-Identifier: GPL-2.0-or-later
"""Simplifies grid paths to clean polylines with minimal segments."""

from typing import List, Tuple
from PyQt5.QtCore import QPointF
from .routing_grid import RoutingGrid


class PathSimplifier:
    """Converts grid paths to simplified world-coordinate polylines."""

    def simplify(
        self, grid: RoutingGrid, path: List[Tuple[int, int]]
    ) -> List[QPointF]:
        """Simplify path by removing collinear points."""
        if len(path) < 2:
            return [grid.grid_to_world(*p) for p in path]

        simplified_grid = self._remove_collinear(path)
        return [grid.grid_to_world(*p) for p in simplified_grid]

    def _remove_collinear(
        self, path: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """Remove collinear intermediate points."""
        if len(path) <= 2:
            return path

        result = [path[0]]

        for i in range(1, len(path) - 1):
            if not self._is_collinear(path[i - 1], path[i], path[i + 1]):
                result.append(path[i])

        result.append(path[-1])
        return result

    def _is_collinear(
        self, p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int]
    ) -> bool:
        """Check if three points are collinear."""
        dx1 = p2[0] - p1[0]
        dy1 = p2[1] - p1[1]
        dx2 = p3[0] - p2[0]
        dy2 = p3[1] - p2[1]

        if dx1 == 0 and dx2 == 0:
            return True
        if dy1 == 0 and dy2 == 0:
            return True
        return False
