"""Air keyboard, volume gesture mode, and camera HUD rendering."""
import math
import time
import cv2
import pyautogui
from interactions import AirKeySelector, keyboard_keys, key_at, volume_fraction
from system_volume import SystemVolume


class FeatureModes:
    def __init__(self):
        self.volume = None
        self.volume_value = None
        self.volume_time = 0
        self.selector = AirKeySelector()
        self.pinch_active = False
        self.numbers = False
        self.shift = False
        self.last_key = ''

    def reset(self):
        self.selector = AirKeySelector()
        self.pinch_active = False
        self.last_key = ''
        self.volume_time = 0
        if self.volume is not None:
            self.volume.close()
            self.volume = None
        self.volume_value = None

    def process(self, frame, mode, pointer, action, two_hands, enabled, threshold):
        lm = pointer.landmark if pointer is not None else None
        action_lm = action.landmark if action is not None else (None if two_hands else lm)
        now = time.monotonic()
        if mode == 'Volume':
            return self.process_volume(frame, lm, enabled, now)
        height, width = frame.shape[:2]
        keys = keyboard_keys(width, height, self.numbers)
        x, y = (int(lm[8].x*width), int(lm[8].y*height)) if lm is not None else (-1, -1)
        hovered = key_at(keys, x, y)
        valid = enabled and lm is not None and action_lm is not None
        gap = math.hypot(action_lm[8].x-action_lm[4].x, action_lm[8].y-action_lm[4].y) if action_lm else 1
        pinch = gap < threshold*(1.45 if self.pinch_active else 1)
        chosen = self.selector.update(hovered, pinch, now, valid)
        self.pinch_active = pinch if valid else False
        if chosen:
            self.type_key(chosen)
        for label, (left, top, w, h) in keys:
            highlighted = label == (self.selector.target if pinch else hovered)
            cv2.rectangle(frame, (left, top), (left+w, top+h), (90, 95, 25) if highlighted else (30, 36, 44), -1)
            cv2.rectangle(frame, (left, top), (left+w, top+h), (230, 215, 60) if highlighted else (100, 110, 110), 1)
            text = label.lower() if len(label) == 1 and label.isalpha() and not self.shift else label
            scale = .52 if len(label) > 1 else .65
            size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0]
            cv2.putText(frame, text, (left+(w-size[0])//2, top+(h+size[1])//2), cv2.FONT_HERSHEY_SIMPLEX, scale, (245, 250, 250), 1, cv2.LINE_AA)
        if lm is not None:
            cv2.circle(frame, (x, y), 8, (0, 230, 255), 2)
        hint = 'Aim RIGHT index + pinch LEFT to type' if two_hands else 'Aim index + pinch to type'
        cv2.putText(frame, hint, (18, int(height*.36)), cv2.FONT_HERSHEY_SIMPLEX, .50, (235, 240, 240), 1, cv2.LINE_AA)
        if not enabled:
            return 'KEYBOARD PAUSED'
        return f'KEY: {self.last_key or "-"} | HOVER: {hovered or "-"}' if lm else 'SHOW POINTING HAND'

    def type_key(self, label):
        self.last_key = label
        if label in ('123', 'ABC'):
            self.numbers = not self.numbers
        elif label == 'Shift':
            self.shift = not self.shift
        elif label in ('Space', 'Back', 'Enter'):
            pyautogui.press({'Space':'space', 'Back':'backspace', 'Enter':'enter'}[label])
        else:
            pyautogui.write(label if self.shift else label.lower())
            self.shift = False

    def process_volume(self, frame, lm, enabled, now):
        if not enabled or lm is None:
            return 'VOLUME PAUSED' if not enabled else 'SHOW RIGHT HAND FOR VOLUME'
        # Only the selected mode can touch audio; mouse clicks/scroll are bypassed.
        if self.volume is None:
            self.volume = SystemVolume()
            self.volume_value = self.volume.get()
        a, b = lm[4], lm[8]
        gap = math.hypot(a.x-b.x, a.y-b.y)
        palm = math.hypot(lm[9].x-lm[0].x, lm[9].y-lm[0].y)
        target = volume_fraction(gap, palm)
        if now-self.volume_time >= .1:
            change = max(-.05, min(.05, target-self.volume_value))
            if abs(change) >= .01:
                self.volume_value = max(0., min(1., self.volume_value+change))
                self.volume.set(self.volume_value)
            self.volume_time = now
        height, width = frame.shape[:2]
        p, q = (int(a.x*width),int(a.y*height)), (int(b.x*width),int(b.y*height))
        cv2.line(frame, p, q, (255, 230, 0), 3)
        cv2.circle(frame, p, 9, (255, 230, 0), 2)
        cv2.circle(frame, q, 9, (255, 230, 0), 2)
        cv2.rectangle(frame, (35, 120), (62, height-65), (80, 90, 100), 1)
        fill = int((height-185)*self.volume_value)
        cv2.rectangle(frame, (36, height-66-fill), (61,height-66), (220, 210, 0), -1)
        return f'VOLUME {round(self.volume_value*100)}% - WIDEN / NARROW THUMB + INDEX'


def draw_hud(frame, status, mode, detected, dragging=False):
    height, width = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 92), (20, 24, 32), -1)
    cv2.rectangle(overlay, (0, height-38), (width, height), (20, 24, 32), -1)
    cv2.addWeighted(overlay, .80, frame, .20, 0, frame)
    cyan = (235, 220, 55)
    cv2.putText(frame, f'GESTURE / {mode.upper()}', (18, 27), cv2.FONT_HERSHEY_SIMPLEX, .65, cyan, 2, cv2.LINE_AA)
    # Keep long status messages inside the frame.
    scale = min(.51, (width-36)/max(1,cv2.getTextSize(status,cv2.FONT_HERSHEY_SIMPLEX,1,1)[0][0]))
    cv2.putText(frame, status, (18, 56), cv2.FONT_HERSHEY_SIMPLEX, scale, (240, 245, 245), 1, cv2.LINE_AA)
    cv2.putText(frame, f'HANDS {len(detected)}   |   {"DRAG ACTIVE" if dragging else "TRACKING"}   |   Q: STOP', (18, height-13), cv2.FONT_HERSHEY_SIMPLEX, .46, cyan, 1, cv2.LINE_AA)
    for hand in detected:
        xs, ys = [p.x*width for p in hand.landmark], [p.y*height for p in hand.landmark]
        x1,x2 = max(4,int(min(xs))-12),min(width-4,int(max(xs))+12)
        y1,y2 = max(96,int(min(ys))-12),min(height-42,int(max(ys))+12)
        if y2 <= y1:
            continue
        for x,y,sx,sy in ((x1,y1,1,1),(x2,y1,-1,1),(x1,y2,1,-1),(x2,y2,-1,-1)):
            cv2.line(frame,(x,y),(x+sx*18,y),cyan,2)
            cv2.line(frame,(x,y),(x,y+sy*18),cyan,2)
