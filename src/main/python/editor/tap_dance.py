# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QTabWidget, QWidget, QSizePolicy, QGridLayout, QVBoxLayout, QLabel, QHBoxLayout, \
    QPushButton, QSpinBox

from protocol.constants import VIAL_PROTOCOL_DYNAMIC
from keycodes.keycodes import update_tap_dance_labels, find_unused_tap_dances
from widgets.key_widget import KeyWidget
from tabbed_keycodes import TabbedKeycodes
from util import tr, KeycodeDisplay
from vial_device import VialKeyboard
from editor.basic_editor import BasicEditor
from widgets.tab_widget_keycodes import TabWidgetWithKeycodes


class TapDanceEntryUI(QObject):

    key_changed = pyqtSignal()
    timing_changed = pyqtSignal()

    def __init__(self, idx):
        super().__init__()

        self.idx = idx
        self.container = QGridLayout()
        self.populate_container()

        w = QWidget()
        w.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        w.setLayout(self.container)
        l = QVBoxLayout()
        l.addStretch()
        l.addSpacing(10)
        l.addWidget(w)
        l.setAlignment(w, QtCore.Qt.AlignHCenter)
        l.addSpacing(10)
        lbl = QLabel("Use <code>TD({})</code> to set up this action in the keymap.".format(self.idx))
        l.addWidget(lbl)
        l.setAlignment(lbl, QtCore.Qt.AlignHCenter)
        l.addStretch()
        self.w2 = QWidget()
        self.w2.setLayout(l)

    def populate_container(self):
        self.container.addWidget(QLabel("On tap"), 0, 0)
        self.kc_on_tap = KeyWidget()
        self.kc_on_tap.changed.connect(self.on_key_changed)
        self.container.addWidget(self.kc_on_tap, 0, 1)
        self.container.addWidget(QLabel("On hold"), 1, 0)
        self.kc_on_hold = KeyWidget()
        self.kc_on_hold.changed.connect(self.on_key_changed)
        self.container.addWidget(self.kc_on_hold, 1, 1)
        self.container.addWidget(QLabel("On double tap"), 2, 0)
        self.kc_on_double_tap = KeyWidget()
        self.kc_on_double_tap.changed.connect(self.on_key_changed)
        self.container.addWidget(self.kc_on_double_tap, 2, 1)
        self.container.addWidget(QLabel("On tap + hold"), 3, 0)
        self.kc_on_tap_hold = KeyWidget()
        self.kc_on_tap_hold.changed.connect(self.on_key_changed)
        self.container.addWidget(self.kc_on_tap_hold, 3, 1)
        self.container.addWidget(QLabel("Tapping term (ms)"), 4, 0)
        self.txt_tapping_term = QSpinBox()
        self.txt_tapping_term.valueChanged.connect(self.on_timing_changed)
        self.txt_tapping_term.setMinimum(0)
        self.txt_tapping_term.setMaximum(10000)
        self.container.addWidget(self.txt_tapping_term, 4, 1)

    def widget(self):
        return self.w2

    def load(self, data):
        objs = [self.kc_on_tap, self.kc_on_hold, self.kc_on_double_tap, self.kc_on_tap_hold, self.txt_tapping_term]
        for o in objs:
            o.blockSignals(True)

        self.kc_on_tap.set_keycode(data[0])
        self.kc_on_hold.set_keycode(data[1])
        self.kc_on_double_tap.set_keycode(data[2])
        self.kc_on_tap_hold.set_keycode(data[3])
        self.txt_tapping_term.setValue(data[4])

        for o in objs:
            o.blockSignals(False)

    def save(self):
        return (
            self.kc_on_tap.keycode,
            self.kc_on_hold.keycode,
            self.kc_on_double_tap.keycode,
            self.kc_on_tap_hold.keycode,
            self.txt_tapping_term.value()
        )

    def on_key_changed(self):
        self.key_changed.emit()

    def on_timing_changed(self):
        self.timing_changed.emit()


class TapDance(BasicEditor):

    def __init__(self):
        super().__init__()
        self.keyboard = None

        self.tap_dance_entries = []
        self.tap_dance_entries_available = []
        self.tabs = TabWidgetWithKeycodes()
        for x in range(128):
            entry = TapDanceEntryUI(x)
            entry.key_changed.connect(self.on_key_changed)
            entry.timing_changed.connect(self.on_timing_changed)
            self.tap_dance_entries_available.append(entry)

        self.addWidget(self.tabs)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.btn_save = QPushButton(tr("TapDance", "Save"))
        self.btn_save.clicked.connect(self.on_save)
        self.btn_revert = QPushButton(tr("TapDance", "Revert"))
        self.btn_revert.clicked.connect(self.on_revert)
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_revert)
        self.addLayout(buttons)

    def rebuild_ui(self):
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
        self.tap_dance_entries = self.tap_dance_entries_available[:self.keyboard.tap_dance_count]
        for x, e in enumerate(self.tap_dance_entries):
            self.tabs.addTab(e.widget(), str(x))
        self.reload_ui()

    def reload_ui(self):
        for x, e in enumerate(self.tap_dance_entries):
            e.load(self.keyboard.tap_dance_get(x))
        self.update_modified_state()

    def on_save(self):
        for x, e in enumerate(self.tap_dance_entries):
            self.keyboard.tap_dance_set(x, self.tap_dance_entries[x].save())
        update_tap_dance_labels(self.keyboard)
        KeycodeDisplay.refresh_clients()
        self.update_modified_state()

    def on_revert(self):
        self.keyboard.reload_dynamic()
        self.reload_ui()
        update_tap_dance_labels(self.keyboard)
        KeycodeDisplay.refresh_clients()

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard
            self.rebuild_ui()

    def valid(self):
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.vial_protocol >= VIAL_PROTOCOL_DYNAMIC
                and self.device.keyboard.tap_dance_count > 0)

    def on_key_changed(self):
        self.on_save()

    def update_modified_state(self):
        """ Update indication of which tabs are modified, and keep Save button enabled only if it's needed """
        has_changes = False
        unused_tap_dances = find_unused_tap_dances(self.keyboard)
        for x, e in enumerate(self.tap_dance_entries):
            current = self.tap_dance_entries[x].save()
            is_free = self.is_entry_free(current)
            if current != self.keyboard.tap_dance_get(x):
                has_changes = True
                self.tabs.set_tab_label(x, "{}*".format(x), is_free)
            else:
                needs_attention = x in unused_tap_dances
                attention_tooltip = unused_tap_dances.get(x)
                self.tabs.set_tab_label(x, str(x), is_free, needs_attention, attention_tooltip)
        self.btn_save.setEnabled(has_changes)

    def is_entry_free(self, entry):
        return all(keycode == "KC_NO" for keycode in entry[:4])

    def on_timing_changed(self):
        self.update_modified_state()
