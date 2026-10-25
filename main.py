import json
import math
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from ui import build, render_guide
from engine import GestureEngine
from queue import Empty

import pyautogui

SETTINGS_PATH = Path(__file__).with_name('settings.json')
DEFAULTS = dict(mouse_speed=1.0, smooth=0.5, pinch_threshold=0.045,
                click_cooldown=0.25, scroll_threshold=0.015, scroll_step=2,
                vertical_range=0.20,
                camera_index=0, two_hands=True, drag_hold=.45, hud_enabled=True)


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
        self.values = {}
        self.worker = None
        self.closing = False
        self.running = False
        settings = load_settings()
        self.control_mode = tk.StringVar(value='Mouse')
        self.hud_enabled = tk.BooleanVar(value=bool(settings['hud_enabled']))
        self.two_hands = tk.BooleanVar(value=bool(settings['two_hands']))
        build(self,settings)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0
        root.bind('<space>',self.on_space)
        root.bind('<Escape>',lambda _:self.stop())
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.last_snapshot = None
        self.poll_job = root.after(30,self.poll_worker)

    def snapshot(self):
        return dict(values={key:value.get() for key,value in self.values.items()},
                    mode=self.control_mode.get(),two_hands=self.two_hands.get(),
                    hud_enabled=self.hud_enabled.get())

    def send_config(self):
        options = self.snapshot()
        if self.worker is not None and self.worker.is_alive() and options != self.last_snapshot:
            self.worker.commands.put(('config',options))
            self.last_snapshot = options

    def poll_worker(self):
        if self.worker is not None:
            while True:
                try:
                    kind,payload = self.worker.messages.get_nowait()
                except Empty:
                    break
                if kind == 'status':
                    self.status.set(payload)
                elif kind == 'button':
                    self.pause_button.config(text=payload)
                    self.running = payload == 'Pause control'
                elif kind == 'opened':
                    self.status.set('Camera ready • Enable control to begin')
                elif kind == 'mode':
                    self.control_mode.set(payload)
                    self.update_guide()
                elif kind == 'closed':
                    self.running = False
                    self.pause_button.config(text='Enable control')
                    self.status.set('Camera stopped')
                elif kind == 'error' and not self.closing:
                    messagebox.showerror('Gesture control stopped',payload)
            if not self.worker.is_alive():
                self.worker = None
            else:
                self.send_config()
        if self.closing and self.worker is None:
            self.root.destroy()
            return
        self.poll_job = self.root.after(30,self.poll_worker)

    def start(self):
        if self.worker is not None and self.worker.is_alive():
            self.status.set('Camera is already running; wait if it is stopping')
            return
        self.status.set('Connecting to default camera…')
        self.running = False
        self.pause_button.config(text='Enable control')
        self.last_snapshot = self.snapshot()
        self.worker = GestureEngine(self.last_snapshot)
        self.worker.start()

    def toggle(self):
        if self.worker is None or not self.worker.is_alive() or self.worker.finished.is_set():
            self.status.set('Start the camera first')
            return
        self.send_config()
        self.worker.commands.put(('toggle',None))

    def recenter(self):
        if self.worker is not None and self.worker.is_alive():
            self.worker.commands.put(('recenter',None))
        self.status.set('Show your index finger at a comfortable height to recenter')

    def change_hand_mode(self):
        self.change_control_mode()

    def change_control_mode(self, *_):
        self.running = False
        self.pause_button.config(text='Enable control')
        self.update_guide()
        self.send_config()
        if self.worker is not None and self.worker.is_alive():
            self.worker.commands.put(('select_mode',self.control_mode.get()))
        self.status.set(f'{self.control_mode.get()} ready • Enable control to begin')

    def stop(self):
        if self.worker is not None and self.worker.is_alive():
            self.worker.request_stop()
            self.status.set('Stopping camera…')
        else:
            self.status.set('Camera stopped')
        self.running = False
        self.pause_button.config(text='Enable control')

    def close(self):
        self.closing = True
        self.stop()
        if self.worker is None:
            self.root.after_cancel(self.poll_job)
            self.root.destroy()

    def on_space(self, event):
        if event.widget.winfo_class() not in ('TSpinbox', 'TEntry', 'TCombobox'):
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
            settings.update(camera_index=camera, two_hands=self.two_hands.get(), hud_enabled=self.hud_enabled.get())
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
        self.hud_enabled.set(DEFAULTS['hud_enabled'])
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


    def update_guide(self):
        render_guide(self)



if __name__ == '__main__':
    root = tk.Tk()
    GestureApp(root)
    root.mainloop()
