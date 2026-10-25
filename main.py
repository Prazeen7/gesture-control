import json
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import cv2
import mediapipe as mp
import pyautogui

SETTINGS_PATH = Path(__file__).with_name('settings.json')
DEFAULTS = dict(mouse_speed=1.0, smooth=0.5, pinch_threshold=0.045,
                click_cooldown=0.5, scroll_threshold=0.05, scroll_step=2,
                camera_index=0)


def load_settings():
    settings = DEFAULTS.copy()
    try:
        saved = json.loads(SETTINGS_PATH.read_text())
        for key, default in DEFAULTS.items():
            value = saved.get(key, default)
            if isinstance(value, (int, float)) and math.isfinite(value):
                settings[key] = value
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return settings


class GestureApp:
    def __init__(self, root):
        self.root = root
        self.cap = self.hands = None
        self.running = False
        self.pinch_active = False
        self.scroll_anchor = None
        self.last_click = 0
        self.values = {}
        settings = load_settings()
        root.title('Gesture Control • Controls & Settings')
        root.geometry('680x780')
        root.minsize(620, 720)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Segoe UI', 23, 'bold'))
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', padding=8)
        panel = ttk.Frame(root, padding=24)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='Gesture Control', style='Title.TLabel').pack(anchor='w')
        ttk.Label(panel, text='Your hand, your cursor. Tune how it feels.').pack(anchor='w', pady=(4, 14))
        self.status = tk.StringVar(value='Ready • Start the camera to begin')
        ttk.Label(panel, textvariable=self.status, wraplength=590).pack(anchor='w', pady=(0, 10))
        buttons = ttk.Frame(panel)
        buttons.pack(fill='x')
        ttk.Button(buttons, text='Start camera', command=self.start).pack(side='left', padx=(0, 8))
        self.pause_button = ttk.Button(buttons, text='Enable control', command=self.toggle)
        self.pause_button.pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='Stop camera', command=self.stop).pack(side='left')
        guide = ttk.LabelFrame(panel, text='Gesture guide', padding=12)
        guide.pack(fill='x', pady=16)
        for text in ('Move index fingertip → Move cursor',
                     'Touch thumb + index → Left click (release before next click)',
                     'Raise index + middle, fold others → Move up/down to scroll',
                     'Open palm (four fingers raised) → Pause movement',
                     'Space in this panel → Enable / pause control',
                     'Q in camera preview or Escape in panel → Stop camera'):
            ttk.Label(guide, text=text).pack(anchor='w', pady=2)
        tuning = ttk.LabelFrame(panel, text='Settings • changes apply immediately', padding=12)
        tuning.pack(fill='x')
        specs = [('mouse_speed', 'Mouse speed', 0.4, 2.5),
                 ('smooth', 'Cursor responsiveness', 0.05, 1.0),
                 ('pinch_threshold', 'Pinch sensitivity', 0.015, 0.10),
                 ('click_cooldown', 'Click cooldown (seconds)', 0.1, 2.0),
                 ('scroll_threshold', 'Scroll movement threshold', 0.01, 0.15),
                 ('scroll_step', 'Scroll amount', 1, 10)]
        for key, label, low, high in specs:
            row = ttk.Frame(tuning)
            row.pack(fill='x', pady=4)
            ttk.Label(row, text=label, width=28).pack(side='left')
            value = tk.DoubleVar(value=max(low, min(high, settings[key])))
            self.values[key] = value
            readout = ttk.Label(row, width=6)
            readout.pack(side='right')
            def update(*_, v=value, output=readout, name=key):
                output.config(text=str(round(v.get())) if name == 'scroll_step' else f'{v.get():.3f}')
            value.trace_add('write', update)
            ttk.Scale(row, from_=low, to=high, variable=value).pack(side='left', fill='x', expand=True)
            update()
        row = ttk.Frame(tuning)
        row.pack(fill='x', pady=6)
        ttk.Label(row, text='Camera index', width=28).pack(side='left')
        self.camera = tk.StringVar(value=str(int(settings['camera_index'])))
        ttk.Spinbox(row, from_=0, to=10, textvariable=self.camera, width=6).pack(side='left')
        ttk.Label(tuning, text='Camera changes apply after stopping and starting the camera.').pack(anchor='w')
        actions = ttk.Frame(panel)
        actions.pack(fill='x', pady=12)
        ttk.Button(actions, text='Save settings', command=self.save).pack(side='left', padx=(0, 8))
        ttk.Button(actions, text='Restore defaults', command=self.reset).pack(side='left')
        ttk.Label(panel, text='Lower responsiveness gives smoother movement. Higher mouse speed\nreaches screen edges with less hand movement. Camera starts paused.', wraplength=590).pack(anchor='w')
        root.bind('<space>', self.on_space)
        root.bind('<Escape>', lambda _: self.stop())
        root.protocol('WM_DELETE_WINDOW', self.close)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0

    def on_space(self, event):
        if event.widget.winfo_class() not in ('TSpinbox', 'TEntry'):
            self.toggle()
            return 'break'

    def save(self):
        try:
            camera = int(self.camera.get())
            if not 0 <= camera <= 10:
                raise ValueError('Camera index must be between 0 and 10.')
            settings = {key: value.get() for key, value in self.values.items()}
            settings.update(camera_index=camera, scroll_step=round(settings['scroll_step']))
            SETTINGS_PATH.write_text(json.dumps(settings, indent=4) + '\n')
            self.status.set('Settings saved')
        except (ValueError, OSError) as error:
            messagebox.showerror('Cannot save settings', str(error))

    def reset(self):
        for key, value in self.values.items():
            value.set(DEFAULTS[key])
        self.camera.set(str(DEFAULTS['camera_index']))
        self.status.set('Defaults restored • Save settings to keep them')

    def start(self):
        if self.cap is not None:
            return
        try:
            camera = int(self.camera.get())
            if not 0 <= camera <= 10:
                raise ValueError('Camera index must be between 0 and 10.')
            self.cap = cv2.VideoCapture(camera)
            if not self.cap.isOpened():
                raise RuntimeError('Cannot open webcam. Check camera permissions or camera index.')
            self.hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
            self.running = False
            self.pause_button.config(text='Enable control')
            self.tick()
        except Exception as error:
            self.stop()
            messagebox.showerror('Camera error', str(error))

    def toggle(self):
        if self.cap is None:
            self.status.set('Start the camera first')
            return
        self.running = not self.running
        self.pinch_active = True
        self.scroll_anchor = None
        self.current_x, self.current_y = pyautogui.position()
        self.pause_button.config(text='Pause control' if self.running else 'Enable control')

    def tick(self):
        if self.cap is None:
            return
        try:
            ok, frame = self.cap.read()
            if not ok:
                raise RuntimeError('Camera stopped sending frames.')
            frame = cv2.flip(frame, 1)
            result = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            status = 'NO HAND' if self.running else 'CONTROL PAUSED'
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                lm = hand.landmark
                index, thumb = lm[8], lm[4]
                raised = [lm[a].y < lm[b].y for a, b in ((8, 6), (12, 10), (16, 14), (20, 18))]
                pinch = math.hypot(index.x - thumb.x, index.y - thumb.y) < self.values['pinch_threshold'].get()
                if self.running:
                    if all(raised):
                        status = 'OPEN PALM • PAUSED'
                        self.scroll_anchor = None
                    elif raised[:2] == [True, True] and raised[2:] == [False, False]:
                        status = 'SCROLL'
                        if self.scroll_anchor is not None:
                            delta = self.scroll_anchor - index.y
                            if abs(delta) > self.values['scroll_threshold'].get():
                                pyautogui.scroll(round(self.values['scroll_step'].get()) * (1 if delta > 0 else -1))
                                self.scroll_anchor = index.y
                        else:
                            self.scroll_anchor = index.y
                    else:
                        self.scroll_anchor = None
                        width, height = pyautogui.size()
                        speed = self.values['mouse_speed'].get()
                        target_x = max(1, min(width - 2, (0.5 + (index.x - 0.5) * speed / 0.8) * width))
                        target_y = max(1, min(height - 2, (0.5 + (index.y - 0.5) * speed / 0.8) * height))
                        # Keep smoothing consistent across camera frame rates.
                        now = time.monotonic()
                        dt = min(0.1, now - getattr(self, 'last_move', now - 1 / 30))
                        self.last_move = now
                        alpha = 1 - (1 - self.values['smooth'].get()) ** (dt * 30)
                        self.current_x += (target_x - self.current_x) * alpha
                        self.current_y += (target_y - self.current_y) * alpha
                        pyautogui.moveTo(self.current_x, self.current_y)
                        status = 'MOVING'
                        if pinch and not self.pinch_active and now - self.last_click > self.values['click_cooldown'].get():
                            pyautogui.click()
                            self.last_click = now
                            status = 'CLICK'
                self.pinch_active = pinch
                mp.solutions.drawing_utils.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
            else:
                self.pinch_active = False
                self.scroll_anchor = None
            self.status.set(status)
            cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            cv2.imshow('Gesture Camera - Q to stop', frame)
            if cv2.waitKey(1) & 0xff == ord('q') or cv2.getWindowProperty('Gesture Camera - Q to stop', cv2.WND_PROP_VISIBLE) < 1:
                self.stop()
                return
        except pyautogui.FailSafeException:
            self.stop()
            self.status.set('Emergency stop triggered • Restart camera to continue')
            return
        except Exception as error:
            self.stop()
            messagebox.showerror('Gesture control stopped', str(error))
            return
        self.root.after(15, self.tick)

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.hands is not None:
            self.hands.close()
            self.hands = None
        cv2.destroyAllWindows()
        self.scroll_anchor = None
        self.pinch_active = False
        self.pause_button.config(text='Enable control')
        self.status.set('Camera stopped')

    def close(self):
        self.stop()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    GestureApp(root)
    root.mainloop()
