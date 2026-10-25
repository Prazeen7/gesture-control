# Technical reference

Current implementation: 25 October 2026. For gesture instructions, see [Advanced features](ADVANCED_FEATURES.md) and the [User guide](USER_GUIDE.md).

## Runtime dependencies

Use Python 3.11 and install `pip install -r requirement.txt` from the repository root. The file pins direct dependencies:

| Package | Version | Purpose |
| --- | --- | --- |
| mediapipe | 0.10.21 | Legacy `mp.solutions.hands` tracking |
| opencv-contrib-python | 4.11.0.86 | Camera frames, image operations, HighGUI preview; satisfies MediaPipe's OpenCV dependency |
| numpy | 1.26.4 | Array compatibility for the camera/vision stack |
| PyAutoGUI | 0.9.54 | Mouse buttons, clicks, wheel output, keyboard simulation, screen geometry |

Install only one OpenCV distribution because its variants share cv2. Tkinter, ctypes, threading, queue, json, math, and pathlib come with Python. The file pins direct packages; it is not a complete transitive dependency lock. Node/Hyperframes/FFmpeg belong to the optional video-production folder and are not runtime requirements.

## Thread architecture

| Owner | Module | Work |
| --- | --- | --- |
| Tk main thread | main.py, ui.py | Widgets, settings variables, user actions, guide rendering, queued status/error handling |
| Tracking/input worker | engine.py | Open camera, read frames, run MediaPipe, classify gestures, emit mouse/keyboard/volume output, render HUD pixels |
| Preview worker | camera_preview.py | OpenCV window/event handling and displaying the newest annotated frame |

Tk reads settings into plain snapshots and sends queue commands. The tracking thread never reads Tk variables or invokes Tk widgets. A mode selected by gesture is sent back as a message; the GUI updates its selector and guide. Routine settings snapshots do not overwrite the worker's gesture-selected mode. Manual changes use an explicit select_mode command.

The preview queue holds **one frame**. New frames replace stale ones; slow or blocked preview repainting does not build a backlog or block tracking. Windows modal window movement on a UI thread therefore does not stop the input worker from detecting pinch release.

All camera, MediaPipe, drag, and volume resources are owned/cleaned by the processing worker. The GUI requests stop instead of joining synchronously. Closing waits through normal UI polling for worker completion. A stop releases held mouse input and the audio endpoint, closes capture/tracker resources, and signals the preview to close.

## Frame flow

1. Read the default camera, mirror horizontally, convert BGR to RGB.
2. Run MediaPipe Hands with up to two hands and confidence thresholds of 0.7.
3. Resolve Right/Left roles from handedness labels.
4. Check the global thumbs-up mode gesture before interpreting mode-specific actions.
5. Dispatch the selected mode if enabled; suppress actions while a mode gesture is held.
6. Draw status, hand landmarks, working-area lines, and mode overlays.
7. Submit the latest frame to the preview queue and continue the worker loop.

The preview handles Q and window closure by requesting a worker stop. Tk handles Space/Escape and GUI controls. A blocking camera driver can still block its own processing worker; separate threads do not guarantee camera-driver responsiveness.

## Gesture primitives

### Roles and finger extension

Two-hand mode assigns Right to pointing and Left to clicks. Either open palm can scroll; Left has priority. An open left palm can scroll without the right hand present, but does not gain cursor control. One-hand mode uses the first detected hand.

A non-thumb finger is extended when fingertip-to-wrist 2D distance exceeds proximal-joint-to-wrist distance by 1.12. Open palm tests the four non-thumb fingers; thumb extension is not required for that gesture.

### Mode cycle

A thumbs-up requires all four non-thumb fingers folded, the thumb tip above its preceding joint/base, and a predominantly upward thumb segment. In two-hand mode only Left is eligible; in one-hand mode the pointer hand is eligible.

`ModeCycle` requires a 1.2-second hold and emits one switch per hold. A 0.25-second release rearms it. The order is Mouse → Volume → Air keyboard. Actions are suspended during detection/hold. Switching releases drag and resets pending mode actions. Release resumes only if input was previously enabled. Explicit manual mode selection cancels pending automatic resume and pauses control.

### Mouse priority and transitions

A pending pinch/drag in cursor mode retains that mode through the release frame, so the newly opened hand cannot cancel a click by selecting scroll/pause. Otherwise two-hand priority is left palm, right palm, right two fingers, then cursor/click. One-hand priority is open-palm pause, two-finger scroll, then cursor/click.

Normal gesture transitions settle for about 100 ms. Pinch entry uses pinch_threshold; release uses 1.45 times the entry threshold. The click/drag state machine requires a release before arming a fresh pinch after a cancellation.

## Cursor and drag

`screen_target()` uses a fixed horizontal center and a comfortable vertical center recorded from the next cursor gesture after enable/recenter. Normalized target:

```text
x = clamp(0.5 + (index.x - 0.5) * mouse_speed / 0.7, 0, 1)
y = clamp(0.5 + (index.y - center_y) * mouse_speed / vertical_range, 0, 1)
```

The target is clamped slightly inside primary-screen bounds. `follow()` ignores under-1.5-pixel target noise and uses time-based exponential smoothing with a distance-dependent response. The working-area bounds are drawn in the preview.

A pinch detected for at least **20 ms**, released before the hold threshold, emits one click subject to cooldown. A hold of `drag_hold` (default 0.45 seconds) emits left mouse-down. Dragging uses relative fingertip travel from the cursor/grab origin. Release emits mouse-up, without another click.

Normal cursor motion uses PyAutoGUI. Active Windows dragging uses `mouse_input.py` and SendInput with MOVE + ABSOLUTE flags, primary-screen coordinates normalized to 0–65535, and no repeated button-down. Rejected native movement raises an error so the worker can stop and release input. Pause, mode change, tracking loss, stop, or exit cancels pending clicks and releases a held button. Mouse-up cleanup temporarily bypasses only the corner failsafe, then restores it.

## Scrolling

Two-hand palm position averages wrist, four finger bases, and four fingertips. A new open-palm gesture records an anchor. Movement of at least `max(0.008, scroll_threshold)` selects direction. Rate then accumulates as `direction * scroll_step * 5` wheel steps per second while the palm stays open. Return strokes do not reverse direction. Closing/reopening starts a new selection.

Right two-finger auto-scroll uses the last palm direction. With none stored, initial fingertip direction relative to the wrist selects it. Leaving the pose stops auto-scroll unless an open palm has priority.

One-hand `ScrollMotion` uses displacement from an initial two-finger anchor, a dead zone, elapsed time, and Scroll amount. Returning to the anchor stops it. Fractional wheel steps are retained between updates. There is no application ceiling of 10 for Scroll amount or internal rate cap. Output remains discrete wheel events.

The old direct-swipe PalmScroll branch remains a helper branch; active two-hand palm control dispatches palm_latched.

## Volume and air keyboard

`system_volume.py` opens the default Windows multimedia output endpoint using Core Audio/ctypes. The gesture target is thumb/index distance divided by wrist-to-middle-base palm size, mapped and clamped to 0–1. Output updates about ten times per second, at most five percentage points per update. Losing a hand or pausing does not set volume. Endpoint initialization, use, and COM cleanup occur on the worker thread.

Air keyboard overlays basic English letters, number/punctuation layers, Shift, Space, Back and Enter. Camera-space fingertip hit testing chooses a hovered key; pinch start locks the target and about 80 ms confirms it. One held pinch emits at most one key. Typing uses the currently focused application; no text buffer, automatic focus restoration, multilingual IME, or clipboard insertion is implemented. OS cursor movement is suspended outside Mouse mode.

## HUD

HUD pixels are drawn by the processing worker: translucent header/footer, tracking corner brackets, active mode, hand count, drag state, stop shortcut, and mode-switch hold progress. Keyboard keys/hover and the volume line/meter are functional mode indicators and remain available with decorative HUD disabled.

## Camera and configuration

Windows camera startup tries DirectShow, Media Foundation, then automatic selection. Each attempt requests 640×480 and accepts only an opened capture with a nonempty frame within five reads. Failed captures are released. Other platforms attempt automatic selection, but the application targets Windows and volume requires Windows.

The worker always opens camera 0. The camera_index JSON field remains for compatibility with saved settings; the current UI exposes no selector and the worker does not switch indexes. The older switching/rollback flow was superseded by the worker architecture.

| Key | Default | UI |
| --- | --- | --- |
| mouse_speed | 1.0 | Mouse speed |
| vertical_range | 0.20 | Vertical hand travel |
| smooth | 0.50 | Cursor responsiveness |
| pinch_threshold | 0.045 | Pinch sensitivity |
| click_cooldown | 0.25 | Click cooldown |
| drag_hold | 0.45 | Pinch hold to drag |
| scroll_threshold | 0.015 | Scroll activation distance |
| scroll_step | 2 | Scroll amount |
| two_hands | true | Two-hand mode |
| hud_enabled | true | Sci-fi HUD |
| camera_index | 0 | Compatibility field; not user-selectable |

Recognized finite numeric settings merge with defaults; malformed/unreadable files fall back to defaults. Boolean values are used for mode/HUD checkboxes. Sliders clamp their displayed range. Save writes preferences; Restore defaults changes the UI and requires Save to persist. Control mode starts as Mouse; it is not persisted.

## Verification

```powershell
.venv\Scripts\python.exe -m unittest check_click_release check_mode_gesture -v
.venv\Scripts\python.exe -m py_compile main.py engine.py camera_preview.py camera.py ui.py motion.py interactions.py mouse_input.py features.py system_volume.py
```

The current check modules contain 11 mocked-output checks. They verify click-on-release before palm selection, fast pinch acceptance, drag release/cancellation, mode hold/release gating, full cycling, paused state, and stale-settings protection. They do not interact with real OS input or a physical webcam.

Historical worker testing also blocked the preview thread while processing over 100 frames, generating drag movement, and detecting release; it confirmed the worker separation at that time. That test module is not currently in the checkout. UI initialization and a read-only Windows audio connection have passed during development. Live recognition, cross-app behavior and driver stability remain manual checks.

## Limits

Primary-screen mapping, approximate hand recognition, discrete wheel input, basic English simulated keyboard input, and default Windows audio only. No right-click gesture, multi-monitor calibration, native precision-touchpad events, custom model training, multilingual IME, packaged installer, or full transitive lockfile. Local camera processing contains no recording/upload feature.
