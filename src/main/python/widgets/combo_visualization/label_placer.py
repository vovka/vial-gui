"""Smart label placement for combo visualization."""

from PyQt5.QtCore import QRectF

from widgets.combo_visualization.geometry import ComboGeometry


class ComboLabelPlacer:
    """Handles smart placement of combo labels."""

    def __init__(self, key_rects, canvas_width, canvas_height, padding, split_gap=None):
        self.key_rects = key_rects
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = padding
        self.split_gap = split_gap
        self.placed_rects = []
        self.placed_lines = []

    def find_best_position(self, combo_info):
        """Find the best label position for a combo."""
        candidates = self._generate_candidates(combo_info)
        best_rect, best_score = None, float('inf')

        for candidate in candidates:
            clamped = self._clamp_rect(candidate, combo_info['rect_w'], combo_info['rect_h'])
            score = self._score_position(clamped, combo_info)
            if score < best_score:
                best_score = score
                best_rect = clamped

        if best_rect is None or best_score >= 1000:
            best_rect = self._find_fallback_position(combo_info)

        self._record_placement(best_rect, combo_info['key_centers'])
        return best_rect

    def _generate_candidates(self, info):
        """Generate candidate positions for label placement."""
        candidates = []
        bbox = info['bbox']
        rect_w, rect_h, gap = info['rect_w'], info['rect_h'], info['gap']
        center = info['center']

        if info['adjacent']:
            candidates.append(QRectF(center.x() - rect_w/2, center.y() - rect_h/2, rect_w, rect_h))

        for direction in info['directions']:
            candidates.append(self._position_for_direction(bbox, direction, rect_w, rect_h, gap))

        candidates.extend(self._corner_positions(bbox, info['directions'], rect_w, rect_h, gap))
        candidates.extend(self._split_gap_positions(bbox, rect_w, rect_h))
        return candidates

    def _position_for_direction(self, bbox, direction, rect_w, rect_h, gap):
        """Create a candidate rect for a given direction."""
        positions = {
            'above': (bbox.center().x() - rect_w/2, bbox.top() - gap - rect_h),
            'below': (bbox.center().x() - rect_w/2, bbox.bottom() + gap),
            'left': (bbox.left() - gap - rect_w, bbox.center().y() - rect_h/2),
            'right': (bbox.right() + gap, bbox.center().y() - rect_h/2),
        }
        x, y = positions.get(direction, (bbox.center().x() - rect_w/2, bbox.top() - gap - rect_h))
        return QRectF(x, y, rect_w, rect_h)

    def _corner_positions(self, bbox, directions, rect_w, rect_h, gap):
        """Generate corner position candidates."""
        candidates = []
        for direction in directions:
            if direction == 'above':
                candidates.append(QRectF(bbox.left(), bbox.top() - gap - rect_h, rect_w, rect_h))
                candidates.append(QRectF(bbox.right() - rect_w, bbox.top() - gap - rect_h, rect_w, rect_h))
            elif direction == 'below':
                candidates.append(QRectF(bbox.left(), bbox.bottom() + gap, rect_w, rect_h))
                candidates.append(QRectF(bbox.right() - rect_w, bbox.bottom() + gap, rect_w, rect_h))
            elif direction == 'left':
                candidates.append(QRectF(bbox.left() - gap - rect_w, bbox.top(), rect_w, rect_h))
                candidates.append(QRectF(bbox.left() - gap - rect_w, bbox.bottom() - rect_h, rect_w, rect_h))
            elif direction == 'right':
                candidates.append(QRectF(bbox.right() + gap, bbox.top(), rect_w, rect_h))
                candidates.append(QRectF(bbox.right() + gap, bbox.bottom() - rect_h, rect_w, rect_h))
        return candidates

    def _split_gap_positions(self, bbox, rect_w, rect_h):
        """Generate positions in the split gap area."""
        if not self.split_gap:
            return []
        gap_x = (self.split_gap[0] + self.split_gap[1]) / 2
        return [
            QRectF(gap_x - rect_w/2, bbox.top(), rect_w, rect_h),
            QRectF(gap_x - rect_w/2, bbox.bottom() - rect_h, rect_w, rect_h),
            QRectF(gap_x - rect_w/2, bbox.center().y() - rect_h/2, rect_w, rect_h),
        ]

    def _score_position(self, rect, combo_info):
        """Score a candidate position (lower is better)."""
        score = 0
        score += self._score_key_overlaps(rect)
        score += self._score_label_overlaps(rect)
        score += self._score_edge_proximity(rect)
        score += self._score_line_crossings(rect, combo_info)
        score += self._score_combo_line_intersections(rect, combo_info)
        score += self._score_split_gap_bonus(rect)
        return score

    def _score_key_overlaps(self, rect):
        return sum(1000 for r in self.key_rects if rect.intersects(r))

    def _score_label_overlaps(self, rect):
        return sum(500 for r in self.placed_rects if rect.intersects(r))

    def _score_edge_proximity(self, rect):
        score, margin = 0, 5
        if rect.left() < margin or rect.right() > self.canvas_width - margin:
            score += 50
        if rect.top() < margin or rect.bottom() > self.canvas_height - margin:
            score += 50
        return score

    def _score_line_crossings(self, rect, combo_info):
        score, rect_center = 0, rect.center()
        combo_key_rects = combo_info['combo_key_rects']
        for key_center in combo_info['key_centers']:
            for key_rect in self.key_rects:
                if key_rect in combo_key_rects:
                    continue
                if ComboGeometry.line_crosses_rect(rect_center, key_center, key_rect):
                    score += 30
        return score

    def _score_combo_line_intersections(self, rect, combo_info):
        score, rect_center = 0, rect.center()
        for prev_center, prev_keys in self.placed_lines:
            for key_center in combo_info['key_centers']:
                for prev_key in prev_keys:
                    if ComboGeometry.segments_intersect(rect_center, key_center, prev_center, prev_key):
                        score += 20
        return score

    def _score_split_gap_bonus(self, rect):
        if self.split_gap and self.split_gap[0] < rect.center().x() < self.split_gap[1]:
            return -10
        return 0

    def _clamp_rect(self, rect, rect_w, rect_h):
        """Clamp rectangle to canvas bounds."""
        x = max(self.padding, min(rect.x(), self.canvas_width - rect_w - self.padding))
        y = max(self.padding, min(rect.y(), self.canvas_height - rect_h - self.padding))
        return QRectF(x, y, rect_w, rect_h)

    def _find_fallback_position(self, combo_info):
        """Find a fallback position when all candidates fail."""
        bbox = combo_info['bbox']
        rect_w, rect_h, gap = combo_info['rect_w'], combo_info['rect_h'], combo_info['gap']
        rect = self._clamp_rect(
            QRectF(bbox.center().x() - rect_w/2, bbox.top() - gap - rect_h, rect_w, rect_h),
            rect_w, rect_h
        )
        step_y = rect_h + gap
        for _ in range(8):
            if self._score_position(rect, combo_info) < 500:
                break
            rect = self._clamp_rect(QRectF(rect.x(), rect.y() + step_y, rect_w, rect_h), rect_w, rect_h)
        return rect

    def _record_placement(self, rect, key_centers):
        """Record a placed label for future collision detection."""
        self.placed_rects.append(rect)
        self.placed_lines.append((rect.center(), key_centers))
