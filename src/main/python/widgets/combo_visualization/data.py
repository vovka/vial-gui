"""Data container for combo visualization."""

from PyQt5.QtCore import QPointF

from widgets.combo_visualization.layout_analyzer import ComboLayoutAnalyzer


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
        self.alignment = 'top'
        self.line_offset = 0.0

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

    def compute_alignment(self):
        """Determine alignment based on label position relative to keys."""
        if self.rect is None or self.bbox is None:
            return
        label_center = self.rect.center()
        bbox_center = self.bbox.center()

        if self.rect.bottom() < self.bbox.top():
            self.alignment = 'top'
        elif self.rect.top() > self.bbox.bottom():
            self.alignment = 'bottom'
        elif self.rect.right() < self.bbox.left():
            self.alignment = 'left'
        elif self.rect.left() > self.bbox.right():
            self.alignment = 'right'
        else:
            self.alignment = 'center'

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
