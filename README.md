# Gesture Control

A local Windows desktop app for webcam-based mouse control, drag-and-drop, volume adjustment, and air typing. Built with Python, MediaPipe, OpenCV, PyAutoGUI, and Tkinter.

Updated **25 October 2026**.

## Install and run

Use **Python 3.11** with Tkinter and a working webcam. From PowerShell in the project folder:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirement.txt
.venv\Scripts\python.exe main.py
```

For an existing compatible environment, run the last two commands. The filename is **requirement.txt**.

MediaPipe is pinned to 0.10.21 because the app uses `mp.solutions.hands`. Install only `opencv-contrib-python`; do not add `opencv-python` or a headless OpenCV package to the same environment. They share the `cv2` namespace. A fresh environment avoids conflicts from previous mixed installations.

Tkinter is part of the Windows Python installation, not a pip dependency. Volume control uses the Windows Core Audio API through ctypes, without another package. Node.js, FFmpeg, and Hyperframes are needed only to recreate the optional launch video, not to run Gesture Control.

## First session

1. Close older copies of the app and other applications using the webcam.
2. Start the app and click **Start camera**. It uses the default webcam; camera-index selection is not shown.
3. Show the right index finger at a comfortable height, then click **Enable control**.
4. Use the gestures below. **Recenter hand** adjusts the comfortable cursor height.
5. Save preferences with **Save settings**. Closing the app stops the camera and releases held input.

The panel has equal-size **Gesture guide** and **Controls & settings** navigation buttons. Both pages scroll, while mode selection, primary controls, status, and save actions stay accessible. The guide updates for the selected mode and hand configuration.

## Mouse mode: default two-hand gestures

| Gesture | Action | Stop / repeat |
| --- | --- | --- |
| ☝️ Right index finger | Move cursor | Change gesture or pause |
| 🤏 Short left thumb/index pinch | Left click on release; minimum detected duration about 20 ms | Separate fingertips before another click |
| 🤏 Hold left pinch for 0.45 seconds | Grab a window title bar or draggable object; move the right pointing hand to drag | Release the pinch to drop |
| ✋ Either open palm, then move up/down once | Lock continuous scrolling in that direction | Close palm; reopen to choose another direction |
| ✌️ Right index + middle fingers | Auto-scroll in the last palm-scroll direction | Return to one pointing finger; close any open left palm |
| 👍 Hold LEFT thumbs-up for 1.2 seconds | Cycle Mouse → Volume → Air keyboard → Mouse | Release for at least 0.25 seconds before another switch |

Palm scrolling **continues when the hand holds still or returns in the opposite direction**. Closing the palm stops it. The left palm has priority when both are open and can scroll without the right hand visible.

A short pinch finishes its click before the opened hand can select scrolling. A held pinch stays in cursor mode, and dragging uses relative travel from the grab position. Losing a required hand, pausing, changing mode, or exiting releases held drag input.

## Other modes

| Mode | Control |
| --- | --- |
| Volume | Widen the pointing hand's thumb/index gap to increase Windows output volume; narrow it to decrease. Mouse actions are suspended. |
| Air keyboard | Focus a target text field, aim the pointing index at a camera-preview key, and pinch with the click hand to type. Includes Shift, Space, Back, Enter, and 123 / ABC layers. |
| Sci-fi HUD | Toggle the camera's tracking brackets, mode/status, hand count, and drag indicators. Functional keyboard and volume indicators remain available when decorative HUD is off. |

Manual mode selection pauses input until enabled again. Gesture mode selection suspends actions while thumbs-up is held, then resumes only if control was previously enabled. The selector and guide synchronize automatically.

Turn off **Two-hand mode** to use the first detected hand for both pointing and pinching. In that mode open palm pauses, two raised fingers use displacement-based scrolling, and thumbs-up uses the visible hand. See the detailed guides for those differences.

## Settings and shortcuts

Settings apply immediately; **Save settings** persists them. **Restore defaults** applies defaults and requires saving to retain them.

| Setting | Built-in default | Meaning |
| --- | --- | --- |
| Scroll amount | 2 | Any positive finite number, including values above 10 |
| Mouse speed | 1.0 | Higher covers more screen distance with less hand travel |
| Vertical hand travel | 0.20 | Lower makes top/bottom screen edges easier to reach |
| Cursor responsiveness | 0.50 | Lower smooths; higher follows faster |
| Pinch sensitivity | 0.045 | Higher accepts a wider thumb/index gap |
| Click cooldown | 0.25 seconds | Minimum interval between short clicks |
| Pinch hold to drag | 0.45 seconds | Hold duration before grabbing |
| Scroll activation distance | 0.015 | Movement needed to choose palm-scroll direction; one-hand scroll dead zone |
| Two-hand mode / Sci-fi HUD | On / On | Hand configuration and overlay visibility |

Saved values may differ from these defaults. The control mode starts as Mouse on each new launch.

- **Space** in the panel: pause/resume (ignored while editing inputs or using the mode selector).
- **Escape** in the panel: stop camera.
- **Q** in the preview, or closing the preview: stop camera.
- **Stop camera**: release the camera and held input.

## Documentation

- [User guide](docs/USER_GUIDE.md): installation, mouse controls, settings, and troubleshooting.
- [Advanced features](docs/ADVANCED_FEATURES.md): dragging, volume, keyboard, HUD, gesture mode switching, and freeze fixes.
- [Technical reference](docs/TECHNICAL_REFERENCE.md): thread architecture, recognition, input output, and dependencies.
- [Development history](docs/DEVELOPMENT_HISTORY.md): evolution and replaced features.

## Project layout

```text
gesture-control/
  main.py                    Tk controller, configuration, worker messages
  engine.py                  Independent camera, tracking, and input thread
  camera_preview.py          Independent preview and latest-frame queue
  camera.py                  Default webcam backend fallback
  ui.py                      Mode-aware guide, controls, settings
  motion.py                  Mapping, smoothing, hand roles, scrolling
  interactions.py            Pinch/drag, mode gesture, air-key selection
  mouse_input.py             Windows SendInput drag movement
  features.py                Air keyboard, volume gesture, HUD
  system_volume.py           Windows Core Audio adapter
  settings.json              Saved preferences
  requirement.txt            Pinned direct runtime dependencies
  check_click_release.py     Click/drag release regressions
  check_mode_gesture.py      Gesture mode-switch checks
  docs/                      Detailed documentation
  artifacts/                 Development visuals
  brag-output/               Optional launch video and editable source
```

## Checks

```powershell
.venv\Scripts\python.exe -m unittest check_click_release check_mode_gesture -v
.venv\Scripts\python.exe -m py_compile main.py engine.py camera_preview.py camera.py ui.py motion.py interactions.py mouse_input.py features.py system_volume.py
```

The two available check modules contain **11 checks** with OS input mocked. They cover quick clicks, release into an open palm, drag release, cancellation, thumbs-up timing, cycling, UI snapshot protection, and paused-state behavior. Earlier test files were removed from this checkout; their historical counts are not the current suite.

A separate worker regression previously confirmed that tracking and drag release continue while preview event handling is blocked. UI startup/mode switching and a read-only Windows audio connection have also been checked during development. Live webcam accuracy, cross-application dragging, typing focus, and perceived smoothness still need hardware testing.

## Troubleshooting and limits

If the camera fails, close older app instances/video calls, check the hardware shutter and Windows camera permissions, and test Windows Camera. Fully restart the app after code updates.

Camera tracking/input, OpenCV preview, and Tk widgets run independently. Dragging an application window should no longer block the tracking callback. The preview window itself may temporarily stop repainting during its own Windows move operation; tracking and release continue separately.

Hand recognition depends on lighting, visibility, pose, and camera frame rate. Output uses discrete mouse-wheel events, primary-monitor mapping, basic English keyboard input, and the default Windows audio device. Elevated applications can reject ordinary injected input. Right-click, multi-monitor calibration, multilingual IME integration, and custom gesture training are not implemented.

Video processing is local. There is no camera recording/upload feature. PyAutoGUI's corner failsafe remains enabled; cleanup releases held mouse buttons even after a failsafe stop.
