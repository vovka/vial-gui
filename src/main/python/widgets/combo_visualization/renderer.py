"""Combo visualization renderer orchestration."""

from widgets.combo_visualization.layout_analyzer import ComboLayoutAnalyzer
from widgets.combo_visualization.label_placer import ComboLabelPlacer
from widgets.combo_visualization.direction_calculator import DirectionCalculator
from widgets.combo_visualization.line_router import ComboLineRouter


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
            combo.compute_alignment()

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
        """Create an arc dendron path for a combo."""
        router = ComboLineRouter(self.key_rects, combo.avg_size)
        x_first = combo.alignment in ('top', 'bottom')
        return router.create_path(start, end, combo.key_rects, x_first)
