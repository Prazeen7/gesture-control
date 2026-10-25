# AI Gesture Control

Control your computer's mouse using hand gestures captured by your
webcam. Built with Python, OpenCV, MediaPipe, and PyAutoGUI.

## Current controls

  -----------------------------------------------------------------------
  Gesture / input         Action                  Notes
  ----------------------- ----------------------- -----------------------
  Move your index         Move cursor             Maps the index
  fingertip                                       fingertip to screen
                                                  coordinates with
                                                  smoothing.

  Touch thumb and index   Left click              One click per new
  fingertips together                             pinch, with a
                                                  0.5-second cooldown.

  Raise index and middle  Enter scroll mode       Move the raised fingers
  fingers; fold ring and                          vertically to scroll.
  pinky                                           

  Move raised index and   Scroll up               Uses relative movement
  middle fingers upward                           after a small
                                                  threshold.

  Move raised index and   Scroll down             Uses relative movement
  middle fingers downward                         after a small
                                                  threshold.

  Raise index, middle,    Pause cursor movement   The mouse stops moving
  ring, and pinky fingers                         while the open-palm
                                                  gesture is detected.

  Press `Q`               Quit                    The webcam preview
                                                  window must have
                                                  keyboard focus.

  Move cursor to a screen Emergency stop          PyAutoGUI's failsafe
  corner                                          raises an exception;
                                                  the program cleans up
                                                  the camera.
  -----------------------------------------------------------------------

**Gesture priority:** Open palm takes priority over scrolling. Scrolling
takes priority over cursor movement and clicking. The thumb is not
checked for open-palm or scroll-mode detection. Gesture recognition can
be affected by lighting and camera angle.

## Requirements

-   Windows 10/11 (the current tested setup target); other operating
    systems may need additional permissions or changes
-   A working webcam
-   Python 3.11 recommended
-   Python packages: `opencv-python`, `mediapipe`, `pyautogui`, `numpy`

## Setup (Windows PowerShell)

``` powershell
mkdir gesture-control
cd gesture-control
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install opencv-python mediapipe==0.10.21 pyautogui numpy
```

If you already created the project and virtual environment, activate it
and install the dependencies; you do not need to recreate the folder.

The current `main.py` uses `mp.solutions.hands`, an older MediaPipe API.
MediaPipe `0.10.21` supports this API, but may not have a compatible
wheel for newer Python versions. If installation fails, use Python 3.11
or migrate the code to the MediaPipe Tasks API.

## Run

From the project directory, with the virtual environment activated:

``` powershell
python main.py
```

Allow webcam access if prompted. A window named **AI Gesture Control**
should appear, showing the hand landmarks and the current status
(`NO HAND`, `MOVING`, `CLICK`, `SCROLL`, or `PAUSED`).

## How to use

1.  Put one hand in view of the webcam in good lighting.
2.  Move your index fingertip to control the cursor.
3.  Touch your thumb and index fingertips to left-click; separate them
    before clicking again.
4.  Hold up your index and middle fingers while folding the other two
    fingers; move vertically to scroll.
5.  Open your hand with four fingers raised to pause movement.
6.  Focus the camera preview window and press `Q` to exit.

**Safety:** Test on a noncritical window first. The app controls your
real system mouse. PyAutoGUI's failsafe is enabled
(`pyautogui.FAILSAFE = True`). If the cursor reaches a corner, the
failsafe may terminate the program with an exception.

## Tuning

In `main.py`:

  -----------------------------------------------------------------------
  x

## Troubleshooting

**`AttributeError: module 'mediapipe' has no attribute 'solutions'`**

The installed MediaPipe version does not expose the legacy API expected
by this code. In your activated virtual environment:

``` powershell
python -m pip uninstall mediapipe -y
python -m pip install mediapipe==0.10.21
python -c "import mediapipe as mp; print(mp.__version__); print(hasattr(mp, 'solutions'))"
```

For this version, the last command should print `0.10.21` and `True`.

**Camera won't open:** Check Windows camera permissions, close other
applications using the webcam, or try another camera index.

**Mouse movement is jittery:** Improve lighting and reduce `smooth` (for
example, to `0.15`).

**Clicks happen accidentally:** Reduce the pinch threshold slightly (for
example, to `0.035`).

**Scrolling doesn't work:** Keep only the index and middle fingers
raised, and move them vertically enough to cross the threshold.

## Not implemented yet

-   Right-click and double-click gestures
-   Drag-and-drop
-   Volume control
-   Virtual keyboard
-   Custom gesture training
-   On-screen calibration and futuristic HUD

## Project structure

``` text
gesture-control/
├── main.py
├── README.md
└── .venv/       # Local Python environment (do not commit)
```

## Privacy

Hand detection runs locally through the webcam. The provided script does
not intentionally record or upload webcam video.

## Desktop control panel

Run `python main.py` to open the controls and gesture guide. Click **Start camera**, then **Enable control**. The camera starts paused. Use **Pause control** or Space in the panel to toggle control. Escape stops the camera; Q works in the camera preview.

Settings apply immediately:
- **Mouse speed:** Increase to cover more screen distance with less hand movement.
- **Cursor responsiveness:** Lower values smooth movement; higher values follow faster.
- **Pinch sensitivity:** Increase to recognize a pinch with fingertips farther apart.
- **Click cooldown:** Minimum delay between clicks; release the pinch before clicking again.
- **Scroll movement threshold:** Movement needed to trigger scrolling.
- **Scroll amount:** Number of scroll steps per movement.
- **Camera index:** Stop and restart the camera to apply a camera change.

Click **Save settings** to persist settings in settings.json. **Restore defaults** applies defaults immediately; save to keep them. The panel uses built-in Tkinter. Closing it releases the camera.
