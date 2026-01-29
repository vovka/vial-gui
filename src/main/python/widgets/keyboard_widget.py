from collections import defaultdict
import logging
import math
import re
import time

from PyQt5.QtGui import QPainter, QColor, QPainterPath, QTransform, QBrush, QPolygonF, QPalette, QPen, QFontMetrics
from PyQt5.QtWidgets import QWidget, QToolTip, QApplication
from PyQt5.QtCore import Qt, QSize, QRect, QPointF, pyqtSignal, QEvent, QRectF

from constants import KEY_SIZE_RATIO, KEY_SPACING_RATIO, KEYBOARD_WIDGET_PADDING, \
    KEYBOARD_WIDGET_MASK_HEIGHT, KEY_ROUNDNESS, SHADOW_SIDE_PADDING, SHADOW_TOP_PADDING, SHADOW_BOTTOM_PADDING, \
    KEYBOARD_WIDGET_NONMASK_PADDING
from keycodes.keycodes import Keycode
from util import KeycodeDisplay
from themes import Theme
from widgets.combo_label_placement import ComboInfoBuilder, ComboSlotAssigner
from widgets.free_slots_grid import SlotGenerator, SlotRenderer, SlotRegionType
from widgets.connector_routing import ConnectorRouter, ConnectorPathRenderer

logger = logging.getLogger("KeyboardWidget")


def _interpolate_color(color1, color2, factor):
    """Interpolate between two QColors based on factor (0.0 to 1.0)."""
    return QColor(
        round(color1.red() + (color2.red() - color1.red()) * factor),
        round(color1.green() + (color2.green() - color1.green()) * factor),
        round(color1.blue() + (color2.blue() - color1.blue()) * factor),
    )


class KeyWidget:

    def __init__(self, desc, scale, shift_x=0, shift_y=0):
        self.active = False
        self.on = False
        self.masked = False
        self.pressed = False
        self.highlight_intensity = 0.0
        self.desc = desc
        self.text = ""
        self.mask_text = ""
        self.tooltip = ""
        self.color = None
        self.mask_color = None
        self.scale = 0
        self.font_scale = 1.0

        self.rotation_angle = desc.rotation_angle

        self.has2 = desc.width2 != desc.width or desc.height2 != desc.height or desc.x2 != 0 or desc.y2 != 0

        self.update_position(scale, shift_x, shift_y)

    def update_position(self, scale, shift_x=0, shift_y=0):
        if self.scale != scale or self.shift_x != shift_x or self.shift_y != shift_y:
            self.scale = scale
            self.size = self.scale * (KEY_SIZE_RATIO + KEY_SPACING_RATIO)
            spacing = self.scale * KEY_SPACING_RATIO

            self.rotation_x = self.size * self.desc.rotation_x
            self.rotation_y = self.size * self.desc.rotation_y

            self.shift_x = shift_x
            self.shift_y = shift_y
            self.x = self.size * self.desc.x
            self.y = self.size * self.desc.y
            self.w = self.size * self.desc.width - spacing
            self.h = self.size * self.desc.height - spacing

            self.rect = QRect(
                round(self.x),
                round(self.y),
                round(self.w),
                round(self.h)
            )
            self.text_rect = QRect(
                round(self.x),
                round(self.y + self.size * SHADOW_TOP_PADDING),
                round(self.w),
                round(self.h - self.size * (SHADOW_BOTTOM_PADDING + SHADOW_TOP_PADDING))
            )

            self.x2 = self.x + self.size * self.desc.x2
            self.y2 = self.y + self.size * self.desc.y2
            self.w2 = self.size * self.desc.width2 - spacing
            self.h2 = self.size * self.desc.height2 - spacing

            self.rect2 = QRect(
                round(self.x2),
                round(self.y2),
                round(self.w2),
                round(self.h2)
            )

            self.bbox = self.calculate_bbox(self.rect)
            self.bbox2 = self.calculate_bbox(self.rect2)
            self.polygon = QPolygonF(self.bbox + [self.bbox[0]])
            self.polygon2 = QPolygonF(self.bbox2 + [self.bbox2[0]])
            self.polygon = self.polygon.united(self.polygon2)
            self.corner = self.size * KEY_ROUNDNESS
            self.background_draw_path = self.calculate_background_draw_path()
            self.foreground_draw_path = self.calculate_foreground_draw_path()
            self.extra_draw_path = self.calculate_extra_draw_path()

            # calculate areas where the inner keycode will be located
            # nonmask = outer (e.g. Rsft_T)
            # mask = inner (e.g. KC_A)
            self.nonmask_rect = QRect(
                round(self.x),
                round(self.y + self.size * KEYBOARD_WIDGET_NONMASK_PADDING),
                round(self.w),
                round(self.h * (1 - KEYBOARD_WIDGET_MASK_HEIGHT))
            )
            self.mask_rect = QRect(
                round(self.x + self.size * SHADOW_SIDE_PADDING),
                round(self.y + self.h * (1 - KEYBOARD_WIDGET_MASK_HEIGHT)),
                round(self.w - 2 * self.size * SHADOW_SIDE_PADDING),
                round(self.h * KEYBOARD_WIDGET_MASK_HEIGHT - self.size * SHADOW_BOTTOM_PADDING)
            )
            self.mask_bbox = self.calculate_bbox(self.mask_rect)
            self.mask_polygon = QPolygonF(self.mask_bbox + [self.mask_bbox[0]])

    def calculate_bbox(self, rect):
        x1 = rect.topLeft().x()
        y1 = rect.topLeft().y()
        x2 = rect.bottomRight().x()
        y2 = rect.bottomRight().y()
        points = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
        bbox = []
        for p in points:
            t = QTransform()
            t.translate(self.shift_x, self.shift_y)
            t.translate(self.rotation_x, self.rotation_y)
            t.rotate(self.rotation_angle)
            t.translate(-self.rotation_x, -self.rotation_y)
            p = t.map(QPointF(p[0], p[1]))
            bbox.append(p)
        return bbox

    def calculate_background_draw_path(self):
        path = QPainterPath()
        path.addRoundedRect(
            round(self.x),
            round(self.y),
            round(self.w),
            round(self.h),
            self.corner,
            self.corner
        )

        # second part only considered if different from first
        if self.has2:
            path2 = QPainterPath()
            path2.addRoundedRect(
                round(self.x2),
                round(self.y2),
                round(self.w2),
                round(self.h2),
                self.corner,
                self.corner
            )
            path = path.united(path2)

        return path

    def calculate_foreground_draw_path(self):
        path = QPainterPath()
        path.addRoundedRect(
            round(self.x + self.size * SHADOW_SIDE_PADDING),
            round(self.y + self.size * SHADOW_TOP_PADDING),
            round(self.w - 2 * self.size * SHADOW_SIDE_PADDING),
            round(self.h - self.size * (SHADOW_BOTTOM_PADDING + SHADOW_TOP_PADDING)),
            self.corner,
            self.corner
        )

        # second part only considered if different from first
        if self.has2:
            path2 = QPainterPath()
            path2.addRoundedRect(
                round(self.x2 + self.size * SHADOW_SIDE_PADDING),
                round(self.y2 + self.size * SHADOW_TOP_PADDING),
                round(self.w2 - 2 * self.size * SHADOW_SIDE_PADDING),
                round(self.h2 - self.size * (SHADOW_BOTTOM_PADDING + SHADOW_TOP_PADDING)),
                self.corner,
                self.corner
            )
            path = path.united(path2)

        return path

    def calculate_extra_draw_path(self):
        return QPainterPath()

    def setText(self, text):
        self.text = text

    def setMaskText(self, text):
        self.mask_text = text

    def setToolTip(self, tooltip):
        self.tooltip = tooltip

    def setActive(self, active):
        self.active = active

    def setOn(self, on):
        self.on = on

    def setPressed(self, pressed):
        self.pressed = pressed

    def setColor(self, color):
        self.color = color

    def setMaskColor(self, color):
        self.mask_color = color

    def setFontScale(self, scale):
        self.font_scale = scale

    def setHighlightIntensity(self, intensity):
        self.highlight_intensity = max(0.0, min(1.0, intensity))

    def __repr__(self):
        qualifiers = ["KeyboardWidget"]
        if self.desc.row is not None:
            qualifiers.append("matrix:{},{}".format(self.desc.row, self.desc.col))
        if self.desc.layout_index != -1:
            qualifiers.append("layout:{},{}".format(self.desc.layout_index, self.desc.layout_option))
        return " ".join(qualifiers)


class EncoderWidget(KeyWidget):

    def calculate_background_draw_path(self):
        path = QPainterPath()
        path.addEllipse(round(self.x), round(self.y), round(self.w), round(self.h))
        return path

    def calculate_foreground_draw_path(self):
        path = QPainterPath()
        path.addEllipse(
            round(self.x + self.size * SHADOW_SIDE_PADDING),
            round(self.y + self.size * SHADOW_TOP_PADDING),
            round(self.w - 2 * self.size * SHADOW_SIDE_PADDING),
            round(self.h - self.size * (SHADOW_BOTTOM_PADDING + SHADOW_TOP_PADDING))
        )
        return path

    def calculate_extra_draw_path(self):
        path = QPainterPath()
        # midpoint of arrow triangle
        p = self.h
        x = self.x
        y = self.y + p / 2
        if self.desc.encoder_dir == 0:
            # counterclockwise - pointing down
            path.moveTo(round(x), round(y))
            path.lineTo(round(x + p / 10), round(y - p / 10))
            path.lineTo(round(x), round(y + p / 10))
            path.lineTo(round(x - p / 10), round(y - p / 10))
            path.lineTo(round(x), round(y))
        else:
            # clockwise - pointing up
            path.moveTo(round(x), round(y))
            path.lineTo(round(x + p / 10), round(y + p / 10))
            path.lineTo(round(x), round(y - p / 10))
            path.lineTo(round(x - p / 10), round(y + p / 10))
            path.lineTo(round(x), round(y))
        return path

    def __repr__(self):
        return "EncoderWidget"


class KeyboardWidget(QWidget):

    clicked = pyqtSignal()
    deselected = pyqtSignal()
    anykey = pyqtSignal()

    def __init__(self, layout_editor):
        super().__init__()

        self.enabled = True
        self.scale = 1
        self.padding = KEYBOARD_WIDGET_PADDING

        self.setMouseTracking(True)

        self.layout_editor = layout_editor

        # widgets common for all layouts
        self.common_widgets = []

        # layout-specific widgets
        self.widgets_for_layout = []

        # widgets in current layout
        self.widgets = []

        self.width = self.height = 0
        self.active_key = None
        self.active_mask = False
        self.combo_entries = []
        self.combo_entries_numeric = []
        self.combo_widget_keycodes_numeric = {}
        self.show_combos = True
        self.show_combo_debug = False

        # Free slots grid
        self.slot_generator = SlotGenerator()
        self.slot_renderer = SlotRenderer()
        self.free_slots = []
        self.canvas_bounds = None

        # Combo layout cache (computed once, reused on every paint)
        self._combo_cache = None

    def _invalidate_combo_cache(self):
        """Invalidate cached combo layout data."""
        import traceback
        logger.warning("CACHE INVALIDATED - stack trace:")
        for line in traceback.format_stack()[-5:-1]:
            logger.warning(line.strip())
        self._combo_cache = None

    def set_keys(self, keys, encoders):
        self.common_widgets = []
        self.widgets_for_layout = []

        self.add_keys([(x, KeyWidget) for x in keys] + [(x, EncoderWidget) for x in encoders])
        self._invalidate_combo_cache()
        self.update_layout()

    def add_keys(self, keys):
        scale_factor = self.fontMetrics().height()

        for key, cls in keys:
            if key.layout_index == -1:
                self.common_widgets.append(cls(key, scale_factor))
            else:
                self.widgets_for_layout.append(cls(key, scale_factor))

    def place_widgets(self):
        scale_factor = self.fontMetrics().height()

        self.widgets = []

        # place common widgets, that is, ones which are always displayed and require no extra transforms
        for widget in self.common_widgets:
            widget.update_position(scale_factor)
            self.widgets.append(widget)

        # top-left position for specific layout
        layout_x = defaultdict(lambda: defaultdict(lambda: 1e6))
        layout_y = defaultdict(lambda: defaultdict(lambda: 1e6))

        # determine top-left position for every layout option
        for widget in self.widgets_for_layout:
            widget.update_position(scale_factor)
            idx, opt = widget.desc.layout_index, widget.desc.layout_option
            p = widget.polygon.boundingRect().topLeft()
            layout_x[idx][opt] = min(layout_x[idx][opt], p.x())
            layout_y[idx][opt] = min(layout_y[idx][opt], p.y())

        # obtain widgets for all layout options now that we know how to shift them
        for widget in self.widgets_for_layout:
            idx, opt = widget.desc.layout_index, widget.desc.layout_option
            if opt == self.layout_editor.get_choice(idx):
                shift_x = layout_x[idx][opt] - layout_x[idx][0]
                shift_y = layout_y[idx][opt] - layout_y[idx][0]
                widget.update_position(scale_factor, -shift_x, -shift_y)
                self.widgets.append(widget)

        # at this point some widgets on left side might be cutoff, or there may be too much empty space
        # calculate top left position of visible widgets and shift everything around
        top_x = top_y = 1e6
        for widget in self.widgets:
            if not widget.desc.decal:
                p = widget.polygon.boundingRect().topLeft()
                top_x = min(top_x, p.x())
                top_y = min(top_y, p.y())
        for widget in self.widgets:
            widget.update_position(widget.scale, widget.shift_x - top_x + self.padding,
                                   widget.shift_y - top_y + self.padding)

    def update_layout(self):
        """ Updates self.widgets for the currently active layout """
        logger.warning(f"update_layout called, scale={self.scale}")

        # determine widgets for current layout
        self.place_widgets()
        self.widgets = list(filter(lambda w: not w.desc.decal, self.widgets))

        self.widgets.sort(key=lambda w: (w.y, w.x))

        # Add extra padding for slot grid (space for 1 row of slots on each side)
        avg_key_size = self._compute_avg_key_size()
        slot_padding = avg_key_size * 0.8

        # Shift all widgets by slot_padding to center keyboard in canvas
        for widget in self.widgets:
            widget.update_position(widget.scale,
                                   widget.shift_x + slot_padding,
                                   widget.shift_y + slot_padding)

        # Calculate max dimensions AFTER shift, then add padding for right/bottom
        max_w = max_h = 0
        for key in self.widgets:
            p = key.polygon.boundingRect().bottomRight()
            max_w = max(max_w, p.x())
            max_h = max(max_h, p.y())

        # Add slot_padding for right/bottom (left/top already have it from shift)
        total_padding = self.padding + slot_padding
        self.width = round((max_w + total_padding) * self.scale)
        self.height = round((max_h + total_padding) * self.scale)

        self._generate_free_slots()

        self.update()
        self.updateGeometry()

    def _compute_avg_key_size(self):
        """Compute average key size for padding calculations."""
        if not self.widgets:
            return 50.0
        total = sum(max(w.polygon.boundingRect().width(), w.polygon.boundingRect().height())
                    for w in self.widgets)
        return total / len(self.widgets)

    def _gap_intersections(self, key_rects, avg_key_size):
        if not key_rects or avg_key_size <= 0:
            return []
        vertical_lines = []
        horizontal_lines = []
        epsilon = avg_key_size * 0.06
        gap_margin = avg_key_size * 0.12
        shrink = avg_key_size * 0.08

        for rect in key_rects:
            nearest_right_left = None
            right_candidates = []
            nearest_left_right = None
            left_candidates = []
            for other in key_rects:
                if other is rect or other.left() <= rect.right():
                    continue
                overlap_top = max(rect.top(), other.top())
                overlap_bottom = min(rect.bottom(), other.bottom())
                if overlap_top >= overlap_bottom:
                    continue
                overlap_top -= gap_margin
                overlap_bottom += gap_margin
                if nearest_right_left is None or other.left() < (nearest_right_left - epsilon):
                    nearest_right_left = other.left()
                    right_candidates = [(other, overlap_top, overlap_bottom)]
                elif abs(other.left() - nearest_right_left) <= epsilon:
                    right_candidates.append((other, overlap_top, overlap_bottom))
            for other, overlap_top, overlap_bottom in right_candidates:
                gap_x = (rect.right() + other.left()) / 2
                vertical_lines.append((gap_x, overlap_top, overlap_bottom))

            for other in key_rects:
                if other is rect or other.right() >= rect.left():
                    continue
                overlap_top = max(rect.top(), other.top())
                overlap_bottom = min(rect.bottom(), other.bottom())
                if overlap_top >= overlap_bottom:
                    continue
                overlap_top -= gap_margin
                overlap_bottom += gap_margin
                if nearest_left_right is None or other.right() > (nearest_left_right + epsilon):
                    nearest_left_right = other.right()
                    left_candidates = [(other, overlap_top, overlap_bottom)]
                elif abs(other.right() - nearest_left_right) <= epsilon:
                    left_candidates.append((other, overlap_top, overlap_bottom))
            for other, overlap_top, overlap_bottom in left_candidates:
                gap_x = (other.right() + rect.left()) / 2
                vertical_lines.append((gap_x, overlap_top, overlap_bottom))

            if not right_candidates:
                vertical_lines.append((
                    rect.right() + gap_margin,
                    rect.top() - gap_margin,
                    rect.bottom() + gap_margin
                ))
            if not left_candidates:
                vertical_lines.append((
                    rect.left() - gap_margin,
                    rect.top() - gap_margin,
                    rect.bottom() + gap_margin
                ))

            nearest_bottom_top = None
            bottom_candidates = []
            nearest_top_bottom = None
            top_candidates = []
            for other in key_rects:
                if other is rect or other.top() <= rect.bottom():
                    continue
                overlap_left = max(rect.left(), other.left())
                overlap_right = min(rect.right(), other.right())
                if overlap_left >= overlap_right:
                    continue
                overlap_left -= gap_margin
                overlap_right += gap_margin
                if nearest_bottom_top is None or other.top() < (nearest_bottom_top - epsilon):
                    nearest_bottom_top = other.top()
                    bottom_candidates = [(other, overlap_left, overlap_right)]
                elif abs(other.top() - nearest_bottom_top) <= epsilon:
                    bottom_candidates.append((other, overlap_left, overlap_right))
            for other, overlap_left, overlap_right in bottom_candidates:
                gap_y = (rect.bottom() + other.top()) / 2
                horizontal_lines.append((gap_y, overlap_left, overlap_right))

            for other in key_rects:
                if other is rect or other.bottom() >= rect.top():
                    continue
                overlap_left = max(rect.left(), other.left())
                overlap_right = min(rect.right(), other.right())
                if overlap_left >= overlap_right:
                    continue
                overlap_left -= gap_margin
                overlap_right += gap_margin
                if nearest_top_bottom is None or other.bottom() > (nearest_top_bottom + epsilon):
                    nearest_top_bottom = other.bottom()
                    top_candidates = [(other, overlap_left, overlap_right)]
                elif abs(other.bottom() - nearest_top_bottom) <= epsilon:
                    top_candidates.append((other, overlap_left, overlap_right))
            for other, overlap_left, overlap_right in top_candidates:
                gap_y = (other.bottom() + rect.top()) / 2
                horizontal_lines.append((gap_y, overlap_left, overlap_right))

            if not bottom_candidates:
                horizontal_lines.append((
                    rect.bottom() + gap_margin,
                    rect.left() - gap_margin,
                    rect.right() + gap_margin
                ))
            if not top_candidates:
                horizontal_lines.append((
                    rect.top() - gap_margin,
                    rect.left() - gap_margin,
                    rect.right() + gap_margin
                ))

        def _dedupe(segments, precision=2):
            seen = set()
            result = []
            for seg in segments:
                key = tuple(round(value, precision) for value in seg)
                if key in seen:
                    continue
                seen.add(key)
                result.append(seg)
            return result

        vertical_lines = _dedupe(vertical_lines)
        horizontal_lines = _dedupe(horizontal_lines)

        intersections = []
        seen = set()
        def _shrunk_rect(rect):
            if shrink <= 0:
                return rect
            shrunk = rect.adjusted(shrink, shrink, -shrink, -shrink)
            if shrunk.width() <= 1 or shrunk.height() <= 1:
                return rect
            return shrunk

        shrunk_rects = [_shrunk_rect(rect) for rect in key_rects]

        for gap_x, y_min, y_max in vertical_lines:
            for gap_y, x_min, x_max in horizontal_lines:
                if (x_min - epsilon) <= gap_x <= (x_max + epsilon) and (y_min - epsilon) <= gap_y <= (y_max + epsilon):
                    point = QPointF(gap_x, gap_y)
                    if any(rect.contains(point) for rect in shrunk_rects):
                        continue
                    key = (round(point.x(), 1), round(point.y(), 1))
                    if key in seen:
                        continue
                    seen.add(key)
                    intersections.append(point)

        for rect in key_rects:
            expanded = rect.adjusted(-gap_margin, -gap_margin, gap_margin, gap_margin)
            corner_points = [
                QPointF(expanded.left(), expanded.top()),
                QPointF(expanded.right(), expanded.top()),
                QPointF(expanded.left(), expanded.bottom()),
                QPointF(expanded.right(), expanded.bottom()),
            ]
            for point in corner_points:
                if any(r.contains(point) for r in shrunk_rects):
                    continue
                key = (round(point.x(), 1), round(point.y(), 1))
                if key in seen:
                    continue
                seen.add(key)
                intersections.append(point)
        return intersections

    def _debug_key_rects(self):
        rects = []
        for widget in self.widgets:
            rects.append(QPolygonF(widget.bbox).boundingRect())
            if widget.has2:
                rects.append(QPolygonF(widget.bbox2).boundingRect())
        return rects

    def _draw_gap_intersections(self, painter):
        key_rects = self._debug_key_rects()
        avg_key_size = self._compute_avg_key_size()
        intersections = self._gap_intersections(key_rects, avg_key_size)
        if not intersections:
            return
        painter.save()
        painter.scale(self.scale, self.scale)
        painter.setRenderHint(QPainter.Antialiasing)
        radius = max(2.5, avg_key_size * 0.08)
        pen = QPen(QColor(120, 120, 120, 200))
        pen.setWidthF(1.0)
        brush = QBrush(QColor(160, 160, 160, 120))
        painter.setPen(pen)
        painter.setBrush(brush)
        for point in intersections:
            painter.drawEllipse(point, radius, radius)
        painter.restore()

    def _generate_free_slots(self):
        """Generate free slot positions based on current key layout."""
        if not self.widgets:
            self.free_slots = []
            self.canvas_bounds = None
            return

        self.canvas_bounds = QRectF(0, 0, self.width / self.scale, self.height / self.scale)
        # Use larger edge padding to leave room for combo labels at canvas edges
        avg_key_size = self._compute_avg_key_size()
        edge_padding = avg_key_size * 0.4  # Room for combo label bbox
        self.free_slots = self.slot_generator.generate_slots(
            self.widgets, self.canvas_bounds, edge_padding
        )

    def set_combo_entries(self, combo_entries, widget_keycodes):
        new_combo_entries = combo_entries or []
        # Only invalidate cache if combo entries actually changed
        if new_combo_entries == self.combo_entries and widget_keycodes == getattr(self, '_last_widget_keycodes', None):
            return
        self._last_widget_keycodes = widget_keycodes
        self.combo_entries = new_combo_entries
        self.combo_entries_numeric = []
        for idx, entry in enumerate(self.combo_entries):
            if not entry:
                continue
            inputs = entry[:4]
            output = entry[4] if len(entry) > 4 else None
            output_label = ""
            if output and output != "KC_NO":
                output_label = KeycodeDisplay.get_label(output)
            combo_label = "C({})".format(idx + 1)
            self.combo_entries_numeric.append((
                [Keycode.deserialize(code) for code in inputs],
                output_label,
                combo_label
            ))
        self.combo_widget_keycodes_numeric = {}
        if widget_keycodes:
            for widget, code in widget_keycodes.items():
                self.combo_widget_keycodes_numeric[widget] = Keycode.deserialize(code)
        self._invalidate_combo_cache()

    def set_show_combos(self, enabled):
        enabled = bool(enabled)
        if self.show_combos != enabled:
            self.show_combos = enabled
            if not enabled:
                self.show_combo_debug = False
            self.update()

    def set_show_combo_debug(self, enabled):
        enabled = bool(enabled)
        if self.show_combo_debug != enabled:
            self.show_combo_debug = enabled
            self.update()

    def _get_key_brush(self, key, normal_brush, on_brush, pressed_brush):
        """Get the appropriate brush for a key based on its state."""
        if key.pressed:
            return pressed_brush
        if key.highlight_intensity > 0:
            color = _interpolate_color(
                normal_brush.color(), on_brush.color(), key.highlight_intensity
            )
            brush = QBrush(color)
            brush.setStyle(Qt.SolidPattern)
            return brush
        if key.on:
            return on_brush
        return normal_brush

    def _collect_combo_widgets(self):
        if not self.combo_entries_numeric or not self.combo_widget_keycodes_numeric:
            return []

        keycode_to_widgets = defaultdict(list)
        for widget, code in self.combo_widget_keycodes_numeric.items():
            if code:
                keycode_to_widgets[code].append(widget)

        combos = []
        for entry, output_label, combo_label in self.combo_entries_numeric:
            keycodes = [code for code in entry if code]
            if len(keycodes) < 2:
                continue
            used = set()
            widgets = []
            for code in keycodes:
                candidates = keycode_to_widgets.get(code, [])
                widget = next((c for c in candidates if c not in used), None)
                if widget is None and candidates:
                    widget = candidates[0]
                if widget is None:
                    widgets = []
                    break
                used.add(widget)
                widgets.append(widget)
            if widgets:
                combos.append((widgets, output_label, combo_label))
        return combos

    def _compute_combo_cache(self):
        """Compute and cache combo layout data (expensive, called once)."""
        start_time = time.time()
        logger.warning("_compute_combo_cache STARTED")
        combos = self._collect_combo_widgets()
        if not combos:
            logger.warning("_compute_combo_cache: no combos, returning early")
            return []

        text_font = QApplication.font()
        base_size = text_font.pointSizeF()
        if base_size <= 0:
            base_size = float(text_font.pointSize())
        text_font.setPointSizeF(max(1.0, base_size * 0.525))
        name_font = QApplication.font()
        name_font.setPointSizeF(max(1.0, base_size * 0.45))
        name_metrics = QFontMetrics(name_font)
        label_metrics = QFontMetrics(text_font)

        key_rects = [widget.polygon.boundingRect() for widget in self.widgets]
        canvas_width = self.width / self.scale if self.scale else self.width
        canvas_height = self.height / self.scale if self.scale else self.height
        canvas_bounds = QRectF(0, 0, canvas_width, canvas_height)

        t1 = time.time()
        combo_infos = ComboInfoBuilder(label_metrics, name_metrics).build(combos)
        logger.warning(f"  ComboInfoBuilder.build: {time.time()-t1:.3f}s")

        t2 = time.time()
        avg_key_size = self._compute_avg_key_size()
        assigner = ComboSlotAssigner(self.free_slots, self.padding, canvas_bounds, key_rects, avg_key_size)
        assignments = assigner.assign(combo_infos)
        logger.warning(f"  ComboSlotAssigner.assign: {time.time()-t2:.3f}s")

        t3 = time.time()
        connector_router = ConnectorRouter(key_rects, avg_key_size)
        logger.warning(f"  ConnectorRouter init: {time.time()-t3:.3f}s, {len(connector_router.graph.waypoints)} waypoints, {len(key_rects)} keys")
        path_renderer = ConnectorPathRenderer(corner_radius=avg_key_size * 0.15)

        t4 = time.time()
        cache = []
        route_count = 0
        for info in combo_infos:
            assignment = assignments.get(info.index)
            if not assignment:
                continue
            rect = assignment["rect"]
            slot = assignment["slot"]
            connector_paths = []
            if not info.adjacent:
                for widget in info.combo_widgets:
                    key_rect = widget.polygon.boundingRect()
                    points = connector_router.route(rect.center(), key_rect)
                    connector_paths.append(path_renderer.create_path(points))
                    route_count += 1
            cache.append({
                "rect": rect, "slot": slot, "connector_paths": connector_paths,
                "output_label": info.output_label, "combo_label": info.combo_label,
                "avg_size": info.avg_size, "adjacent": info.adjacent,
            })
        logger.warning(f"  Routing loop: {time.time()-t4:.3f}s, {route_count} routes")
        elapsed = time.time() - start_time
        logger.warning(f"_compute_combo_cache FINISHED in {elapsed:.3f}s, {len(cache)} items")
        return cache

    def _draw_combos(self, qp):
        start_time = time.time()
        cache_was_none = self._combo_cache is None
        if self._combo_cache is None:
            self._combo_cache = self._compute_combo_cache()
        if not self._combo_cache:
            return

        palette = QApplication.palette()
        fill_color = QColor(palette.color(QPalette.Highlight))
        fill_color.setAlpha(40)
        border_color = QColor(palette.color(QPalette.Highlight))
        border_color.setAlpha(90)
        region_border_pens = None
        if self.show_combo_debug:
            region_border_pens = {
                SlotRegionType.INTER_KEY: QPen(QColor(80, 200, 120, 180)),
                SlotRegionType.INTERIOR: QPen(QColor(80, 160, 220, 180)),
                SlotRegionType.EXTERIOR: QPen(QColor(220, 120, 80, 180)),
                SlotRegionType.SPLIT_MIDDLE: QPen(QColor(180, 120, 220, 180)),
            }
            for pen in region_border_pens.values():
                pen.setWidthF(1.0)
        line_color = QColor(palette.color(QPalette.ButtonText))
        line_color.setAlpha(80)
        line_pen = QPen(line_color)
        line_pen.setWidthF(1.0)
        border_pen = QPen(border_color)
        border_pen.setWidthF(1.0)
        fill_brush = QBrush(fill_color)
        text_color = QColor(palette.color(QPalette.ButtonText))
        text_color.setAlpha(160)
        text_pen = QPen(text_color)
        text_font = QApplication.font()
        base_size = text_font.pointSizeF()
        if base_size <= 0:
            base_size = float(text_font.pointSize())
        text_font.setPointSizeF(max(1.0, base_size * 0.525))
        name_font = QApplication.font()
        name_font.setPointSizeF(max(1.0, base_size * 0.45))
        name_metrics = QFontMetrics(name_font)
        label_metrics = QFontMetrics(text_font)

        qp.save()
        qp.scale(self.scale, self.scale)
        qp.setRenderHint(QPainter.Antialiasing)

        for item in self._combo_cache:
            rect = item["rect"]
            slot = item["slot"]
            output_label = item["output_label"]
            combo_label = item["combo_label"]
            avg_size = item["avg_size"]
            label_lines = output_label.splitlines() if output_label else []
            label_height = len(label_lines) * label_metrics.height()
            name_height = name_metrics.height() if combo_label else 0
            text_gap = max(1.0, name_metrics.height() * 0.15) if output_label else 0

            for path in item["connector_paths"]:
                qp.setPen(line_pen)
                qp.setBrush(Qt.NoBrush)
                qp.drawPath(path)

            if region_border_pens:
                qp.setPen(region_border_pens.get(slot.region_type, border_pen))
            else:
                qp.setPen(border_pen)
            qp.setBrush(fill_brush)
            corner = avg_size * KEY_ROUNDNESS
            qp.drawRoundedRect(rect, corner, corner)

            if combo_label:
                qp.setPen(text_pen)
                if output_label:
                    total_height = name_height + label_height + text_gap
                    start_y = rect.y() + (rect.height() - total_height) / 2
                    name_rect = QRectF(rect.x(), start_y, rect.width(), name_height)
                    label_rect = QRectF(rect.x(), start_y + name_height + text_gap,
                                        rect.width(), label_height)
                    qp.setFont(name_font)
                    qp.drawText(name_rect, Qt.AlignHCenter | Qt.AlignVCenter, combo_label)
                    qp.setFont(text_font)
                    qp.drawText(label_rect, Qt.AlignHCenter | Qt.AlignVCenter, output_label)
                else:
                    qp.setFont(name_font)
                    qp.drawText(rect, Qt.AlignCenter, combo_label)

        elapsed = time.time() - start_time
        logger.warning(f"_draw_combos FINISHED in {elapsed:.3f}s, cache_was_none={cache_was_none}")
        qp.restore()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        # for regular keycaps
        regular_pen = qp.pen()
        regular_pen.setColor(QApplication.palette().color(QPalette.ButtonText))
        qp.setPen(regular_pen)
        outline_pen = QPen(QColor(140, 140, 140, 140))
        outline_pen.setWidthF(0.8)

        background_brush = QBrush()
        background_brush.setColor(QApplication.palette().color(QPalette.Button))
        background_brush.setStyle(Qt.SolidPattern)

        foreground_brush = QBrush()
        foreground_brush.setColor(QApplication.palette().color(QPalette.Button).lighter(120))
        foreground_brush.setStyle(Qt.SolidPattern)

        mask_brush = QBrush()
        mask_brush.setColor(QApplication.palette().color(QPalette.Button).lighter(Theme.mask_light_factor()))
        mask_brush.setStyle(Qt.SolidPattern)

        # for currently selected keycap
        active_pen = qp.pen()
        active_pen.setColor(QApplication.palette().color(QPalette.Highlight))
        active_pen.setWidthF(1.5)

        # for the encoder arrow
        extra_pen = regular_pen
        extra_brush = QBrush()
        extra_brush.setColor(QApplication.palette().color(QPalette.ButtonText))
        extra_brush.setStyle(Qt.SolidPattern)

        # for pressed keycaps
        background_pressed_brush = QBrush()
        background_pressed_brush.setColor(QApplication.palette().color(QPalette.Highlight))
        background_pressed_brush.setStyle(Qt.SolidPattern)

        foreground_pressed_brush = QBrush()
        foreground_pressed_brush.setColor(QApplication.palette().color(QPalette.Highlight).lighter(120))
        foreground_pressed_brush.setStyle(Qt.SolidPattern)

        background_on_brush = QBrush()
        background_on_brush.setColor(QApplication.palette().color(QPalette.Highlight).darker(150))
        background_on_brush.setStyle(Qt.SolidPattern)

        foreground_on_brush = QBrush()
        foreground_on_brush.setColor(QApplication.palette().color(QPalette.Highlight).darker(120))
        foreground_on_brush.setStyle(Qt.SolidPattern)

        mask_font = qp.font()
        mask_font.setPointSize(round(mask_font.pointSize() * 0.8))

        # Draw free slots grid (debug-only, below keys)
        if self.show_combo_debug:
            self.slot_renderer.render(qp, self.free_slots, self.scale, self.canvas_bounds)

        for idx, key in enumerate(self.widgets):
            qp.save()

            qp.scale(self.scale, self.scale)
            qp.translate(key.shift_x, key.shift_y)
            qp.translate(key.rotation_x, key.rotation_y)
            qp.rotate(key.rotation_angle)
            qp.translate(-key.rotation_x, -key.rotation_y)

            active = key.active or (self.active_key == key and not self.active_mask)

            # draw keycap background/drop-shadow
            qp.setPen(active_pen if active else Qt.NoPen)
            bg_brush = self._get_key_brush(
                key, background_brush, background_on_brush, background_pressed_brush
            )
            qp.setBrush(bg_brush)
            qp.drawPath(key.background_draw_path)

            if self.show_combo_debug:
                # draw key outline rectangle (debug layer)
                qp.setPen(outline_pen)
                qp.setBrush(Qt.NoBrush)
                qp.drawRect(key.rect)
                if key.has2:
                    qp.drawRect(key.rect2)

            # draw keycap foreground
            qp.setPen(Qt.NoPen)
            fg_brush = self._get_key_brush(
                key, foreground_brush, foreground_on_brush, foreground_pressed_brush
            )
            qp.setBrush(fg_brush)
            qp.drawPath(key.foreground_draw_path)

            # draw key text
            if key.masked:
                # draw the outer legend
                qp.setFont(mask_font)
                qp.setPen(key.color if key.color else regular_pen)
                qp.drawText(key.nonmask_rect, Qt.AlignCenter, key.text)

                # draw the inner highlight rect
                qp.setPen(active_pen if self.active_key == key and self.active_mask else Qt.NoPen)
                qp.setBrush(mask_brush)
                qp.drawRoundedRect(key.mask_rect, key.corner, key.corner)

                # draw the inner legend
                qp.setPen(key.mask_color if key.mask_color else regular_pen)
                qp.drawText(key.mask_rect, Qt.AlignCenter, key.mask_text)
            else:
                # draw the legend with optional font scaling
                qp.setPen(key.color if key.color else regular_pen)
                if key.font_scale != 1.0:
                    scaled_font = qp.font()
                    scaled_font.setPointSize(round(scaled_font.pointSize() * key.font_scale))
                    qp.setFont(scaled_font)
                if "\n" in key.text:
                    lines = key.text.split("\n")
                    has_td_header = lines and lines[0].startswith("TD(")
                    action_lines = []
                    for line in lines[1:]:
                        match = re.match(r"^([._]+)\s*(.*)$", line)
                        if match:
                            action_lines.append((match.group(1), match.group(2)))
                        else:
                            action_lines.append((None, line))
                    has_tap_dance_lines = any(prefix for prefix, _ in action_lines)
                    if has_td_header and has_tap_dance_lines:
                        fm = qp.fontMetrics()
                        text_width = fm.horizontalAdvance if hasattr(fm, "horizontalAdvance") else fm.width
                        line_height = fm.height()
                        total_height = line_height * len(lines)
                        start_y = key.text_rect.y() + (key.text_rect.height() - total_height) / 2
                        left_pad = max(2, round(key.size * SHADOW_SIDE_PADDING))
                        prefix_width = max(
                            (text_width(prefix) for prefix, _ in action_lines if prefix),
                            default=0
                        )
                        gap = max(2, text_width(" "))
                        base_x = key.text_rect.x() + left_pad
                        available_width = key.text_rect.width() - left_pad
                        for i, line in enumerate(lines):
                            line_y = round(start_y + (i * line_height))
                            if i == 0:
                                line_rect = QRect(
                                    key.text_rect.x(),
                                    line_y,
                                    key.text_rect.width(),
                                    line_height
                                )
                                qp.drawText(line_rect, Qt.AlignHCenter | Qt.AlignVCenter, line)
                                continue
                            prefix, body = action_lines[i - 1]
                            if prefix:
                                prefix_rect = QRect(base_x, line_y, prefix_width, line_height)
                                body_rect = QRect(
                                    base_x + prefix_width + gap,
                                    line_y,
                                    max(0, available_width - prefix_width - gap),
                                    line_height
                                )
                                qp.drawText(prefix_rect, Qt.AlignLeft | Qt.AlignVCenter, prefix)
                                qp.drawText(body_rect, Qt.AlignLeft | Qt.AlignVCenter, body)
                            else:
                                line_rect = QRect(base_x, line_y, available_width, line_height)
                                qp.drawText(line_rect, Qt.AlignLeft | Qt.AlignVCenter, line)
                    else:
                        qp.drawText(key.text_rect, Qt.AlignCenter, key.text)
                else:
                    qp.drawText(key.text_rect, Qt.AlignCenter, key.text)

            # draw the extra shape (encoder arrow)
            qp.setPen(extra_pen)
            qp.setBrush(extra_brush)
            qp.drawPath(key.extra_draw_path)

            qp.restore()

        if self.show_combos:
            self._draw_combos(qp)

        if self.show_combo_debug:
            self._draw_gap_intersections(qp)

        qp.end()

    def minimumSizeHint(self):
        return QSize(self.width, self.height)

    def hit_test(self, pos):
        """ Returns key, hit_masked_part """

        for key in self.widgets:
            if key.masked and key.mask_polygon.containsPoint(pos/self.scale, Qt.OddEvenFill):
                return key, True
            if key.polygon.containsPoint(pos/self.scale, Qt.OddEvenFill):
                return key, False

        return None, False

    def mousePressEvent(self, ev):
        if not self.enabled:
            return

        self.active_key, self.active_mask = self.hit_test(ev.pos())
        if self.active_key is not None:
            self.clicked.emit()
        else:
            self.deselected.emit()
        self.update()

    def resizeEvent(self, ev):
        if self.isEnabled():
            self.update_layout()

    def select_next(self):
        """ Selects next key based on their order in the keymap """

        keys_looped = self.widgets + [self.widgets[0]]
        for x, key in enumerate(keys_looped):
            if key == self.active_key:
                self.active_key = keys_looped[x + 1]
                self.active_mask = False
                self.clicked.emit()
                return

    def deselect(self):
        if self.active_key is not None:
            self.active_key = None
            self.deselected.emit()
            self.update()

    def event(self, ev):
        if not self.enabled:
            super().event(ev)

        if ev.type() == QEvent.ToolTip:
            key = self.hit_test(ev.pos())[0]
            if key is not None:
                QToolTip.showText(ev.globalPos(), key.tooltip)
            else:
                QToolTip.hideText()
        elif ev.type() in (QEvent.FontChange, QEvent.ApplicationFontChange):
            self.update_layout()
        elif ev.type() == QEvent.LayoutRequest:
            self.update_layout()
        elif ev.type() == QEvent.MouseButtonDblClick and self.active_key:
            self.anykey.emit()
        return super().event(ev)

    def set_enabled(self, val):
        self.enabled = val

    def set_scale(self, scale):
        logger.warning(f"set_scale called: {self.scale} -> {scale}")
        self.scale = scale

    def get_scale(self):
        return self.scale
