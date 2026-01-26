"""Main renderer for combo visualization with dendrons."""

from typing import List
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QApplication

from .combo_data import ComboSpec, ComboPlacement, KeyInfo
from .combo_box_placer import ComboBoxPlacer, Alignment
from .dendron_drawer import DendronDrawer
from .combo_colors import ComboColors


class ComboRenderer:
    """Orchestrates combo box and dendron rendering."""

    def __init__(self, arc_radius: float = 6.0):
        self.placer = ComboBoxPlacer()
        self.dendron_drawer = DendronDrawer(arc_radius)
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
        box_w = avg_size * self.box_width_ratio
        box_h = avg_size * self.box_height_ratio
        pos, alignment = self.placer.compute_placement(centers, sizes, box_w, box_h)
        return ComboPlacement(pos, alignment, box_w, box_h,
                              combo.keys, combo.output_label, combo.combo_label)

    def _draw_combo(self, qp: QPainter, placement: ComboPlacement, colors: dict):
        """Draw a single combo with dendrons and box."""
        self._draw_dendrons(qp, placement, colors['line_pen'])
        self._draw_box(qp, placement, colors)
        self._draw_labels(qp, placement, colors['text_pen'])

    def _draw_dendrons(self, qp: QPainter, placement: ComboPlacement, pen: QPen):
        """Draw dendron lines from combo box to keys."""
        qp.setPen(pen)
        qp.setBrush(Qt.NoBrush)
        for key in placement.keys:
            if not self._should_draw_dendron(placement, key):
                continue
            path = self._create_dendron_path(placement, key)
            qp.drawPath(path)

    def _should_draw_dendron(self, p: ComboPlacement, key: KeyInfo) -> bool:
        """Check if dendron should be drawn for this key."""
        return self.placer.should_draw_dendron(p.alignment, p.position, key.center, key.size)

    def _create_dendron_path(self, placement: ComboPlacement, key: KeyInfo):
        """Create the dendron path for a key."""
        offset = self.placer.get_key_offset(
            placement.alignment, key.size, placement.position,
            key.center, placement.width, placement.height)
        x_first = placement.alignment in (Alignment.TOP, Alignment.BOTTOM)
        if placement.alignment == Alignment.MID:
            return self.dendron_drawer.draw_line_dendron(
                placement.position, key.center, offset)
        return self.dendron_drawer.draw_arc_dendron(
            placement.position, key.center, x_first, offset)

    def _draw_box(self, qp: QPainter, placement: ComboPlacement, colors: dict):
        """Draw the combo box rectangle."""
        qp.setPen(colors['border_pen'])
        qp.setBrush(colors['fill_brush'])
        qp.drawRoundedRect(self._get_box_rect(placement), placement.width * 0.15, placement.width * 0.15)

    def _get_box_rect(self, placement: ComboPlacement) -> QRectF:
        """Get the rectangle for the combo box."""
        p, w, h = placement.position, placement.width, placement.height
        return QRectF(p.x - w / 2, p.y - h / 2, w, h)

    def _draw_labels(self, qp: QPainter, placement: ComboPlacement, pen: QPen):
        """Draw combo label and output text."""
        qp.setPen(pen)
        font = QApplication.font()
        font.setPointSizeF(max(1.0, font.pointSizeF() * 0.6))
        qp.setFont(font)
        text = f"{placement.combo_label}\n{placement.output_label}" if placement.output_label else placement.combo_label
        qp.drawText(self._get_box_rect(placement), Qt.AlignCenter, text)