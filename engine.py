"""Camera and input processing without Tk calls or UI-thread scheduling."""
import math
import time
from queue import Queue, Empty, Full
from threading import Thread, Event
import cv2
import mediapipe as mp
import pyautogui
from camera import open_camera
from camera_preview import CameraPreview
from interactions import PinchDrag, drag_target, keep_drag_mode
from mouse_input import move_drag_cursor
from features import FeatureModes, draw_hud
from motion import screen_target, follow, ScrollMotion, PalmScroll, hand_roles, raised_fingers, palm_source


class Value:
    def __init__(self, value, callback=None):
        self.value, self.callback = value, callback
    def get(self):
        return self.value
    def set(self, value):
        self.value = value
        if self.callback:
            self.callback(value)


class ButtonProxy:
    def __init__(self, emit):
        self.emit = emit
    def config(self, **options):
        self.emit('button', options.get('text', 'Enable control'))


class GestureEngine(Thread):
    def __init__(self, options):
        super().__init__(name='gesture-tracking', daemon=True)
        self.options = options
        self.commands = Queue()
        self.messages = Queue(maxsize=64)
        self.finished = Event()
        self.cap = self.hands = None
        self.active_camera = None
        self.running = False
        self.pinch_active = False
        self.scroll_anchor = None
        self.last_click = 0
        self.scroll_motion = ScrollMotion()
        self.palm_scroll = PalmScroll()
        self.mode = self.pending_mode = None
        self.mode_since = 0
        self.pinch_since = None
        self.center_y = None
        self.drag = PinchDrag()
        self.drag_origin = None
        self.features = FeatureModes()
        self.values = {key:Value(value) for key,value in options['values'].items()}
        self.two_hands = Value(options['two_hands'])
        self.hud_enabled = Value(options['hud_enabled'])
        self.control_mode = Value(options['mode'])
        self.status = Value('', lambda text:self.emit('status',text))
        self.pause_button = ButtonProxy(self.emit)
        self.preview = CameraPreview(self.request_stop)
        self.processed_frames = 0

    def emit(self, kind, payload):
        try:
            self.messages.put_nowait((kind,payload))
        except Full:
            if kind == 'status':
                return
            try:
                self.messages.get_nowait()
            except Empty:
                pass
            self.messages.put_nowait((kind,payload))

    def request_stop(self):
        self.finished.set()

    def configure(self, options):
        changed = options['mode'] != self.control_mode.get() or options['two_hands'] != self.two_hands.get()
        self.options = options
        for key,value in options['values'].items():
            self.values[key].set(value)
        self.hud_enabled.set(options['hud_enabled'])
        self.two_hands.set(options['two_hands'])
        self.control_mode.set(options['mode'])
        if changed:
            self.change_control_mode()

    def run(self):
        try:
            self.cap = open_camera(0)
            self.hands = mp.solutions.hands.Hands(max_num_hands=2,
                min_detection_confidence=.7,min_tracking_confidence=.7)
            self.active_camera = 0
            self.preview.start()
            self.emit('opened',0)
            while not self.finished.is_set():
                while True:
                    try:
                        command,payload = self.commands.get_nowait()
                    except Empty:
                        break
                    if command == 'config':
                        self.configure(payload)
                    elif command == 'toggle':
                        self.toggle()
                    elif command == 'recenter':
                        self.recenter()
                if not self.finished.is_set():
                    self.tick()
        except Exception as error:
            self.emit('error',str(error))
        finally:
            self.stop()
            self.emit('closed',None)

    def update_guide(self):
        pass  # UI cards are updated only by the main thread.

    def stop(self):
        self.finished.set()
        self.running = False
        try:
            self.release_drag()
        finally:
            try:
                self.features.reset()
            finally:
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                if self.hands is not None:
                    self.hands.close()
                    self.hands = None
                self.preview.close()
                if self.preview.is_alive():
                    self.preview.join(timeout=1)
                self.active_camera = None


    def change_control_mode(self, *_):
        self.release_drag()
        self.features.reset()
        self.running = False
        self.mode = self.pending_mode = None
        self.center_y = None
        self.palm_scroll.reset()
        self.scroll_motion.reset()
        self.pause_button.config(text='Enable control')
        self.update_guide()
        self.status.set(f'{self.control_mode.get()} ready • Enable control to begin')


    def release_drag(self):
        self.drag_origin = None
        if self.drag.update(False, time.monotonic(), enabled=False) == 'up':
            # Mouse-up must work even if the corner failsafe caused the stop.
            failsafe = pyautogui.FAILSAFE
            try:
                pyautogui.FAILSAFE = False
                pyautogui.mouseUp()
            finally:
                pyautogui.FAILSAFE = failsafe


    def update_drag(self, pinch, now, enabled):
        self.drag.hold_seconds = self.values['drag_hold'].get()
        event = self.drag.update(pinch, now, enabled, self.values['click_cooldown'].get())
        if event == 'up':
            failsafe = pyautogui.FAILSAFE
            try:
                pyautogui.FAILSAFE = False
                pyautogui.mouseUp()
            finally:
                pyautogui.FAILSAFE = failsafe
        elif event == 'down':
            pyautogui.mouseDown()
        elif event == 'click':
            pyautogui.click()
        return event


    def toggle(self):
        if self.cap is None:
            self.status.set('Start the camera first')
            return
        self.release_drag()
        self.features.reset()
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
            if self.control_mode.get() != 'Mouse':
                self.release_drag()
                status = self.features.process(frame, self.control_mode.get(),
                    hand if pointer_available else None, action_hand,
                    self.two_hands.get(), self.running, self.values['pinch_threshold'].get())
            elif hand is not None:
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
                # Finger folding during a held pinch must not select scroll or pause.
                if pointer_available and action_lm is not None and keep_drag_mode(
                        pinch, self.drag.started, self.drag.dragging, self.mode):
                    desired = 'move'
                drag_event = self.update_drag(pinch, now, self.running and pointer_available and self.mode == 'move'
                    and action_lm is not None and desired == 'move')
                if drag_event == 'down':
                    # Map relative travel from the grab point, not the fingertip's
                    # shifted absolute position after forming a pinch.
                    px, py = pyautogui.position()
                    self.current_x, self.current_y = px, py
                    self.drag_origin = (index.x, index.y, px, py)
                elif not self.drag.dragging:
                    self.drag_origin = None
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
                        if self.drag.dragging and self.drag_origin is not None:
                            target = drag_target(self.drag_origin, index.x, index.y, width, height,
                                self.values['mouse_speed'].get(), self.values['vertical_range'].get())
                        dt = max(0.001, min(0.1, now - getattr(self, 'last_move', now - 1 / 30)))
                        self.last_move = now
                        # Freeze before a pinch closes: pulling the index finger toward
                        # the thumb should not pull the pointer off the click target.
                        freeze = pinch and not self.two_hands.get() and not self.drag.dragging
                        if not freeze:
                            self.current_x, self.current_y = follow(
                                (self.current_x, self.current_y), target,
                                self.values['smooth'].get(), dt)
                            if self.drag.dragging:
                                pyautogui.failSafeCheck()
                                move_drag_cursor(self.current_x, self.current_y, width, height)
                            else:
                                pyautogui.moveTo(self.current_x, self.current_y)
                        status = 'MOVING' if not pinch else 'PINCH'
                        if self.drag.dragging:
                            status = 'DRAGGING - RELEASE PINCH TO DROP'
                        elif drag_event == 'click':
                            status = 'CLICK'
                        elif pinch:
                            status = 'PINCH - HOLD TO DRAG / RELEASE TO CLICK'
                if not pinch and action_lm is not None:
                    self.pinch_clicked = False
                self.pinch_active = pinch
            else:
                self.release_drag()
                self.features.selector.update(None, False, time.monotonic(), enabled=False)
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
            if self.hud_enabled.get():
                draw_hud(frame, status, self.control_mode.get(), detected, self.drag.dragging)
            else:
                cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
            self.preview.submit(frame)
            self.processed_frames += 1
        except pyautogui.FailSafeException:
            self.stop()
            self.status.set('Emergency stop triggered • Restart camera to continue')
            return
        except Exception as error:
            self.stop()
            self.emit('error',str(error))
            return

