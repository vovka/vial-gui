"""
Combo visualization module for rendering combo overlays on keyboard layouts.

This module provides classes for smart label placement and curved line routing
to visualize keyboard combos without cluttering the display.
"""

import math
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainterPath, QColor, QPen, QBrush, QFontMetrics, QPainter
from PyQt5.QtWidgets import QApplication, QPalette

from constants import KEY_ROUNDNESS


class ComboGeometry:
    """Handles geometric calculations for line intersections and collisions."""

    @staticmethod
    def segments_intersect(p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects with p3-p4."""
        def ccw(a, b, c):
            return (c.y() - a.y()) * (b.x() - a.x()) > (b.y() - a.y()) * (c.x() - a.x())
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    @staticmethod
    def line_intersection(p1, p2, p3, p4):
        """Find intersection point of two line segments, or None."""
        x1, y1, x2, y2 = p1.x(), p1.y(), p2.x(), p2.y()
        x3, y3, x4, y4 = p3.x(), p3.y(), p4.x(), p4.y()

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            return QPointF(x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        return None

    @staticmethod
    def line_crosses_rect(p1, p2, rect, margin_ratio=0.15):
        """Check if line crosses through rectangle interior."""
        shrunk = rect.adjusted(
            rect.width() * margin_ratio, rect.height() * margin_ratio,
            -rect.width() * margin_ratio, -rect.height() * margin_ratio
        )
        edges = ComboGeometry._get_rect_edges(shrunk)
        return any(ComboGeometry.segments_intersect(p1, p2, e1, e2) for e1, e2 in edges)

    @staticmethod
    def _get_rect_edges(rect):
        """Return the four edges of a rectangle as point pairs."""
        return [
            (QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top())),
            (QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom())),
            (QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())),
            (QPointF(rect.left(), rect.bottom()), QPointF(rect.left(), rect.top())),
        ]


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
        bbox, rect_w, rect_h, gap = info['bbox'], info['rect_w'], info['rect_h'], info['gap']
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
        score = 0
        margin = 5
        if rect.left() < margin or rect.right() > self.canvas_width - margin:
            score += 50
        if rect.top() < margin or rect.bottom() > self.canvas_height - margin:
            score += 50
        return score

    def _score_line_crossings(self, rect, combo_info):
        score = 0
        rect_center = rect.center()
        combo_key_rects = combo_info['combo_key_rects']
        for key_center in combo_info['key_centers']:
            for key_rect in self.key_rects:
                if key_rect in combo_key_rects:
                    continue
                if ComboGeometry.line_crosses_rect(rect_center, key_center, key_rect):
                    score += 30
        return score

    def _score_combo_line_intersections(self, rect, combo_info):
        score = 0
        rect_center = rect.center()
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


class DirectionCalculator:
    """Calculates preferred label placement direction based on key positions."""

    @staticmethod
    def compute(combo_centers, all_key_centers, canvas_width, canvas_height):
        """Compute preferred directions for label placement."""
        if not combo_centers:
            return ['above', 'below', 'right', 'left']

        avg_x = sum(c.x() for c in combo_centers) / len(combo_centers)
        avg_y = sum(c.y() for c in combo_centers) / len(combo_centers)

        kb_center_x, kb_center_y = canvas_width / 2, canvas_height / 2
        if all_key_centers:
            kb_center_x = sum(c.x() for c in all_key_centers) / len(all_key_centers)
            kb_center_y = sum(c.y() for c in all_key_centers) / len(all_key_centers)

        dx, dy = avg_x - kb_center_x, avg_y - kb_center_y

        if abs(dx) > abs(dy):
            return ['right', 'above', 'below', 'left'] if dx > 0 else ['left', 'above', 'below', 'right']
        return ['below', 'right', 'left', 'above'] if dy > 0 else ['above', 'right', 'left', 'below']


class ComboData:
    """Data container for a single combo's visualization info."""

    def __init__(self, widgets, output_label, combo_label):
        self.widgets = widgets
        self.output_label = output_label
        self.combo_label = combo_label
        self.bbox = None
        self.centers = []
        self.avg_size = 0
        self.adjacent = False
        self.rect = None

    def compute_geometry(self, adjacency_threshold_ratio=1.7):
        """Compute bounding box, centers, and adjacency."""
        self.bbox = self.widgets[0].polygon.boundingRect()
        size_total = 0
        for widget in self.widgets:
            self.bbox = self.bbox.united(widget.polygon.boundingRect())
            size_total += widget.size
            self.centers.append(widget.polygon.boundingRect().center())

        self.avg_size = size_total / len(self.widgets)
        threshold = self.avg_size * adjacency_threshold_ratio
        analyzer = ComboLayoutAnalyzer([])
        self.adjacent = analyzer.are_keys_adjacent(self.centers, threshold)

    @property
    def center(self):
        """Get the center point of all combo keys."""
        return QPointF(
            sum(c.x() for c in self.centers) / len(self.centers),
            sum(c.y() for c in self.centers) / len(self.centers)
        )

    @property
    def key_rects(self):
        """Get bounding rects of all combo keys."""
        return [w.polygon.boundingRect() for w in self.widgets]


class ComboLineRouter:
    """Routes curved lines between labels and keys, avoiding obstacles."""

    def __init__(self, obstacles, avg_size):
        self.obstacles = obstacles
        self.avg_size = avg_size

    def create_path(self, start, end, combo_key_rects):
        """Create a curved path from start to end avoiding obstacles."""
        path = QPainterPath()
        path.moveTo(start)

        blocking = self._find_blocking_rects(start, end, combo_key_rects)

        if not blocking:
            self._add_simple_curve(path, start, end)
            return path

        self._add_routed_curve(path, start, end, blocking)
        return path

    def _find_blocking_rects(self, start, end, combo_key_rects):
        """Find rectangles that block the direct path."""
        blocking = []
        for rect in self.obstacles:
            if rect in combo_key_rects:
                continue
            if ComboGeometry.line_crosses_rect(start, end, rect):
                blocking.append(rect)
        blocking.sort(key=lambda r: math.hypot(r.center().x() - start.x(), r.center().y() - start.y()))
        return blocking

    def _add_simple_curve(self, path, start, end):
        """Add a simple curve or line when no obstacles."""
        dx, dy = end.x() - start.x(), end.y() - start.y()
        dist = math.hypot(dx, dy)

        if dist > self.avg_size * 2:
            mid_x, mid_y = (start.x() + end.x()) / 2, (start.y() + end.y()) / 2
            perp_x = -dy / dist * self.avg_size * 0.15
            perp_y = dx / dist * self.avg_size * 0.15
            path.quadTo(QPointF(mid_x + perp_x, mid_y + perp_y), end)
        else:
            path.lineTo(end)

    def _add_routed_curve(self, path, start, end, blocking):
        """Add a curve that routes around blocking rectangles."""
        current = start
        for rect in blocking:
            waypoint = self._compute_waypoint(current, end, rect)
            self._add_cubic_segment(path, current, waypoint)
            current = waypoint
        self._add_final_segment(path, current, end)

    def _compute_waypoint(self, current, end, rect):
        """Compute a waypoint to route around a rectangle."""
        dx, dy = end.x() - current.x(), end.y() - current.y()
        rect_center = rect.center()
        cross = dx * (rect_center.y() - current.y()) - dy * (rect_center.x() - current.x())
        margin = self.avg_size * 0.3

        if abs(dy) > abs(dx):
            y = rect.top() - margin if cross > 0 else rect.bottom() + margin
            return QPointF(rect_center.x(), y)
        else:
            x = rect.left() - margin if cross > 0 else rect.right() + margin
            return QPointF(x, rect_center.y())

    def _add_cubic_segment(self, path, start, end):
        """Add a cubic bezier segment."""
        ctrl1 = QPointF((start.x() + end.x()) / 2, start.y())
        ctrl2 = QPointF(end.x(), (start.y() + end.y()) / 2)
        path.cubicTo(ctrl1, ctrl2, end)

    def _add_final_segment(self, path, current, end):
        """Add the final segment to the destination."""
        ctrl1 = QPointF(current.x(), (current.y() + end.y()) / 2)
        ctrl2 = QPointF((current.x() + end.x()) / 2, end.y())
        path.cubicTo(ctrl1, ctrl2, end)


class ComboRenderer:
    """Orchestrates combo visualization rendering."""

    def __init__(self, widgets, canvas_width, canvas_height, padding):
        self.widgets = widgets
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = padding
        self.key_rects = [w.polygon.boundingRect() for w in widgets]
        self._setup_layout_analysis()

    def _setup_layout_analysis(self):
        """Initialize layout analyzer for split detection."""
        self.analyzer = ComboLayoutAnalyzer(self.key_rects)
        self.all_key_centers = [r.center() for r in self.key_rects]

    def compute_placements(self, combos_data):
        """Compute label placements for all combos."""
        placer = ComboLabelPlacer(
            self.key_rects, self.canvas_width, self.canvas_height,
            self.padding, self.analyzer.split_gap
        )

        for combo in combos_data:
            combo.compute_geometry()
            combo_info = self._build_combo_info(combo)
            combo.rect = placer.find_best_position(combo_info)

        return combos_data

    def _build_combo_info(self, combo):
        """Build info dict for label placement."""
        directions = DirectionCalculator.compute(
            combo.centers, self.all_key_centers,
            self.canvas_width, self.canvas_height
        )
        gap = combo.avg_size * 0.25
        rect_w = max(combo.avg_size * 0.5, combo.avg_size * 0.45)
        rect_h = max(combo.avg_size * 0.4, combo.avg_size * 0.35)

        return {
            'bbox': combo.bbox,
            'center': combo.center,
            'centers': combo.centers,
            'key_centers': combo.centers,
            'combo_key_rects': combo.key_rects,
            'adjacent': combo.adjacent,
            'directions': directions,
            'rect_w': rect_w,
            'rect_h': rect_h,
            'gap': gap,
        }

    def create_line_path(self, combo, start, end):
        """Create a curved line path for a combo."""
        router = ComboLineRouter(self.key_rects, combo.avg_size)
        return router.create_path(start, end, combo.key_rects)


class ComboDrawingContext:
    """Handles the actual drawing of combo visualizations."""

    def __init__(self, painter, scale):
        self.qp = painter
        self.scale = scale
        self._setup_styles()
        self._setup_fonts()

    def _setup_styles(self):
        """Initialize pens and brushes for drawing."""
        palette = QApplication.palette()

        fill_color = QColor(palette.color(QPalette.Highlight))
        fill_color.setAlpha(40)
        border_color = QColor(palette.color(QPalette.Highlight))
        border_color.setAlpha(90)
        line_color = QColor(palette.color(QPalette.ButtonText))
        line_color.setAlpha(100)
        text_color = QColor(palette.color(QPalette.ButtonText))
        text_color.setAlpha(160)

        self.line_pen = QPen(line_color)
        self.line_pen.setWidthF(1.5)
        self.border_pen = QPen(border_color)
        self.border_pen.setWidthF(1.0)
        self.fill_brush = QBrush(fill_color)
        self.text_pen = QPen(text_color)

    def _setup_fonts(self):
        """Initialize fonts for label text."""
        self.text_font = QApplication.font()
        base_size = self.text_font.pointSizeF()
        if base_size <= 0:
            base_size = float(self.text_font.pointSize())

        self.text_font.setPointSizeF(max(1.0, base_size * 0.7))
        self.name_font = QApplication.font()
        self.name_font.setPointSizeF(max(1.0, base_size * 0.6))

        self.name_metrics = QFontMetrics(self.name_font)
        self.label_metrics = QFontMetrics(self.text_font)

    def draw_all(self, combos_data, renderer):
        """Draw all combo visualizations."""
        self.qp.save()
        self.qp.scale(self.scale, self.scale)
        self.qp.setRenderHint(QPainter.Antialiasing)

        for combo in combos_data:
            self._draw_combo(combo, renderer)

        self.qp.restore()

    def _draw_combo(self, combo, renderer):
        """Draw a single combo visualization."""
        if not combo.adjacent:
            self._draw_lines(combo, renderer)
        self._draw_label_box(combo)
        self._draw_label_text(combo)

    def _draw_lines(self, combo, renderer):
        """Draw connecting lines from label to keys."""
        self.qp.setPen(self.line_pen)
        rect_center = combo.rect.center()
        for widget in combo.widgets:
            key_center = widget.polygon.boundingRect().center()
            path = renderer.create_line_path(combo, rect_center, key_center)
            self.qp.drawPath(path)

    def _draw_label_box(self, combo):
        """Draw the label background box."""
        self.qp.setPen(self.border_pen)
        self.qp.setBrush(self.fill_brush)
        corner = combo.avg_size * KEY_ROUNDNESS
        self.qp.drawRoundedRect(combo.rect, corner, corner)

    def _draw_label_text(self, combo):
        """Draw the label text."""
        if not combo.combo_label:
            return

        self.qp.setPen(self.text_pen)
        if combo.output_label:
            self._draw_two_line_label(combo)
        else:
            self._draw_single_line_label(combo)

    def _draw_two_line_label(self, combo):
        """Draw label with combo name and output."""
        name_h = self.name_metrics.height()
        label_lines = combo.output_label.splitlines() if combo.output_label else []
        label_h = len(label_lines) * self.label_metrics.height()
        text_gap = max(1.0, self.name_metrics.height() * 0.15)

        total_h = name_h + label_h + text_gap
        start_y = combo.rect.y() + (combo.rect.height() - total_h) / 2

        name_rect = QRectF(combo.rect.x(), start_y, combo.rect.width(), name_h)
        label_rect = QRectF(combo.rect.x(), start_y + name_h + text_gap,
                            combo.rect.width(), label_h)

        self.qp.setFont(self.name_font)
        self.qp.drawText(name_rect, Qt.AlignHCenter | Qt.AlignVCenter, combo.combo_label)
        self.qp.setFont(self.text_font)
        self.qp.drawText(label_rect, Qt.AlignHCenter | Qt.AlignVCenter, combo.output_label)

    def _draw_single_line_label(self, combo):
        """Draw label with only combo name."""
        self.qp.setFont(self.name_font)
        self.qp.drawText(combo.rect, Qt.AlignCenter, combo.combo_label)
