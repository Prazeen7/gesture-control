# Development history

Consolidated implementation history through 25 October 2026. This is a record of the project's evolution, not a list of simultaneously available modes. For current behavior, use the [user guide](USER_GUIDE.md).

| Stage | Changes | Current status |
| --- | --- | --- |
| Initial controller | Webcam preview, index cursor mapping, pinch click, two-finger scroll, open-palm pause | Evolved into the desktop application |
| Desktop panel | Gesture instructions, camera controls, live tuning, Save settings, Restore defaults | Available |
| Cursor tuning | Smaller vertical working area, time-based adaptive smoothing, fractional scrolling, pinch release hysteresis | Available |
| Comfortable reach | Comfortable-height recentering, Vertical hand travel slider, preview boundary lines | Available |
| Click alternative | Index-bend gesture and selector | Removed; pinch remains the click gesture |
| Scroll tuning | Removed Scroll amount ceiling of 10 and internal rate cap; positive numeric input | Available |
| Two-hand mode | Right pointer, left pinch click, hand identity assignment | Available; scrolling roles expanded afterward |
| Mode-aware guide | Separate gesture instructions for one/two-hand use and emoji illustrations | Available |
| Right-palm scrolling | Whole-hand swipe scrolling and right two-finger auto-scroll | Palm behavior replaced by direction lock |
| Either-palm scrolling | Left palm can scroll alone; left priority when both palms are open | Available |
| Return-stroke correction | First clear palm movement locks continuous direction so repositioning does not reverse scrolling | Current two-hand palm behavior |
| UI redesign | Persistent controls/status, guide cards, setting descriptions, scrollable pages | Available |
| Camera handling | Windows backend fallback, failed-capture cleanup, stop-before-switch lifecycle, rollback attempt | Implemented; physical switching still needs validation |
| Navigation cleanup | Removed camera-index selector and Camera setup page; two fixed equal-size navigation buttons | Current UI |
| Documentation consolidation | Replaced accumulated README fragments with current user, technical, and history documents | This documentation update |

## Important behavior changes

- An open palm pauses only in one-hand mode. In two-hand mode it selects scrolling.
- Current two-hand palm scrolling continues when the hand holds still or returns downward. Close the palm to stop.
- Left two-finger scrolling from an earlier two-hand design is no longer the active mapping. Right two fingers select auto-scroll.
- Scroll amount was renamed temporarily during development; its current UI label is **Scroll amount**.
- The camera-index setting remains internally, but the current UI uses the default webcam and exposes no selector.
- Tests and UI checks do not replace live webcam validation. Smoothness and gesture reliability have been iterated in response to user feedback, rather than certified across camera hardware.
