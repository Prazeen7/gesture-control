# Technical reference

Implementation snapshot: 25 October 2026. This document describes the source currently in the project, including internal behavior that is not exposed in the UI.

## Advanced controls

The application now includes drag-and-drop, Windows volume, air typing, and a camera HUD. See [Advanced features](ADVANCED_FEATURES.md) for current mode behavior and verification. interactions.py contains pure interaction state machines; features.py dispatches and renders the modes; system_volume.py wraps Core Audio.

## Architecture

| File | Responsibility |
| --- | --- |
| main.py | Application state, Tk lifecycle, frame loop, gesture dispatch, click gating, settings persistence |
| ui.py | Styling, two equal-size navigation buttons, scrollable guide/settings pages, persistent controls, guide cards |
| motion.py | Finger classification, hand assignment, cursor mapping/filtering, palm direction lock, auto-scroll, one-hand scroll accumulator |
| camera.py | Backend fallback, frame validation, release of unsuccessful captures |
| settings.json | Local preferences loaded at startup and overwritten by Save settings |

## Frame pipeline

1. Read the camera frame and mirror it horizontally.
2. Convert BGR to RGB and process with MediaPipe Hands.
3. Draw landmarks for detected hands.
4. Assign pointer/action roles and classify gestures.
5. Apply the gesture transition delay and dispatch movement, clicking, or scrolling if control is enabled.
6. Draw status and vertical working-area lines, display the OpenCV preview, and process Q/window closure.
7. Continue the tracking worker loop; submit the frame to the independent preview queue.

The camera and gesture loop now runs independently in engine.py. Camera preview runs in camera_preview.py on a second worker, with only the newest frame retained. Tk sends commands and polls status, and does not schedule frame processing. Stop requests release input and camera/tracker/audio resources on the processing thread.

MediaPipe is configured for up to two hands with detection and tracking confidence thresholds of 0.7. Camera startup requests 640 × 480; the actual camera may negotiate a different resolution.

## Recognition and priority

### Hand roles

`hand_roles()` uses MediaPipe handedness labels for mirrored input. In two-hand mode Right supplies cursor landmarks and Left supplies click landmarks. Detection order does not change the assigned roles. In one-hand mode the first detected hand supplies controls.

An open left palm can enter scrolling without a detected right hand. That fallback is restricted to scrolling; it does not grant the left hand cursor control.

### Finger classification

`raised_fingers()` compares each fingertip's 2D distance from the wrist to its proximal joint's distance from the wrist. A fingertip is classified as extended when its distance exceeds the joint distance by a factor of 1.12. The four non-thumb fingers are tested. Open-palm recognition does not explicitly require an extended thumb.

### Two-hand gesture priority

1. Left open palm.
2. Right open palm.
3. Right index + middle raised, with at least one of ring/little fingers folded: auto-scroll.
4. Cursor movement and left pinch clicking.

Gesture candidates must remain stable for about 100 ms before changing the active mode. Palm source changes reanchor scroll initialization. Pausing, stopping, changing hand mode, or losing the required hand resets relevant gesture state.

### One-hand priority

Open-palm pause, then two-finger displacement scroll, then cursor/click mode.

## Cursor mapping and smoothing

`screen_target()` maps normalized fingertip coordinates to primary-screen coordinates. The horizontal center is 0.5; the vertical center is captured from the first cursor gesture after enabling, changing hand mode, or requesting Recenter hand.

Normalized coordinates are computed as:

```text
horizontal = clamp(0.5 + (index.x - 0.5) * mouse_speed / 0.7, 0, 1)
vertical   = clamp(0.5 + (index.y - center_y) * mouse_speed / vertical_range, 0, 1)
```

Output stays one pixel inside the top/left and two pixels inside the bottom/right screen bounds. Preview lines show the nominal vertical active area.

`follow()` ignores target distances under 1.5 pixels and applies an exponential filter. Responsiveness sets the base response, and greater target distance increases the response to reduce travel lag. Elapsed time is used rather than a fixed per-frame smoothing factor. The caller bounds elapsed time to 1–100 ms.

In two-hand mode, left-hand pinching does not freeze right-hand cursor movement. One-hand cursor movement is held during a pinch until dragging starts, then follows the finger with the mouse button held. Mouse output uses PyAutoGUI with pause set to zero and failsafe enabled.

## Click gating

Pinch distance is measured between thumb and index tips in normalized 2D coordinates. Entry uses `pinch_threshold`; release uses 1.45 times that threshold to reduce flicker. A short pinch must persist for approximately 45 ms and satisfy click cooldown; it clicks on release. Holding for drag_hold (default 0.45 seconds) emits left mouse-down. Release emits mouse-up without an extra click. Pause, loss of tracking, scrolling, mode changes, and exit cancel pending clicks and release held buttons.

Changing modes or losing the required hand blocks a held pinch from immediately creating a click on reentry. Index-bend clicking was removed. Only left clicks are emitted.

## Scroll implementations

### Palm direction lock: active two-hand behavior

Whole-hand vertical position averages the wrist, four finger-base landmarks, and four fingertips. A new palm gesture records an anchor and clears its stroke direction. Displacement of at least `max(0.008, scroll_threshold)` selects up/down.

After selection, wheel steps accumulate continuously at approximately:

```text
signed wheel steps per second = direction * scroll_step * 5
```

The return stroke cannot reverse direction. Closing the palm exits the gesture. Reopening records a fresh anchor. Fractional wheel steps are retained between frames and whole steps are emitted with PyAutoGUI. Elapsed time is capped at 0.1 seconds per update to avoid a large catch-up after stalls.

### Right two-finger auto-scroll

Uses the same rate and the most recent palm direction. With no stored direction, fingertip orientation relative to the wrist chooses an initial direction. Leaving the pose stops this mode unless a higher-priority palm gesture is active.

### One-hand displacement scroll

`ScrollMotion` stores the initial average index/middle fingertip height. Beyond the dead zone, rate depends on displacement, Scroll amount, and elapsed time. Returning to the anchor clears the fractional remainder and stops output.

### Retained helper branch

`PalmScroll.update(mode='palm', ...)` retains direct swipe behavior and test coverage. The current UI dispatches `palm_latched` for open-palm scrolling, so the direct-swipe branch is not the active two-hand behavior.

There is no application-level ceiling of 10 for Scroll amount and no internal scroll-rate cap. The emitted events remain discrete wheel steps; application and OS behavior can differ from a native touchpad.

## Camera lifecycle

Windows startup attempts DirectShow, Media Foundation, then automatic backend selection. Other platforms use automatic selection. Each backend gets up to five initial frame-read attempts. A capture is accepted only if it opens and returns a nonempty frame; unsuccessful attempts are released.

The current UI initializes the camera choice to index 0. It does not display a selector or Camera setup tab. The internal `camera_index` key and camera-switch/rollback code remain for compatibility, but editing that JSON key does not change the current UI's default camera selection.

`start()` validates the internal selection, returns if that camera is already connected, stops the current capture before connecting another, and attempts to reconnect the previous capture on startup failure. Control begins paused. Live physical camera behavior still needs hardware validation.

## Configuration

`load_settings()` merges recognized finite numeric values with built-in defaults and falls back on unreadable or malformed settings. Unknown keys are ignored. UI sliders clamp their displayed values to supported ranges. The UI uses a Boolean variable for Two-hand mode.

| JSON key | Built-in default | UI label |
| --- | --- | --- |
| mouse_speed | 1.0 | Mouse speed |
| vertical_range | 0.20 | Vertical hand travel |
| smooth | 0.50 | Cursor responsiveness |
| pinch_threshold | 0.045 | Pinch sensitivity |
| click_cooldown | 0.25 | Click cooldown |
| scroll_threshold | 0.015 | Scroll activation distance |
| scroll_step | 2 | Scroll amount |
| two_hands | true | Two-hand mode |
| camera_index | 0 | Internal; selector removed |

Save settings writes the current UI values to settings.json. The currently saved file can differ from defaults; documentation does not reset it. In particular, a large saved Scroll amount remains active at startup. Restore defaults changes the UI immediately, and Save is needed to persist those defaults.

## Tests and verification

```powershell
.venv\Scripts\python.exe -m unittest discover -p "test_*.py"
.venv\Scripts\python.exe -m py_compile main.py ui.py motion.py camera.py
```

The current checkout contains test_features.py with 18 tests for drag, keyboard, volume mapping, output cleanup, and HUD. Earlier helper test modules are no longer present. See ADVANCED_FEATURES.md for current verification details.

During development, the motion suite and UI checks passed. UI checks included mode switching, scroll-value persistence, smaller windows, and equal selected/unselected navigation dimensions. Camera backend fallback and physical camera switching have not been verified against the user's hardware. Automated helper tests do not establish live tracking accuracy, correct driver behavior, or natural-feeling mouse interaction.

## Current limitations

- Primary-screen mapping; no multi-monitor calibration.
- Camera-driver reads may still block their own tracking worker; Tk and preview processing are independent.
- Hand classification depends on landmark quality and pose.
- No native precision-touchpad events or kinetic scrolling.
- No right-click or double-click gesture, custom model training, or multilingual IME input. Basic English air typing, left-button dragging, and Windows volume control are implemented.
- No dependency lockfile or packaged desktop installer.


