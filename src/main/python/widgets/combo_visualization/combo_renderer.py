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
        key_pts = [k.center for k in p.keys]
        go_right = p.position.x < sum(pt.x for pt in key_pts) / len(key_pts)
        offset = avg_size * 0.3
        trunk_x = max(pt.x for pt in key_pts) + offset if go_right else min(pt.x for pt in key_pts) - offset
        trunk_start = Point(trunk_x, p.position.y + p.height / 2)
        qp.drawPath(self.trunk_drawer.draw_trunk_with_branches(trunk_start, key_pts, offset, go_right))
        qp.drawLine(int(p.position.x), int(p.position.y + p.height / 2), int(trunk_x), int(trunk_start.y))

    def _draw_individual_dendrons(self, qp: QPainter, p: ComboPlacement):
        """Draw tree-structured dendrons connecting to key corners with curved endings."""
        # Filter keys that should have dendrons drawn
        keys_to_draw = [key for key in p.keys
                        if self.placer.should_draw_dendron(p.alignment, p.position, key.center, key.size)]

        if not keys_to_draw:
            return

        if p.alignment == Alignment.MID:
            # Simple line dendrons for MID alignment
            for key in keys_to_draw:
                corner = self.placer.get_closest_corner(p.position, key.center, key.size)
                qp.drawPath(self.dendron_drawer.draw_line_dendron(p.position, corner, 0))
            return

        # Group keys by row for tree-structured dendrons
        groups = self.placer.group_keys_by_row(keys_to_draw)

        # Build row_groups list: (row_y, corners, centers) for each row
        row_groups = []
        for group in groups:
            corners = [self.placer.get_closest_corner(p.position, k.center, k.size) for k in group]
            centers = [k.center for k in group]
            # Use average corner y for the row level
            row_y = sum(c.y for c in corners) / len(corners)
            row_groups.append((row_y, corners, centers))

        # Sort by row_y to draw from combo downward
        row_groups.sort(key=lambda x: x[0])

        # Draw tree dendron with all rows
        qp.drawPath(self.dendron_drawer.draw_tree_dendron(p.position, row_groups))

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
