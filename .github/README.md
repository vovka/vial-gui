# Vial GUI Fork

## Original README

See [README.md](/README.md) for the upstream overview, release links, and development setup.

## What This Fork Changes

This fork focuses on making dynamic behavior visible directly in the GUI and improving navigation so key assignments are easier to understand at a glance.

- Overall UI clarity: original -> enhanced layout with dynamic previews and overlays.

  <div align="center">
    <img src="/docs/images/original-ui.png" alt="Original Vial GUI screenshot" />
    <br />
    &darr;
    <br />
    <img src="/docs/images/fork-ui.png" alt="Enhanced fork UI screenshot" />
  </div>
- Macro key labels: M(n) labels with inline previews of text or key actions (including down/up), so you can identify macros without opening the editor; previews refresh after edits.

  <div align="center">
    <img src="/docs/images/macro-keys-before.png" alt="Macro key labels before" />
    <br />
    &darr;
    <br />
    <img src="/docs/images/macro-keys-after.png" alt="Macro key labels after" />
  </div>
- Macro text preview: compact multi-line text previews inside key labels.

  <div align="center">
    <img src="/docs/images/macro-text-before.png" alt="Macro text preview before" />
    <br />
    &darr;
    <br />
    <img src="/docs/images/macro-text-after.png" alt="Macro text preview after" />
  </div>
- Tap dance previews: dot/underscore action lines in a consistent order, aligned layout, and font scaling that keeps the key grid stable.

  <div align="center">
    <img src="/docs/images/tap-dance-before.png" alt="Tap dance preview before" />
    <br />
    &darr;
    <br />
    <img src="/docs/images/tap-dance-after.png" alt="Tap dance preview after" />
  </div>
- Combo overlays: keymap shows combo overlays with labels/output previews; View > Combos toggle (Ctrl+C) remembers your choice; masked keycodes expand to show their inner key.

  <div align="center">
    <img src="/docs/images/combos-after.png" alt="Combos overlay preview" />
  </div>

- Free slots: unused entries are italicized in dynamic tabs (macros, tap dance, combos, key overrides, alt-repeat).

  <div align="center">
    <img src="/docs/images/free-slots-tabs.png" alt="Free slots in tabs" />
  </div>
- Navigation and zoom: Ctrl+PgUp/PgDn for tabs, Alt+PgUp/PgDn for subtabs, Alt+1..9 for layers via a Navigation menu; UI zoom and keymap zoom persist across restarts.

  <div align="center">
    <img src="/docs/images/navigation-menu.png" alt="Navigation menu shortcuts" />
  </div>
