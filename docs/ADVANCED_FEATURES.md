# Advanced features

Updated 25 October 2026. Install with `pip install -r requirement.txt` from the project root; use Python 3.11 on Windows. See the [README](../README.md) for full setup.

## Mode selection by gesture or UI

Choose Mouse, Volume, or Air keyboard above the tabs. Manual selection pauses output; enable it again when ready.

For hands-free switching, fold all four non-thumb fingers and hold an upright **👍 thumbs-up for 1.2 seconds**. Use the left hand in two-hand mode, or the visible hand in one-hand mode. The order is **Mouse → Volume → Air keyboard → Mouse**.

The HUD shows hold progress and the selected mode. One hold changes one mode; release for at least 0.25 seconds before switching again. Output is suspended while the gesture is held. Active control resumes on release; an already paused session stays paused. The selector and guide synchronize with the worker-selected mode.

A sideways thumb or an extended non-thumb finger does not qualify. Mode switching requires the camera to be running. It works across all three control modes, including while control is paused.

## Click and drag

In Mouse mode, the left hand pinches in two-hand mode; the pointing hand pinches in one-hand mode.

- **Click:** Pinch briefly, then release. A detected pinch lasting at least 20 ms can click, subject to cooldown. Separate fingertips before another click.
- **Drag:** Aim at a window title bar or draggable item, hold the pinch for the configured duration (default 0.45 seconds), move the pointing hand, then release to drop.

A pending pinch keeps cursor mode through its release frame. Opening the hand therefore completes the click/drop before selecting palm scrolling. A long hold emits mouse-down instead of a click; release emits mouse-up without an extra click.

Drag movement starts relative to the grab position, avoiding the fingertip jump caused by closing a pinch. In one-hand mode the pointer is steadied during pinch formation, then follows the hand once dragging starts. In two-hand mode the right pointer can move while the left pinches.

Losing either required hand, pausing, changing mode, stopping, or exiting releases held input. The corner failsafe remains active, with a cleanup exception only to ensure mouse-up can be sent. Some elevated applications reject ordinary injected input.

### Drag freeze correction

Camera capture, hand tracking, and input output now run in engine.py independently of Tk. OpenCV preview/event handling runs on a second thread with only the newest frame queued. A UI window-move loop cannot block gesture tracking or pinch release. The preview itself may temporarily stop repainting while that preview window is being moved; tracking still continues.

Active Windows drag movement uses SendInput movement events instead of only repositioning the pointer. Close older app copies and restart after updating. If a drag remains stuck, use Pause/Stop and check that both required hands are visible; record whether the freeze affects only the preview repaint or all tracking.

## Palm scrolling and auto-scroll

In two-hand Mouse mode, open either palm and make one clear upward/downward movement. That locks continuous scroll direction. Holding still or returning the hand does not reverse it. **Close the palm to stop; reopen to choose the opposite direction.** The left palm wins if both are open and can scroll alone without the right hand.

Right index + middle fingers select auto-scroll in the last palm direction. Without a previous direction, fingertip orientation relative to the wrist supplies the initial direction. Return to one pointing finger to stop; close any open left palm as well.

One-hand mode differs: open palm pauses; two raised fingers scroll according to displacement from a starting height. Return to that height or lower the middle finger to stop.

Scroll amount accepts any positive finite number. Values above 10 work, but large values can scroll very quickly. Invalid input keeps the last valid amount and blocks saving until corrected.

## Windows volume

1. Select Volume, or use the thumbs-up cycle.
2. Enable control if paused.
3. Use the right hand in two-hand mode, or the visible hand in one-hand mode.
4. Widen thumb/index distance to raise volume; narrow it to lower volume.

The preview shows a fingertip line, volume meter and percentage. The gap is measured relative to palm size. Changes approach the target gradually, with updates around ten times per second and at most five percentage points per update. Pause or remove the hand to hold the level. Mouse clicks and scrolling are suppressed in this mode.

The default Windows multimedia playback endpoint is controlled through [Core Audio](https://learn.microsoft.com/en-us/windows/win32/api/endpointvolume/nf-endpointvolume-iaudioendpointvolume-setmastervolumelevelscalar). Mute is not toggled. After changing output devices, pause/resume or change modes to reopen the endpoint. An unavailable endpoint reports an error and stops processing.

## Air keyboard

1. Select Air keyboard and enable control.
2. Focus the target application/text field with the physical mouse.
3. Aim the right index at a camera-preview key (visible hand in one-hand mode).
4. Pinch with the left hand in two-hand mode, or the same hand in one-hand mode.
5. Hold briefly, around 80 ms, then release before the next key.

The target locks when the pinch starts. Holding a pinch emits one key, not repeated characters. Missing hands, pause and mode changes cancel pending selections. OS cursor movement is suspended in this mode.

| Key | Action |
| --- | --- |
| Letters | Basic English QWERTY typing |
| Shift | Uppercase the next letter; press again to toggle off |
| 123 / ABC | Switch numbers/punctuation and letters |
| Space | Space |
| Back | Backspace |
| Enter | Return/Enter |

Input goes to the currently focused application. There is no internal text buffer, automatic focus restoration, or multilingual IME. Enable first, then focus the intended field. Pause before clicking back into the controller when finished.

## Sci-fi HUD

Toggle Sci-fi HUD above the tabs. It adds a translucent status strip, cyan hand brackets, hand count, control mode, drag state, mode-switch countdown and stop hint. Functional keyboard keys/hover and volume indicators remain available when decorative HUD is disabled. Save settings persists HUD visibility; the selected control mode starts as Mouse on a new launch.

## Controls and recovery

- Space in the controller: pause/resume; editing inputs and the mode selector are exempt.
- Escape in the controller: stop camera.
- Q in the preview, closing the preview, or Stop camera: stop processing.
- Recenter hand: use the next cursor gesture's comfortable fingertip height as vertical center.
- Save settings persists adjustments; Restore defaults needs Save to persist.

Tk widgets, tracking and preview communicate using queues. Stop is asynchronous so the GUI can remain responsive while worker-owned resources are released. Allow it to finish before starting another camera session.

## Verification

```powershell
.venv\Scripts\python.exe -m unittest check_click_release check_mode_gesture -v
```

The available modules contain 11 mocked-output checks. They cover click release into an open palm, fast pinch acceptance, unchanged drag release, cancelled clicks, gesture hold/release, complete mode cycling, paused state, manual cancellation, and stale-settings protection.

Earlier tests verified worker/preview isolation, keyboard selection, volume mapping and cleanup; those historical test files are no longer present. A read-only Windows audio connection and UI checks passed during development. These checks do not certify live webcam recognition, natural movement, or successful input in every target application.
