# Advanced features

## Modes and shared controls

The mode selector above the two tabs offers **Mouse**, **Volume**, and **Air keyboard**. Each mode change pauses input and releases a held drag. Start the camera, choose the mode, then Enable control. The gesture guide changes with the mode. Space toggles control when the panel has focus; Escape stops the camera. Q stops it from the preview. Only Mouse mode emits cursor movement/click/scroll output.

No new packages are required. Windows volume uses Core Audio directly through Python ctypes.

## Pinch and hold to drag

In Mouse mode, use the left hand to pinch in two-hand mode, or the same pointing hand in one-hand mode.

1. Aim the cursor at a window title bar, file, or other draggable item.
2. Pinch thumb and index and hold for the configured duration (default **0.45 seconds**).
3. The HUD shows DRAGGING; move the pointing hand to drag.
4. Release the pinch to drop. One-hand cursor movement resumes while dragging, so the held pinch does not freeze the pointer.

A **short pinch clicks on release**, rather than immediately on pinch entry. This distinguishes a click from a hold without emitting a click before every drag. Separate fingertips before the next pinch. Adjust **Pinch hold to drag** in Settings (0.25–1.5 seconds). Click cooldown still governs short clicks.

Pausing, stopping, losing the pointer/click hand, switching hand/control mode, entering a scroll pose, or closing the app releases the held mouse button. Mouse-up cleanup also runs when PyAutoGUI's corner failsafe has fired. Dragging depends on the target app supporting drag; some elevated apps may reject ordinary desktop input.

## Finger-distance volume control

1. Choose **Volume** and enable control.
2. Show the right hand in two-hand mode, or your visible hand in one-hand mode.
3. Widen the thumb/index gap to increase Windows output volume; narrow it to decrease.
4. Watch the fingertip line, vertical meter, and percentage in the camera preview.
5. Pause or remove the hand to hold the current level. Choose Mouse to return to mouse controls.

The gap is normalized by wrist-to-middle-base palm distance, reducing changes caused only by camera depth. Updates are limited to roughly ten per second, with at most five percentage points per update. Volume moves gradually toward the gesture's target. The gesture does not toggle mute. It controls the default Windows multimedia playback endpoint; reconnecting devices may require changing modes or pausing/resuming to reopen that endpoint.

An unavailable endpoint produces an error and stops the camera. Reconnect an audio output and restart. The adapter uses [Microsoft's normalized endpoint volume API](https://learn.microsoft.com/en-us/windows/win32/api/endpointvolume/nf-endpointvolume-iaudioendpointvolume-setmastervolumelevelscalar).

## Air keyboard

1. Choose **Air keyboard**, start the camera, and enable control.
2. Use the physical mouse once to focus the app/text field that should receive text. The keyboard sends input to the active app; it does not maintain its own text buffer.
3. Aim the right index fingertip at a key drawn in the camera preview. In one-hand mode use the visible hand.
4. Pinch with the left hand in two-hand mode, or the pointing hand in one-hand mode. Keep the pinch briefly (about 80 ms).
5. The target locks at pinch start, so bending the finger does not change the selected key. Separate fingertips before the next key.

A held pinch types at most one key. Missing hands, pause, and mode changes cancel pending selections and require a release before another key. The OS cursor stays still in this mode.

Available controls:

| Key | Action |
| --- | --- |
| Letters | Basic English QWERTY input |
| Shift | Uppercase the next letter; press again to toggle off |
| 123 / ABC | Switch numbers/punctuation and letters |
| Space | Insert a space |
| Back | Backspace |
| Enter | Enter/Return |

Letters use the current keyboard layer; this is basic simulated desktop input, not multilingual IME support. Focus matters: if the camera or controller is focused, keystrokes go there. For reliable typing, enable the mode first, then focus the intended text field. Pause before clicking back into the controller when you are finished.

## Sci-fi camera HUD

The **Sci-fi HUD** checkbox toggles the overlay. It contains a dark translucent status strip, cyan tracking corner brackets, detected-hand count, active control mode, drag state, and stop shortcut. Volume mode adds a distance line and level meter. Air keyboard mode draws keys, a fingertip cursor, and the target highlight.

Disabling HUD keeps the functional keyboard and volume visual controls; it removes the decorative tracking/status overlay and falls back to plain status text. Save settings to retain HUD visibility. The selected control mode always starts as Mouse on a fresh launch.

## Verification and limits

Run:

```powershell
.venv\Scripts\python.exe -m unittest discover -p "test_*.py"
```

The current suite has 18 tests covering click-versus-hold timing, drag release and cancellation, release at a failsafe corner, cooldown, keyboard targeting and held-key suppression, keyboard layers, volume mapping/smoothing, endpoint cleanup, and HUD drawing. UI mode switching and guide construction were also checked. A read-only connection to the actual Windows audio endpoint succeeded.

Tests mock emitted mouse/keyboard/audio changes; they do not prove live webcam recognition quality or cross-app drag/typing behavior. Manual testing remains necessary for camera ergonomics, window dragging, volume feel, and targeting keys in your lighting.


### Drag continuity update

While a click-hand pinch is held in cursor mode, it takes priority over finger poses that would otherwise select scrolling or pause. This prevents a finger folding during the grab from interrupting drag movement. Drag motion is relative to the fingertip and cursor positions at the grab, avoiding the jump caused by closing the index finger into a pinch. Release the pinch before selecting scrolling. Pause, tracking loss, mode change, and exit still release the mouse button.

### Windows drag input update

Active dragging now uses Windows SendInput mouse-movement events through mouse_input.py, rather than only repositioning the pointer with PyAutoGUI's SetCursorPos path. Movement events carry MOVE and ABSOLUTE flags without repeating button-down. Pinch release still sends mouse-up, and failsafe checks remain active. This targets drags that resume only after physical mouse movement. The current verification checked native input structure size, coordinate conversion, event flags, and pinch release with mocked output. Live dragging remains to be confirmed on the target window.

Reference: [Microsoft MOUSEINPUT flags and absolute coordinates](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-mouseinput).

### Camera freeze during drag: independent processing

The camera/gesture loop now runs in `engine.py` on its own tracking/input thread. `camera_preview.py` owns a separate preview thread with a single-frame queue. The Tk controller only sends configuration/commands and polls status messages. No tracking-thread code reads Tk variables or waits for Tk callbacks.

This prevents a Windows window-move loop on the controller or preview thread from blocking gesture tracking and pinch release. Preview updates may pause while the preview window itself is being moved, but frame processing and mouse-up continue independently. Slow preview frames are replaced instead of queued indefinitely.

Stopping, mode changes, and close request worker cleanup; the worker releases held input and closes camera/tracker/audio resources. Restart the application completely after this update.

Verification: `python -m unittest test_engine -v` passes three tests. The regression deliberately blocks the preview's event handling while the actual gesture-processing loop detects a hold, emits drag movement, processes over 100 frames, and releases the button. All OS input is mocked. Real webcam behavior still needs a live check.
