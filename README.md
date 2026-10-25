# Gesture Control

A local Windows desktop application that controls the mouse using webcam hand gestures. It combines OpenCV, MediaPipe, PyAutoGUI, and a Tkinter control panel.

Documentation reflects the implementation as of **25 October 2026**.

## Documentation

- [User guide](docs/USER_GUIDE.md): setup, gestures, controls, settings, and troubleshooting.
- [Technical reference](docs/TECHNICAL_REFERENCE.md): architecture, recognition rules, configuration, and testing.
- [Development history](docs/DEVELOPMENT_HISTORY.md): changes made so far and superseded behavior.

## Quick start

From PowerShell in the project directory, using the existing environment:

```powershell
.venv\Scripts\python.exe main.py
```

For a new environment, use Python 3.11:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install opencv-python mediapipe==0.10.21 pyautogui numpy
.venv\Scripts\python.exe main.py
```

The application uses the legacy `mp.solutions.hands` API. The version above is the project's documented compatible MediaPipe target; dependency versions are not locked in a requirements file. Tkinter must be included in your Python installation.

1. Click **Start camera**. Mouse control starts paused.
2. Show your right index finger at a comfortable height.
3. Click **Enable control**.
4. Use the gestures below. Click **Save settings** to retain adjustments.

## Default two-hand controls

| Gesture | Action | How to stop / repeat |
| --- | --- | --- |
| ☝️ Right index finger | Move cursor | Pause control or change gesture |
| 🤏 Left thumb + index pinch | Short pinch clicks on release; hold to drag | Release to drop; separate before the next action |
| ✋ Either open palm, then move up/down once | Lock continuous scrolling in that direction | Close the palm; reopen to choose another direction |
| ✌️ Right index + middle fingers | Auto-scroll in the last palm-scroll direction | Return to one pointing finger |
| Space in the control panel | Pause / resume all mouse control | Press again to toggle |
| Escape in the panel | Stop camera | Start camera again |
| Q in the camera preview | Stop camera | Start camera again |

**Palm scrolling continues while the hand is open, including when it holds still or returns downward after an upward stroke.** Close the palm to stop. The left palm takes priority when both palms are open and can scroll without the right hand visible.

Turn off **Two-hand mode** for one-hand controls. In that mode, open palm pauses, and two raised fingers use displacement-based scrolling. See the [user guide](docs/USER_GUIDE.md) for the differences.

## New control modes

Choose **Mouse**, **Volume**, or **Air keyboard** above the tabs. Changing mode pauses control; enable it again when ready.

- **Drag and drop:** In Mouse mode, aim at a title bar or draggable object. Hold the click-hand pinch for 0.45 seconds, move the pointing hand, then release to drop. A short pinch clicks on release. Pause, tracking loss, mode change, and exit release any held mouse button.
- **Volume:** Spread the pointing hand's thumb and index to raise system volume; bring them closer to lower it. Uses the default Windows audio endpoint, a hand-relative distance, and gradual updates. Mouse actions are suspended.
- **Air keyboard:** Aim the pointing index at a key in the camera preview and pinch with the click hand to type into the focused application. Includes Shift, Space, Back, Enter, and 123 / ABC layers. In one-hand mode the same hand aims and pinches.
- **Sci-fi HUD:** Toggle the camera overlay for mode/status, hand tracking brackets, drag indicators, a volume meter, and the virtual-keyboard highlight.

See [advanced features](docs/ADVANCED_FEATURES.md) for usage and verification.

## Interface

- **Gesture guide:** Four emoji cards with hand assignments, instructions, and stopping actions.
- **Controls & settings:** Scroll amount, mouse speed, vertical hand travel, responsiveness, pinch sensitivity, click cooldown, and scroll activation distance.
- Camera buttons, status, Save settings, and Restore defaults stay outside the scrolling pages.
- Both navigation buttons have equal dimensions; selection changes their colors.
- The app uses the default webcam. Camera-index selection is no longer exposed in the UI.

## Project files

```text
gesture-control/
  main.py                    Application lifecycle and gesture dispatch
  ui.py                      Desktop UI and mode-aware guide
  motion.py                  Mapping, smoothing, scroll logic, and hand roles
  camera.py                  Camera backend fallback and cleanup
  settings.json              Saved preferences
  interactions.py            Drag and keyboard state machines
  features.py                Air keyboard, volume gesture, and HUD
  system_volume.py           Windows Core Audio adapter
  test_features.py            Current feature tests
  docs/                      Detailed documentation
  .venv/                     Local Python environment
```

## Verification and limits

The current feature suite contains 18 tests. Earlier helper tests are not present in this checkout. Run discovery with:

```powershell
.venv\Scripts\python.exe -m unittest discover -p "test_*.py"
```

Motion tests and UI checks have passed during development. Live gesture accuracy, camera availability, and perceived smoothness still depend on hardware, lighting, and hand visibility. The app emits mouse-wheel steps; it does not implement native precision-touchpad scrolling.

Left clicks, drag-and-drop, Windows volume control, a basic English air keyboard, and a camera HUD are implemented. Right clicking, custom gesture training, and multi-monitor calibration are not implemented. Hand processing runs locally; the application does not record or upload video.

