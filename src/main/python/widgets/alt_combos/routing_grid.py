# SPDX-License-Identifier: GPL-2.0-or-later
"""Routing grid with gap-preference costs for pathfinding."""

from typing import List, Tuple, Optional
from PyQt5.QtCore import QRectF, QPointF


class RoutingGrid:
    """Grid for A* routing that prefers gaps between keys."""

    BLOCKED = 1000.0
    NEAR_KEY_COST = 10.0
    BASE_COST = 1.0

    def __init__(self, boundary: QRectF, cell_size: float = 4.0):
        self.boundary = boundary
        self.cell_size = cell_size
        self.cols = max(1, int(boundary.width() / cell_size) + 1)
        self.rows = max(1, int(boundary.height() / cell_size) + 1)
        self.costs = [[self.BASE_COST] * self.cols for _ in range(self.rows)]
        self.used_cells = set()

    def mark_obstacles(self, key_rects: List[QRectF], padding: float = 2.0):
        """Mark key cells as blocked and nearby cells as higher cost."""
        for rect in key_rects:
            self._mark_rect_blocked(rect)
            self._mark_rect_edges(rect, padding)

    def _mark_rect_blocked(self, rect: QRectF):
        """Mark cells inside rectangle as blocked."""
        min_col, min_row = self.world_to_grid(rect.topLeft())
        max_col, max_row = self.world_to_grid(rect.bottomRight())

        for r in range(max(0, min_row), min(self.rows, max_row + 1)):
            for c in range(max(0, min_col), min(self.cols, max_col + 1)):
                self.costs[r][c] = self.BLOCKED

    def _mark_rect_edges(self, rect: QRectF, padding: float):
        """Mark cells near rectangle edges as higher cost."""
        expanded = rect.adjusted(-padding, -padding, padding, padding)
        min_col, min_row = self.world_to_grid(expanded.topLeft())
        max_col, max_row = self.world_to_grid(expanded.bottomRight())

        for r in range(max(0, min_row), min(self.rows, max_row + 1)):
            for c in range(max(0, min_col), min(self.cols, max_col + 1)):
                if self.costs[r][c] < self.BLOCKED:
                    self.costs[r][c] = max(self.costs[r][c], self.NEAR_KEY_COST)

    def world_to_grid(self, point: QPointF) -> Tuple[int, int]:
        """Convert world coordinates to grid cell."""
        col = int((point.x() - self.boundary.left()) / self.cell_size)
        row = int((point.y() - self.boundary.top()) / self.cell_size)
        return (col, row)

    def grid_to_world(self, col: int, row: int) -> QPointF:
        """Convert grid cell to world coordinates (cell center)."""
        x = self.boundary.left() + (col + 0.5) * self.cell_size
        y = self.boundary.top() + (row + 0.5) * self.cell_size
        return QPointF(x, y)

    def get_cost(self, col: int, row: int) -> float:
        """Get cost for a cell, including congestion from used paths."""
        if not self._in_bounds(col, row):
            return self.BLOCKED
        base = self.costs[row][col]
        if (col, row) in self.used_cells:
            base += 5.0
        return base

    def mark_used(self, path: List[Tuple[int, int]]):
        """Mark cells as used by a routed path."""
        for cell in path:
            self.used_cells.add(cell)

    def _in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def is_blocked(self, col: int, row: int) -> bool:
        """Check if a cell is blocked."""
        return self.get_cost(col, row) >= self.BLOCKED
