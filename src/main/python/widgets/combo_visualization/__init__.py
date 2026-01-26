"""
Combo visualization package for rendering combo overlays on keyboard layouts.

This package provides classes for smart label placement and curved line routing
to visualize keyboard combos without cluttering the display.
"""

from widgets.combo_visualization.geometry import ComboGeometry
from widgets.combo_visualization.layout_analyzer import ComboLayoutAnalyzer
from widgets.combo_visualization.direction_calculator import DirectionCalculator
from widgets.combo_visualization.label_placer import ComboLabelPlacer
from widgets.combo_visualization.data import ComboData
from widgets.combo_visualization.line_router import ComboLineRouter
from widgets.combo_visualization.renderer import ComboRenderer
from widgets.combo_visualization.drawing_context import ComboDrawingContext

__all__ = [
    'ComboGeometry',
    'ComboLayoutAnalyzer',
    'DirectionCalculator',
    'ComboLabelPlacer',
    'ComboData',
    'ComboLineRouter',
    'ComboRenderer',
    'ComboDrawingContext',
]
