"""Drawing context for combo visualization."""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QFontMetrics, QPainter, QPalette
from PyQt5.QtWidgets import QApplication

from constants import KEY_ROUNDNESS


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
        fill_color.setAlpha(50)
        border_color = QColor(palette.color(QPalette.Highlight))
        border_color.setAlpha(120)

        line_color = QColor(128, 128, 128)
        text_color = QColor(palette.color(QPalette.ButtonText))

        self.line_pen = QPen(line_color)
        self.line_pen.setWidthF(1.0)
        self.line_pen.setCapStyle(Qt.RoundCap)
        self.line_pen.setJoinStyle(Qt.RoundJoin)
        self.border_pen = QPen(border_color)
        self.border_pen.setWidthF(1.5)
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
        self._draw_lines(combo, renderer)
        self._draw_label_box(combo)
        self._draw_label_text(combo)

    def _draw_lines(self, combo, renderer):
        """Draw connecting lines from label to keys."""
        self.qp.setPen(self.line_pen)
        self.qp.setBrush(Qt.NoBrush)
        start = self._get_dendron_start(combo)
        for widget in combo.widgets:
            key_center = widget.polygon.boundingRect().center()
            path = renderer.create_line_path(combo, start, key_center)
            self.qp.drawPath(path)

    def _get_dendron_start(self, combo):
        """Get the starting point for dendrons based on alignment."""
        rect = combo.rect
        if combo.alignment == 'top':
            return QPointF(rect.center().x(), rect.bottom())
        elif combo.alignment == 'bottom':
            return QPointF(rect.center().x(), rect.top())
        elif combo.alignment == 'left':
            return QPointF(rect.right(), rect.center().y())
        elif combo.alignment == 'right':
            return QPointF(rect.left(), rect.center().y())
        return rect.center()

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
