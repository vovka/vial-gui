# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF
from widgets.combo_label_placement.combo_info import ComboInfo


class ComboInfoBuilder:
    def __init__(self, label_metrics, name_metrics):
        self.label_metrics = label_metrics
        self.name_metrics = name_metrics

    def build(self, combos):
        return [self._build_one(idx, *combo) for idx, combo in enumerate(combos)]

    def _build_one(self, index, combo_widgets, output_label, combo_label):
        bbox, avg_size, centers, anchor = self._combo_stats(combo_widgets)
        rect_w, rect_h = self._rect_size(avg_size, output_label, combo_label)
        adjacent = self._is_adjacent(centers, avg_size)
        return ComboInfo(index, combo_widgets, output_label, combo_label,
                         rect_w, rect_h, avg_size, bbox, anchor, adjacent)

    def _combo_stats(self, combo_widgets):
        bbox = self._combo_bbox(combo_widgets)
        centers = [w.polygon.boundingRect().center() for w in combo_widgets]
        avg_size = sum(w.size for w in combo_widgets) / len(combo_widgets)
        return bbox, avg_size, centers, self._avg_point(centers)

    def _combo_bbox(self, combo_widgets):
        bbox = combo_widgets[0].polygon.boundingRect()
        for widget in combo_widgets[1:]:
            bbox = bbox.united(widget.polygon.boundingRect())
        return bbox

    def _avg_point(self, points):
        total_x = sum(point.x() for point in points)
        total_y = sum(point.y() for point in points)
        count = len(points)
        return QPointF(total_x / count, total_y / count)

    def _rect_size(self, avg_size, output_label, combo_label):
        rect_w = max(avg_size * 0.5, avg_size * 0.45)
        rect_h = max(avg_size * 0.4, avg_size * 0.35)
        return rect_w, self._rect_height(rect_h, avg_size, output_label, combo_label)

    def _rect_height(self, rect_h, avg_size, output_label, combo_label):
        label_lines = output_label.splitlines() if output_label else []
        label_height = len(label_lines) * self.label_metrics.height()
        name_height = self.name_metrics.height() if combo_label else 0
        text_gap = max(1.0, self.name_metrics.height() * 0.15) if output_label else 0
        needed = name_height + label_height + text_gap + (max(1.5, avg_size * 0.05) * 2)
        return max(rect_h, needed)

    def _is_adjacent(self, centers, avg_size):
        if len(centers) <= 1:
            return False
        threshold = self._adjacent_threshold(avg_size)
        visited, stack = {0}, [0]
        while stack:
            neighbors = self._collect_neighbors(centers, stack.pop(), threshold, visited)
            visited.update(neighbors); stack.extend(neighbors)
        return len(visited) == len(centers)

    def _adjacent_threshold(self, avg_size):
        return avg_size * 1.7

    def _collect_neighbors(self, centers, index, threshold, visited):
        neighbors = []
        for j, point in enumerate(centers):
            if j in visited:
                continue
            dx = point.x() - centers[index].x()
            dy = point.y() - centers[index].y()
            if math.hypot(dx, dy) <= threshold:
                neighbors.append(j)
        return neighbors
