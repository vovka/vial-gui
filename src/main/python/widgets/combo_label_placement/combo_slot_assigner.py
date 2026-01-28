# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF, QRectF
from widgets.free_slots_grid import Slot, SlotRegionType


def _range_steps(start, end, step):
    values = []
    val = start
    while val <= end:
        values.append(val)
        val += step
    return values


def _slot_distance(slot, anchor):
    return math.hypot(slot.position.x() - anchor.x(), slot.position.y() - anchor.y())


def _sort_entries(entries):
    entries.sort(key=lambda entry: entry[0])
    return entries


def _split_slots(slots, info):
    preferred, fallback = [], []
    for slot in slots:
        entry = (_slot_distance(slot, info.anchor), slot)
        (preferred if info.adjacent and slot.region_type == SlotRegionType.INTER_KEY else fallback).append(entry)
    return _sort_entries(preferred), _sort_entries(fallback)


def _clamp_rect(rect, padding, canvas_bounds):
    rect_x = max(padding, min(rect.x(), canvas_bounds.width() - rect.width() - padding))
    rect_y = max(padding, min(rect.y(), canvas_bounds.height() - rect.height() - padding))
    return QRectF(rect_x, rect_y, rect.width(), rect.height())


def _rect_for_slot(slot, rect_w, rect_h, padding, canvas_bounds):
    rect = QRectF(slot.position.x() - rect_w / 2, slot.position.y() - rect_h / 2, rect_w, rect_h)
    return _clamp_rect(rect, padding, canvas_bounds)


def _rect_overlaps(rect, placed_rects):
    return any(rect.intersects(placed) for placed in placed_rects)


def _region_bonus(slot, info, avg_key_size):
    if info.adjacent:
        if slot.region_type == SlotRegionType.EXTERIOR:
            return -avg_key_size * 0.6
        if slot.region_type == SlotRegionType.INTER_KEY:
            return avg_key_size * 0.6
        return avg_key_size * 0.3
    return 0.0


def _multi_key_penalty(slot, info, avg_key_size):
    if len(info.combo_widgets) <= 2:
        return 0.0
    if slot.region_type == SlotRegionType.EXTERIOR:
        return 0.0
    return avg_key_size * 0.9


def _key_overlap_penalty(rect, key_rects):
    overlaps = [rect.intersected(key) for key in key_rects if rect.intersects(key)]
    area = sum(overlap.width() * overlap.height() for overlap in overlaps)
    rect_area = rect.width() * rect.height()
    return area / rect_area if area and rect_area else 0.0


def _spacing_penalty(rect, placed_rects, avg_key_size):
    penalty = 0.0
    for placed in placed_rects:
        dist = math.hypot(rect.center().x() - placed.center().x(),
                          rect.center().y() - placed.center().y())
        if dist < avg_key_size:
            penalty += (avg_key_size - dist) / avg_key_size
    return penalty


def _slot_cost(slot, rect, info, avg_key_size, key_rects, placed_rects):
    distance_cost = _slot_distance(slot, info.anchor)
    overlap_cost = _key_overlap_penalty(rect, key_rects) * avg_key_size * 2.0
    spacing_cost = _spacing_penalty(rect, placed_rects, avg_key_size) * avg_key_size
    clearance_bonus = slot.clearance_score * 0.2
    region_bonus = _region_bonus(slot, info, avg_key_size)
    multi_key_penalty = _multi_key_penalty(slot, info, avg_key_size)
    return distance_cost + overlap_cost + spacing_cost + multi_key_penalty - clearance_bonus - region_bonus


class ComboSlotAssigner:
    def __init__(self, slots, padding, canvas_bounds, key_rects, avg_key_size):
        self.slots = list(slots or [])
        self.padding = padding
        self.canvas_bounds = canvas_bounds
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.placed_rects = []
        self.used_slot_ids = set()

    def assign(self, combo_infos):
        assignments = {}
        for info in self._sorted_infos(combo_infos):
            choice = self._choose_slot(info)
            if choice:
                assignments[info.index] = {"slot": choice[0], "rect": choice[1]}
                self._record_choice(choice)
        return assignments

    def _sorted_infos(self, combo_infos):
        return sorted(combo_infos, key=self._sort_key)

    def _sort_key(self, info):
        return (-(info.rect_w * info.rect_h), -len(info.combo_widgets))

    def _choose_slot(self, info):
        best = self._best_from_candidates(info, self._candidate_slots(info))
        best = best or self._best_from_candidates(info, self._fallback_slots())
        return best or self._best_from_spiral(info)

    def _candidate_slots(self, info):
        preferred, fallback = _split_slots(self.slots, info)
        candidates = [slot for _, slot in preferred[:20]]
        candidates += [slot for _, slot in fallback[:30]]
        return candidates if len(candidates) >= 10 else [slot for _, slot in preferred + fallback]

    def _best_from_candidates(self, info, slots):
        best = None
        for slot in slots:
            candidate = self._evaluate_slot(info, slot)
            best = self._pick_best(best, candidate)
        return self._strip_cost(best)

    def _evaluate_slot(self, info, slot):
        if id(slot) in self.used_slot_ids:
            return None
        rect = _rect_for_slot(slot, info.rect_w, info.rect_h, self.padding, self.canvas_bounds)
        if _rect_overlaps(rect, self.placed_rects):
            return None
        cost = _slot_cost(slot, rect, info, self.avg_key_size, self.key_rects, self.placed_rects)
        return (cost, slot, rect)

    def _pick_best(self, best, candidate):
        if not candidate:
            return best
        if not best or candidate[0] < best[0]:
            return candidate
        return best

    def _strip_cost(self, best):
        return (best[1], best[2]) if best else None

    def _record_choice(self, choice):
        slot, rect = choice
        self.used_slot_ids.add(id(slot))
        self.placed_rects.append(rect)

    def _fallback_slots(self):
        points = []
        step = max(8.0, self.avg_key_size * 0.4)
        for x in _range_steps(self.padding, self.canvas_bounds.width() - self.padding, step):
            points.append(QPointF(x, self.padding))
            points.append(QPointF(x, self.canvas_bounds.height() - self.padding))
        for y in _range_steps(self.padding, self.canvas_bounds.height() - self.padding, step):
            points.append(QPointF(self.padding, y))
            points.append(QPointF(self.canvas_bounds.width() - self.padding, y))
        return [Slot(point, SlotRegionType.EXTERIOR, 0.0) for point in points]

    def _best_from_spiral(self, info):
        for slot in self._spiral_slots(info.anchor):
            candidate = self._evaluate_slot(info, slot)
            if candidate:
                return (candidate[1], candidate[2])
        return None

    def _spiral_slots(self, anchor):
        step = max(4.0, self.avg_key_size * 0.2)
        for radius in range(1, 8):
            offset = step * radius
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset),
                           (-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset)]:
                point = QPointF(anchor.x() + dx, anchor.y() + dy)
                yield Slot(point, SlotRegionType.INTERIOR, 0.0)
