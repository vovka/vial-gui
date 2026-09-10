# SPDX-License-Identifier: GPL-2.0-or-later
"""A* pathfinder with direction state and bend penalties."""

import heapq
from typing import List, Tuple, Optional
from .routing_grid import RoutingGrid


class Pathfinder:
    """A* pathfinding with bend penalties for smoother routes."""

    DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Up, Right, Down, Left

    def __init__(self, bend_penalty: float = 5.0):
        self.bend_penalty = bend_penalty

    def find_path(
        self, grid: RoutingGrid, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Tuple[Optional[List[Tuple[int, int]]], float]:
        """Find path from start to goal. Returns (path, cost) or (None, inf)."""
        start = self._find_nearest_unblocked(grid, start)
        goal = self._find_nearest_unblocked(grid, goal)

        if start is None or goal is None:
            return self._direct_fallback(start or (0, 0), goal or (0, 0))

        return self._run_astar(grid, start, goal)

    def _find_nearest_unblocked(
        self, grid: RoutingGrid, pos: Tuple[int, int], max_radius: int = 20
    ) -> Optional[Tuple[int, int]]:
        """Find nearest unblocked cell using BFS spiral."""
        if not grid.is_blocked(*pos):
            return pos

        for radius in range(1, max_radius + 1):
            for dc in range(-radius, radius + 1):
                for dr in range(-radius, radius + 1):
                    if abs(dc) != radius and abs(dr) != radius:
                        continue
                    nc, nr = pos[0] + dc, pos[1] + dr
                    if not grid.is_blocked(nc, nr):
                        return (nc, nr)
        return None

    def _run_astar(
        self, grid: RoutingGrid, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Tuple[List[Tuple[int, int]], float]:
        """Run A* search."""
        open_set = []
        for d in range(4):
            h = self._heuristic(start, goal)
            heapq.heappush(open_set, (h, 0.0, start[0], start[1], d, None))

        came_from = {}
        g_score = {}

        while open_set:
            f, g, col, row, direction, parent = heapq.heappop(open_set)

            state = (col, row, direction)
            if state in g_score and g_score[state] <= g:
                continue
            g_score[state] = g
            came_from[state] = parent

            if (col, row) == goal:
                return self._reconstruct_path(came_from, state), g

            self._expand_neighbors(
                grid, col, row, direction, g, goal, open_set, g_score, state
            )

        return self._direct_fallback(start, goal)

    def _expand_neighbors(
        self, grid, col, row, direction, g, goal, open_set, g_score, state
    ):
        """Expand neighboring cells."""
        for d, (dc, dr) in enumerate(self.DIRECTIONS):
            nc, nr = col + dc, row + dr
            if grid.is_blocked(nc, nr):
                continue

            move_cost = grid.get_cost(nc, nr)
            if d != direction:
                move_cost += self.bend_penalty

            ng = g + move_cost
            ns = (nc, nr, d)
            if ns in g_score and g_score[ns] <= ng:
                continue

            h = self._heuristic((nc, nr), goal)
            heapq.heappush(open_set, (ng + h, ng, nc, nr, d, state))

    def _heuristic(self, pos: Tuple[int, int], goal: Tuple[int, int]) -> float:
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def _reconstruct_path(self, came_from, state) -> List[Tuple[int, int]]:
        """Reconstruct path from came_from dict."""
        path = []
        while state is not None:
            path.append((state[0], state[1]))
            state = came_from.get(state)
        path.reverse()
        return path

    def _direct_fallback(
        self, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Tuple[List[Tuple[int, int]], float]:
        """Fallback to direct line if A* fails."""
        return [start, goal], float('inf')
