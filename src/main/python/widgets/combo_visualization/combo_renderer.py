"""Main renderer for combo visualization with dendrons."""

from typing import List
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QApplication

from .combo_data import ComboSpec, ComboPlacement
from .combo_box_placer import ComboBoxPlacer, Alignment
from .dendron_drawer import DendronDrawer
from .trunk_drawer import TrunkDrawer
from .combo_colors import ComboColors
from .point import Point


class ComboRenderer:
    """Orchestrates combo box and dendron rendering."""

    def __init__(self, arc_radius: float = 6.0):
        self.placer = ComboBoxPlacer()
        self.dendron_drawer = DendronDrawer(arc_radius)
        self.trunk_drawer = TrunkDrawer(arc_radius)
        self.colors = ComboColors()
        self.box_width_ratio = 0.45
        self.box_height_ratio = 0.35

    def render(self, qp: QPainter, combos: List[ComboSpec], scale: float):
        """Render all combos with dendrons."""
        if not combos:
            return
        qp.save()
        qp.scale(scale, scale)
        qp.setRenderHint(QPainter.Antialiasing)
        colors = self.colors.get_colors()
        for combo in combos:
            placement = self._compute_placement(combo)
            if placement:
                self._draw_combo(qp, placement, colors)
        qp.restore()

    def _compute_placement(self, combo: ComboSpec) -> ComboPlacement:
        """Compute placement for a single combo."""
        if not combo.keys:
            return None
        centers = [k.center for k in combo.keys]
        sizes = [k.size for k in combo.keys]
        avg_size = sum(sizes) / len(sizes)
        box_w, box_h = avg_size * self.box_width_ratio, avg_size * self.box_height_ratio
        pos, align = self.placer.compute_placement(centers, sizes, box_w, box_h)
        return ComboPlacement(pos, align, box_w, box_h, combo.keys, combo.output_label, combo.combo_label)

    def _draw_combo(self, qp: QPainter, p: ComboPlacement, colors: dict):
        """Draw a single combo with dendrons and box."""
        self._draw_dendrons(qp, p, colors['line_pen'])
        self._draw_box(qp, p, colors)
        self._draw_labels(qp, p, colors['text_pen'])

    def _draw_dendrons(self, qp: QPainter, p: ComboPlacement, pen: QPen):
        qp.setPen(pen)
        qp.setBrush(Qt.NoBrush)
        if p.alignment != Alignment.MID and self._should_use_trunk(p):
            self._draw_trunk_dendrons(qp, p)
        else:
            self._draw_individual_dendrons(qp, p)

    def _should_use_trunk(self, p: ComboPlacement) -> bool:
        if len(p.keys) < 2 or p.alignment not in (Alignment.TOP, Alignment.BOTTOM):
            return False
        avg = sum(k.size for k in p.keys) / len(p.keys)
        xs = [k.center.x for k in p.keys]
        return (max(xs) - min(xs)) < avg * 0.8

    def _draw_trunk_dendrons(self, qp: QPainter, p: ComboPlacement):
        """Draw trunk-and-branch style dendrons."""
        avg_size = sum(k.size for k in p.keys) / len(p.keys)
        key_centers = [k.center for k in p.keys]
        go_right = p.position.x < sum(pt.x for pt in key_centers) / len(key_centers)
        offset = avg_size * 0.3
        # Calculate key corner points (top-right if trunk on right, top-left if trunk on left)
        key_corners = []
        for k in p.keys:
            corner_x = k.center.x + k.size / 2 if go_right else k.center.x - k.size / 2
            corner_y = k.center.y - k.size / 2  # Top edge
            key_corners.append(Point(corner_x, corner_y))
        trunk_x = max(pt.x for pt in key_corners) + offset if go_right else min(pt.x for pt in key_corners) - offset
        trunk_start = Point(trunk_x, p.position.y + p.height / 2)
        qp.drawPath(self.trunk_drawer.draw_trunk_with_branches(trunk_start, key_corners, offset, go_right))
        qp.drawLine(int(p.position.x), int(p.position.y + p.height / 2), int(trunk_x), int(trunk_start.y))

    def _draw_individual_dendrons(self, qp: QPainter, p: ComboPlacement):
        """Draw individual dendron for each key."""
        for key in p.keys:
            if not self.placer.should_draw_dendron(p.alignment, p.position, key.center, key.size):
                continue
            # Calculate target point at key edge based on alignment
            target = self._get_key_edge_point(key, p.alignment)
            off = self.placer.get_key_offset(p.alignment, key.size, p.position, target, p.width, p.height)
            if p.alignment == Alignment.MID:
                qp.drawPath(self.dendron_drawer.draw_line_dendron(p.position, key.center, off))
            else:
                qp.drawPath(self.dendron_drawer.draw_arc_dendron(p.position, target, True, off))

    def _get_key_edge_point(self, key, alignment: Alignment) -> Point:
        """Get the point on key edge where dendron should connect."""
        half = key.size / 2
        if alignment == Alignment.TOP:
            return Point(key.center.x, key.center.y - half)
        elif alignment == Alignment.BOTTOM:
            return Point(key.center.x, key.center.y + half)
        elif alignment == Alignment.LEFT:
            return Point(key.center.x - half, key.center.y)
        elif alignment == Alignment.RIGHT:
            return Point(key.center.x + half, key.center.y)
        return key.center

    def _draw_box(self, qp: QPainter, p: ComboPlacement, colors: dict):
        """Draw the combo box rectangle."""
        qp.setPen(colors['border_pen'])
        qp.setBrush(colors['fill_brush'])
        qp.drawRoundedRect(self._box_rect(p), p.width * 0.15, p.width * 0.15)

    def _box_rect(self, p: ComboPlacement) -> QRectF:
        return QRectF(p.position.x - p.width / 2, p.position.y - p.height / 2, p.width, p.height)

    def _draw_labels(self, qp: QPainter, p: ComboPlacement, pen: QPen):
        """Draw combo label and output text."""
        qp.setPen(pen)
        font = QApplication.font()
        font.setPointSizeF(max(1.0, font.pointSizeF() * 0.6))
        qp.setFont(font)
        text = f"{p.combo_label}\n{p.output_label}" if p.output_label else p.combo_label
        qp.drawText(self._box_rect(p), Qt.AlignCenter, text)
