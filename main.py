import json
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from ui import build, render_guide
from camera import open_camera

import cv2
import mediapipe as mp
import pyautogui
from motion import screen_target, follow, ScrollMotion, hand_roles, raised_fingers, PalmScroll, palm_source

SETTINGS_PATH = Path(__file__).with_name('settings.json')
DEFAULTS = dict(mouse_speed=1.0, smooth=0.5, pinch_threshold=0.045,
                click_cooldown=0.25, scroll_threshold=0.015, scroll_step=2,
                vertical_range=0.20,
                camera_index=0, two_hands=True)


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
        self.active_camera = None
        self.tick_job = None
        self.running = False
        self.pinch_active = False
        self.scroll_anchor = None
        self.last_click = 0
        self.scroll_motion = ScrollMotion()
        self.palm_scroll = PalmScroll()
        self.mode = None
        self.pending_mode = None
        self.mode_since = 0
        self.pinch_since = None
        self.center_y = None
        self.values = {}
        settings = load_settings()
        self.two_hands = tk.BooleanVar(value=bool(settings['two_hands']))
        build(self, settings)
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
            if not self.update_scroll_speed():
                raise ValueError('Enter a positive finite scroll amount.')
            camera = int(self.camera.get())
            if not 0 <= camera <= 10:
                raise ValueError('Camera index must be between 0 and 10.')
            settings = {key: value.get() for key, value in self.values.items()}
            settings.update(camera_index=camera, two_hands=self.two_hands.get())
            SETTINGS_PATH.write_text(json.dumps(settings, indent=4) + '\n')
            self.status.set('Settings saved')
        except (ValueError, OSError) as error:
            messagebox.showerror('Cannot save settings', str(error))

    def reset(self):
        for key, value in self.values.items():
            value.set(DEFAULTS[key])
        self.camera.set(str(DEFAULTS['camera_index']))
        self.scroll_input.set(str(DEFAULTS['scroll_step']))
        self.two_hands.set(DEFAULTS['two_hands'])
        self.change_hand_mode()
        self.status.set('Defaults restored • Save settings to keep them')

    def update_scroll_speed(self, *_):
        try:
            speed = float(self.scroll_input.get())
            if not math.isfinite(speed) or speed <= 0:
                raise ValueError
            self.values['scroll_step'].set(speed)
            self.scroll_hint.config(text='Applied immediately')
            return True
        except ValueError:
            self.scroll_hint.config(text='Enter a positive number')
            return False

    def change_hand_mode(self):
        self.update_guide()
        self.center_y = None
        self.mode = self.pending_mode = None
        self.pinch_active = self.pinch_clicked = True
        self.pinch_since = None
        self.scroll_motion.reset()
        self.palm_scroll.reset()
        self.status.set('Hand mode changed • show your pointing hand to recenter')

    def update_guide(self):
        render_guide(self)

    def start(self):
        try:
            camera = int(self.camera.get())
            if not 0 <= camera <= 10:
                raise ValueError('Camera index must be between 0 and 10.')
        except ValueError as error:
            messagebox.showerror('Camera selection', str(error))
            return
        if self.cap is not None and camera == self.active_camera:
            self.status.set(f'Camera {camera} is already connected')
            return
        previous = self.active_camera
        self.stop()
        try:
            self.connect_camera(camera)
        except Exception as error:
            self.stop()
            restored = False
            if previous is not None:
                try:
                    self.connect_camera(previous)
                    self.camera.set(str(previous))
                    restored = True
                except Exception:
                    self.stop()
            detail = '\n\nPrevious camera restored; control is paused.' if restored else '\n\nClose other camera apps, check Windows camera permissions, then retry Start camera.'
            messagebox.showerror('Camera unavailable', str(error) + detail)

    def connect_camera(self, index):
        self.status.set(f'Connecting to camera {index}…')
        self.root.update_idletasks()
        self.cap = open_camera(index)
        self.hands = mp.solutions.hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.active_camera = index
        self.center_y = None
        self.running = False
        self.pause_button.config(text='Enable control')
        self.tick()

    def toggle(self):
        if self.cap is None:
            self.status.set('Start the camera first')
            return
        self.running = not self.running
        self.center_y = None
        self.mode = None
        self.pending_mode = None
        self.scroll_motion.reset()
        self.palm_scroll.reset()
        self.last_move = time.monotonic()
        self.pinch_active = True
        self.pinch_clicked = True
        self.pinch_since = None
        self.scroll_anchor = None
        self.current_x, self.current_y = pyautogui.position()
        self.pause_button.config(text='Pause control' if self.running else 'Enable control')

    def recenter(self):
        self.center_y = None
        self.status.set('Show your index finger at a comfortable height to recenter')

    def tick(self):
        self.tick_job = None
        if self.cap is None:
            return
        try:
            ok, frame = self.cap.read()
            if not ok:
                raise RuntimeError('Camera stopped sending frames.')
            frame = cv2.flip(frame, 1)
            result = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            status = 'NO HAND' if self.running else 'CONTROL PAUSED'
            detected = result.multi_hand_landmarks or []
            for visible_hand in detected:
                mp.solutions.drawing_utils.draw_landmarks(frame, visible_hand, mp.solutions.hands.HAND_CONNECTIONS)
            hand, action_hand = hand_roles(detected, result.multi_handedness or [], self.two_hands.get())
            pointer_available = hand is not None
            # A left palm can scroll even when the pointing hand leaves the camera.
            if (hand is None and self.two_hands.get() and action_hand is not None
                    and all(raised_fingers(action_hand.landmark))):
                hand = action_hand
            if hand is not None:
                lm = hand.landmark
                index, thumb = lm[8], lm[4]
                raised = raised_fingers(lm)
                action_lm = action_hand.landmark if action_hand is not None else (None if self.two_hands.get() else lm)
                now = time.monotonic()
                gap = math.hypot(action_lm[8].x - action_lm[4].x, action_lm[8].y - action_lm[4].y) if action_lm is not None else 1.0
                threshold = self.values['pinch_threshold'].get()
                # Separate press/release thresholds prevent repeated clicks from noise.
                pinch = gap < threshold * (1.45 if self.pinch_active else 1.0)
                # Ring/pinky need not both be perfectly folded for two-finger scrolling.
                action_raised = raised_fingers(action_lm) if action_lm is not None else [False]*4
                scroll_gesture = all(action_raised[:2]) and not all(action_raised)
                desired = 'pause' if all(raised) else ('scroll' if scroll_gesture else 'move')
                if self.two_hands.get():
                    source = palm_source(pointer_available and all(raised), all(action_raised))
                    desired = 'palm_' + source if source else ('auto' if all(raised[:2]) and not all(raised[2:]) else 'move')
                if action_lm is None:
                    self.pinch_clicked = True
                    self.pinch_since = None
                if desired != self.pending_mode:
                    self.pending_mode, self.mode_since = desired, now
                if now - self.mode_since >= 0.10 and desired != self.mode:
                    self.mode = desired
                    self.scroll_motion.reset()
                    self.palm_scroll.mode = None
                    self.last_move = now
                    self.current_x, self.current_y = pyautogui.position()
                if pinch and self.pinch_since is None:
                    self.pinch_since = now
                if not pinch:
                    self.pinch_since = None
                if self.running:
                    if self.mode == 'pause':
                        status = 'PAUSED'
                    elif desired != self.mode and self.mode != 'move':
                        status = 'CHANGING GESTURE'
                    elif self.mode in ('palm_left', 'palm_right', 'auto'):
                        # Whole-hand position averages wrist, palm and fingertips.
                        scroll_lm = action_lm if self.mode == 'palm_left' else lm
                        palm_y = sum(scroll_lm[i].y for i in (0, 5, 9, 13, 17, 8, 12, 16, 20)) / 9
                        steps = self.palm_scroll.update('auto' if self.mode == 'auto' else 'palm_latched', palm_y,
                            self.values['scroll_step'].get(), self.values['scroll_threshold'].get(),
                            now, pointing_up=(lm[8].y + lm[12].y) / 2 < lm[0].y)
                        if self.mode == 'auto':
                            status = 'AUTO SCROLL'
                        elif not self.palm_scroll.stroke_direction:
                            status = 'PALM READY - MOVE UP / DOWN'
                        else:
                            status = 'SCROLL UP - CLOSE PALM TO STOP' if self.palm_scroll.stroke_direction > 0 else 'SCROLL DOWN - CLOSE PALM TO STOP'
                        if steps:
                            pyautogui.scroll(steps)
                    elif self.mode == 'scroll':
                        status = 'SCROLL'
                        # Average fingertips to reduce noise from a single landmark.
                        steps = self.scroll_motion.update((action_lm[8].y + action_lm[12].y) / 2,
                                                          self.values['scroll_threshold'].get(),
                                                          self.values['scroll_step'].get(), now)
                        if steps:
                            pyautogui.scroll(steps)
                    elif self.mode == 'move' and pointer_available and desired == 'move':
                        self.palm_scroll.mode = None
                        if self.center_y is None:
                            self.center_y = index.y
                        width, height = pyautogui.size()
                        target = screen_target(index.x, index.y, width, height,
                                               self.values['mouse_speed'].get(),
                                               self.values['vertical_range'].get(), self.center_y)
                        dt = max(0.001, min(0.1, now - getattr(self, 'last_move', now - 1 / 30)))
                        self.last_move = now
                        # Freeze before a pinch closes: pulling the index finger toward
                        # the thumb should not pull the pointer off the click target.
                        freeze = pinch and not self.two_hands.get()
                        if not freeze:
                            self.current_x, self.current_y = follow(
                                (self.current_x, self.current_y), target,
                                self.values['smooth'].get(), dt)
                            pyautogui.moveTo(self.current_x, self.current_y)
                        status = 'MOVING' if not pinch else 'PINCH'
                        if (desired == 'move' and action_lm is not None and pinch and self.pinch_since is not None
                                and now - self.pinch_since >= 0.045
                                and not getattr(self, 'pinch_clicked', False)
                                and now - self.last_click >= self.values['click_cooldown'].get()):
                            pyautogui.click()
                            self.last_click = now
                            self.pinch_clicked = True
                            status = 'CLICK'
                if not pinch and action_lm is not None:
                    self.pinch_clicked = False
                self.pinch_active = pinch
            else:
                if self.two_hands.get() and detected:
                    status = 'SHOW RIGHT HAND • LEFT HAND IS FOR CLICK'
                self.pinch_active = True
                self.pinch_clicked = True
                self.pinch_since = None
                self.mode = None
                self.pending_mode = None
                self.scroll_motion.reset()
                self.palm_scroll.reset()
                self.scroll_anchor = None
            self.status.set(status)
            if self.center_y is not None:
                half_range = self.values['vertical_range'].get() / (2 * self.values['mouse_speed'].get())
                for edge in (self.center_y - half_range, self.center_y + half_range):
                    y = max(0, min(frame.shape[0] - 1, int(edge * frame.shape[0])))
                    cv2.line(frame, (0, y), (frame.shape[1], y), (255, 190, 0), 1)
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
        self.tick_job = self.root.after(1, self.tick)

    def stop(self):
        if self.tick_job is not None:
            self.root.after_cancel(self.tick_job)
            self.tick_job = None
        self.active_camera = None
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.hands is not None:
            self.hands.close()
            self.hands = None
        cv2.destroyAllWindows()
        self.scroll_anchor = None
        self.palm_scroll.reset()
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
