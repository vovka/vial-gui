"""Theme-aware color management for combo visualization."""

from PyQt5.QtGui import QColor, QPen, QBrush, QPalette
from PyQt5.QtWidgets import QApplication


class ComboColors:
    """Provides theme-aware colors for combo rendering."""

    def __init__(self):
        self._cache = None

    def get_colors(self) -> dict:
        """Get the current theme colors for combo rendering."""
        return self._create_colors()

    def _create_colors(self) -> dict:
        """Create color dictionary from current palette."""
        palette = QApplication.palette()
        return {
            'fill_brush': self._create_fill_brush(palette),
            'border_pen': self._create_border_pen(palette),
            'line_pen': self._create_line_pen(palette),
            'text_pen': self._create_text_pen(palette),
        }

    def _create_fill_brush(self, palette: QPalette) -> QBrush:
        """Create semi-transparent fill brush."""
        color = QColor(palette.color(QPalette.Highlight))
        color.setAlpha(40)
        return QBrush(color)

    def _create_border_pen(self, palette: QPalette) -> QPen:
        """Create border pen with highlight color."""
        color = QColor(palette.color(QPalette.Highlight))
        color.setAlpha(90)
        return QPen(color, 1.0)

    def _create_line_pen(self, palette: QPalette) -> QPen:
        """Create dendron line pen."""
        color = QColor(palette.color(QPalette.ButtonText))
        color.setAlpha(100)
        return QPen(color, 1.0)

    def _create_text_pen(self, palette: QPalette) -> QPen:
        """Create text pen."""
        color = QColor(palette.color(QPalette.ButtonText))
        color.setAlpha(180)
        return QPen(color)
