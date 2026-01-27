"""Calculates combo box placement relative to trigger keys."""

from enum import Enum
from typing import List, Tuple, TYPE_CHECKING

from .point import Point

if TYPE_CHECKING:
    from .combo_data import KeyInfo


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

        if adjacent and not self._are_vertically_aligned(key_centers, avg_size):
            return centroid, Alignment.MID
        return self._compute_external_placement(key_centers, centroid, avg_size, box_height)

    def _are_vertically_aligned(self, centers: List[Point], avg_size: float) -> bool:
        """Check if keys are vertically stacked (small x-spread)."""
        if len(centers) < 2:
            return False
        xs = [p.x for p in centers]
        return (max(xs) - min(xs)) < avg_size * 0.8

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

    def get_closest_corner(self, combo_pos: Point, key_center: Point,
                           key_size: float) -> Point:
        """Get the corner of the key closest to the combo box position."""
        half = key_size / 2
        # Determine which corner is closest based on direction from combo to key
        dx = key_center.x - combo_pos.x
        dy = key_center.y - combo_pos.y
        # Choose corner on the side facing the combo box
        corner_x = key_center.x - half if dx > 0 else key_center.x + half
        corner_y = key_center.y - half if dy > 0 else key_center.y + half
        return Point(corner_x, corner_y)

    def group_keys_by_row(self, keys: List['KeyInfo'], threshold_ratio: float = 0.5) -> List[List['KeyInfo']]:
        """Group keys that are in similar horizontal rows."""
        if not keys:
            return []
        avg_size = sum(k.size for k in keys) / len(keys)
        threshold = avg_size * threshold_ratio

        # Sort by y-coordinate
        sorted_keys = sorted(keys, key=lambda k: k.center.y)
        groups = []
        current_group = [sorted_keys[0]]

        for key in sorted_keys[1:]:
            if abs(key.center.y - current_group[0].center.y) <= threshold:
                current_group.append(key)
            else:
                groups.append(current_group)
                current_group = [key]
        groups.append(current_group)

        # Sort each group by x-coordinate
        for group in groups:
            group.sort(key=lambda k: k.center.x)

        return groups
