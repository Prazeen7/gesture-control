# User guide

Updated: 25 October 2026.

## 1. Setup and launch

You need a working webcam, Windows camera access, Python 3.11 with Tkinter, and OpenCV, MediaPipe, PyAutoGUI, and NumPy. See the [README](../README.md#quick-start) for installation commands.

Launch from the project directory:

```powershell
.venv\Scripts\python.exe main.py
```

Close older copies of Gesture Control before starting a new session so they do not compete for the webcam.

Click **Start camera**, show your pointing hand at a comfortable height, then click **Enable control**. Starting the camera alone does not enable mouse control.

## 2. Layout and buttons

| Control | Purpose |
| --- | --- |
| Two-hand mode | Switch between two-hand and one-hand gesture rules; the guide updates automatically |
| Start camera | Connect the default webcam and open its preview with control paused |
| Enable control / Pause control | Toggle mouse control without closing the camera |
| Recenter hand | Use the next cursor gesture's fingertip height as the vertical center |
| Stop camera | Release the camera, hand tracker, and preview |
| Gesture guide | Read four visual gesture cards and startup instructions |
| Controls & settings | Adjust control behavior; changes apply immediately |
| Save settings | Write preferences to settings.json |
| Restore defaults | Apply built-in defaults; save afterward to keep them |

The status strip shows tracking and action states. Both tabs are equal in size. Their contents scroll when needed, while primary buttons and status remain visible.

## 3. Two-hand mode

This is enabled by default. The preview is mirrored. Roles are assigned using MediaPipe's Right/Left labels, rather than the order in which hands are detected.

### ☝️ Move with the right hand

Raise your right index finger and move gently. Fold the other fingers so you do not accidentally select palm or two-finger scrolling.

When you enable control, the first cursor gesture establishes your comfortable vertical center. At the default speed and vertical range, moving the fingertip approximately 10% of the image height above or below that center reaches the top or bottom screen edge. Blue preview lines mark the working area's vertical boundaries.

If reaching an edge is difficult, click **Recenter hand** while your hand is comfortable, or lower **Vertical hand travel**.

### 🤏 Click with the left hand

Keep the right pointing hand visible. Touch the left thumb and index fingertips together briefly, then separate them before clicking again. Pinching must persist for roughly 45 milliseconds. Click cooldown also applies.

The right cursor hand can continue moving while the left pinches. Aim steadily when clicking a small target. The removed index-bend click gesture is not available.

### ✋ Scroll with either open palm

1. Open the hand with the four non-thumb fingers extended.
2. Wait briefly for the gesture to settle; the preview shows `PALM READY - MOVE UP / DOWN`.
3. Move the whole hand upward or downward once to select the direction.
4. Scrolling continues in that direction while the palm stays open.
5. Lower, hold still, or reposition the open hand without reversing the direction.
6. **Close the palm to stop.** Reopen and move in the other direction to reverse.

This direction lock prevents the return stroke from scrolling the page backward. It is continuous scrolling, rather than a direct touchpad-style mapping of every hand movement.

The left palm has priority if both palms are open. It can scroll while the right hand is outside the camera view. A closed left hand alone does not move the cursor. Palm scrolling suspends cursor movement and clicking.

### ✌️ Auto-scroll with the right hand

Raise the right index and middle fingers, folding the others. Holding this pose continues scrolling in the last palm-scroll direction. If no palm direction has been selected in the current control session, the fingertips' upward/downward direction relative to the wrist selects the initial direction.

Return to a single pointing finger to stop auto-scroll. If the left palm is still open, left-palm scrolling takes priority, so close it as well when you want to return to cursor movement.

### Pause and stop

Use **Pause control** or Space in the panel to pause all mouse actions. Use Escape in the panel, Q in the preview, the preview's close button, or **Stop camera** to stop the camera. Keyboard shortcuts require focus in the appropriate window; Space is ignored while editing a text field.

In two-hand mode, an open palm scrolls; it does not pause.

## 4. One-hand mode

Turn off **Two-hand mode**. The first detected hand supplies all controls; use one visible hand for predictable behavior.

| Pose | Result |
| --- | --- |
| Index pointing, other fingers folded | Move cursor |
| Thumb + index pinch | Left click; release before next click |
| Index + middle raised, at least one other finger folded | Scroll mode |
| Four non-thumb fingers extended | Pause movement and clicks |

For scrolling, start the two-finger gesture, shift upward or downward from its starting height, and hold. Greater displacement beyond the dead zone increases the rate. Return to the starting height or lower the middle finger to stop. This differs from two-hand palm direction lock.

During a detected one-hand pinch, cursor movement is held to steady the click. Open palm takes priority over scrolling. Switching hand modes resets gesture state and recenters the next cursor gesture.

## 5. Settings

Values below are built-in defaults, not necessarily the values currently saved in settings.json.

| Setting | Default | Allowed UI range | Effect |
| --- | --- | --- | --- |
| Scroll amount | 2 | Any positive finite number | Higher values increase scroll rate; decimals and values above 10 are supported |
| Mouse speed | 1.0 | 0.4–2.5 | Higher covers more screen distance with less hand travel |
| Vertical hand travel | 0.20 | 0.10–0.50 | Lower requires less vertical movement to reach edges |
| Cursor responsiveness | 0.50 | 0.05–1.00 | Lower smooths movement; higher follows faster |
| Pinch sensitivity | 0.045 | 0.015–0.10 | Higher detects a pinch with fingertips farther apart |
| Click cooldown | 0.25 seconds | 0.1–2.0 seconds | Minimum delay between clicks |
| Scroll activation distance | 0.015 | 0.005–0.06 | Lower needs less movement to choose palm direction; also sets the one-hand scroll dead zone |
| Two-hand mode | On | On / Off | Selects the gesture rules |

Try modest scroll amounts first. Large values such as 100 can scroll very quickly. There is no user-facing upper limit or rate cap; the target application's handling of wheel input still affects the result.

Invalid or incomplete scroll input leaves the last valid amount active and prevents saving until corrected. Changes are not automatically saved. **Restore defaults** applies immediately, but also needs **Save settings** to persist.

## 6. Status messages

| Status | Meaning / next step |
| --- | --- |
| CONTROL PAUSED | Enable control to begin |
| NO HAND | Put the expected hand in view |
| SHOW RIGHT HAND | Cursor/click operations need the right hand; an open left palm can still be used for scrolling |
| CHANGING GESTURE | Hold the pose briefly while the transition settles |
| MOVING | Cursor mode is active |
| PINCH / CLICK | Pinch is held / a click was emitted |
| PALM READY - MOVE UP / DOWN | Move the open palm to select a direction |
| SCROLL UP / DOWN - CLOSE PALM TO STOP | Palm direction is locked; close the palm to stop |
| AUTO SCROLL | Right two-finger auto-scroll is active |
| SCROLL | One-hand displacement scrolling is active |
| PAUSED | One-hand open-palm pause is active |
| Emergency stop triggered | PyAutoGUI failsafe stopped the camera; restart the camera to continue |

## 7. Troubleshooting

### Camera unavailable

The app uses the default webcam; there is no camera-index control in the UI. Close older Gesture Control copies and camera applications such as video-call software. Check Windows Settings → Privacy & security → Camera, including access for desktop apps. Check the camera shutter or hardware privacy key, and test the webcam in Windows Camera.

On Windows the app attempts DirectShow, Media Foundation, then automatic backend selection. Failed attempts release their camera handles. A camera still may be unavailable because of permissions, a driver issue, or another application holding it.

### Cursor seems stuck or switches modes

Keep your right pointing hand visible in two-hand mode. Fold the middle, ring, and little fingers while aiming. Close an open left palm so it does not keep selecting scrolling. Use good lighting and avoid overlapping hands. Recenter at a comfortable height. Adjust responsiveness if tracking feels too slow.

### Cursor cannot reach the top or bottom comfortably

Lower Vertical hand travel or increase Mouse speed. Recenter with the index finger at your normal working height. Settings operate on normalized camera coordinates, so camera distance and placement affect physical hand travel.

### Pinch misses or clicks accidentally

Adjust Pinch sensitivity: higher for missed pinches, lower for accidental clicks. Separate the fingertips before each attempt and respect Click cooldown. In two-hand mode, click with the left hand while keeping the right hand visible in cursor mode.

### Palm scrolling goes in the wrong direction

Close the palm fully to end the current lock. Reopen, let the palm-ready status appear, then make a clear movement in the desired direction. Returning an already open palm does not reverse direction by design. If both palms are open, the left controls scrolling.

### Scroll is too fast or slow

Adjust Scroll amount. Reduce Scroll activation distance if the initial direction is hard to activate. One-hand scrolling also depends on distance from the starting height. Different applications may respond differently to mouse-wheel steps.

### MediaPipe has no solutions attribute

This application requires the legacy API. Use the project's Python 3.11 environment and documented MediaPipe 0.10.21 target, rather than replacing it with an incompatible version. See the README installation command.

## 8. Privacy and current limits

Video processing happens locally. The application contains no recording or upload feature. It controls the real system mouse, and PyAutoGUI's corner failsafe remains enabled.

Recognition depends on lighting, angle, distance, hand overlap, and camera frame rate. Scrolling uses discrete wheel events, not native precision-touchpad gestures. Right-click, drag-and-drop, virtual keyboard, custom gesture training, and multi-monitor calibration are not implemented.
