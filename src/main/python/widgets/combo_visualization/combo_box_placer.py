"""Calculates combo box placement relative to trigger keys."""

from enum import Enum
from typing import List, Tuple

from .point import Point


class Alignment(Enum):
    """Combo box alignment relative to trigger keys."""
    MID = "mid"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class ComboBoxPlacer:
    """Determines optimal combo box placement."""

    def __init__(self, offset: float = 0.5, adjacency_threshold: float = 1.7):
        self.offset = offset
        self.adjacency_threshold = adjacency_threshold

    def compute_placement(self, key_centers: List[Point], key_sizes: List[float],
                          box_width: float, box_height: float) -> Tuple[Point, Alignment]:
        """Compute combo box position and alignment."""
        if not key_centers:
            return Point(0, 0), Alignment.MID

        centroid = self._compute_centroid(key_centers)
        avg_size = sum(key_sizes) / len(key_sizes)
        adjacent = self._are_keys_adjacent(key_centers, avg_size)

        if adjacent:
            return centroid, Alignment.MID
        return self._compute_external_placement(key_centers, centroid,
                                                avg_size, box_height)

    def _compute_centroid(self, points: List[Point]) -> Point:
        """Calculate centroid of all points."""
        if not points:
            return Point(0, 0)
        total = Point(0, 0)
        for p in points:
            total = total + p
        return total / len(points)

    def _are_keys_adjacent(self, centers: List[Point], avg_size: float) -> bool:
        """Check if all keys form a connected group."""
        if len(centers) <= 1:
            return True
        threshold = avg_size * self.adjacency_threshold
        return self._check_connectivity(centers, threshold)

    def _check_connectivity(self, centers: List[Point], threshold: float) -> bool:
        """Use flood-fill to check if all points are connected."""
        visited = {0}
        stack = [0]
        while stack:
            i = stack.pop()
            for j in range(len(centers)):
                if j not in visited and abs(centers[i] - centers[j]) <= threshold:
                    visited.add(j)
                    stack.append(j)
        return len(visited) == len(centers)

    def _compute_external_placement(self, centers: List[Point], centroid: Point,
                                    avg_size: float, box_height: float) -> Tuple[Point, Alignment]:
        """Compute placement outside the key group."""
        min_y = min(p.y for p in centers)
        gap = avg_size * self.offset
        pos = Point(centroid.x, min_y - gap - box_height / 2)
        return pos, Alignment.TOP

    def get_key_offset(self, alignment: Alignment, key_size: float,
                       combo_pos: Point, key_pos: Point,
                       box_width: float, box_height: float) -> float:
        """Calculate how much to shorten dendron to avoid overlapping key."""
        if alignment in (Alignment.TOP, Alignment.BOTTOM):
            dx = abs(key_pos.x - combo_pos.x)
            dy = abs(key_pos.y - combo_pos.y)
            if dx < box_width / 2 and dy <= key_size / 3 + box_height / 2:
                return key_size / 5
            return key_size / 3
        if alignment in (Alignment.LEFT, Alignment.RIGHT):
            dx = abs(key_pos.x - combo_pos.x)
            dy = abs(key_pos.y - combo_pos.y)
            if dy < box_height / 2 and dx <= key_size / 3 + box_width / 2:
                return key_size / 5
            return key_size / 3
        return key_size / 3

    def should_draw_dendron(self, alignment: Alignment, combo_pos: Point,
                            key_pos: Point, key_size: float) -> bool:
        """Determine if dendron should be drawn for this key."""
        if alignment != Alignment.MID:
            return True
        distance = abs(key_pos - combo_pos)
        return distance >= key_size - 1
