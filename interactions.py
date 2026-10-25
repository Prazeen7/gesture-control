"""State machines for click/drag and the camera-space air keyboard."""
import math


def drag_target(origin, x, y, width, height, speed, vertical_range):
    start_x, start_y, cursor_x, cursor_y = origin
    return (max(1, min(width-2, cursor_x+(x-start_x)*speed*width/.7)),
            max(1, min(height-2, cursor_y+(y-start_y)*speed*height/vertical_range)))


def keep_drag_mode(pinched, started, dragging, current_mode):
    return pinched and (started is not None or dragging or current_mode == 'move')


class PinchDrag:
    def __init__(self, hold_seconds=.45):
        self.hold_seconds = hold_seconds
        self.started = None
        self.dragging = False
        self.armed = False
        self.last_click = -math.inf

    def update(self, pinched, now, enabled=True, cooldown=.25):
        if not enabled:
            event = 'up' if self.dragging else None
            self.started = None
            self.dragging = False
            self.armed = False
            return event
        if not pinched:
            event = None
            if self.dragging:
                event = 'up'
            elif self.started is not None and now-self.started >= .045 and now-self.last_click >= cooldown:
                event = 'click'
                self.last_click = now
            self.started = None
            self.dragging = False
            self.armed = True
            return event
        if not self.armed:
            return None
        if self.started is None:
            self.started = now
        if not self.dragging and now-self.started >= self.hold_seconds:
            self.dragging = True
            return 'down'
        return None


def volume_fraction(gap, palm_size):
    """Use hand-relative distance so camera depth has less effect."""
    ratio = gap / max(.01, palm_size)
    return max(0., min(1., (ratio-.20)/1.30))


KEY_ROWS = [list('QWERTYUIOP'), list('ASDFGHJKL'), list('ZXCVBNM'),
            ['Shift', 'Space', 'Back', 'Enter', '123']]
NUMBER_ROWS = [list('1234567890'), list('-/:;()$&@'), list('.,?!\'"+'),
               ['Shift', 'Space', 'Back', 'Enter', 'ABC']]


def keyboard_keys(width, height, numbers=False):
    rows = NUMBER_ROWS if numbers else KEY_ROWS
    left, top = int(width*.03), int(height*.40)
    total, row_h = int(width*.94), max(24, int(height*.125))
    keys = []
    for row, labels in enumerate(rows):
        cell = total/len(labels)
        for col, label in enumerate(labels):
            x, y = int(left+col*cell), top+row*row_h
            keys.append((label, (x+2, y+2, int(cell)-4, row_h-4)))
    return keys


def key_at(keys, x, y):
    for label, (left, top, width, height) in keys:
        if left <= x < left+width and top <= y < top+height:
            return label
    return None


class AirKeySelector:
    def __init__(self):
        self.armed = False
        self.target = None
        self.started = None

    def update(self, hovered, pinched, now, enabled=True):
        if not enabled:
            self.armed = False
            self.started = None
            self.target = None
            return None
        if not pinched:
            self.armed = True
            self.started = None
            self.target = None
            return None
        if not self.armed:
            return None
        if self.started is None:
            self.started = now
            self.target = hovered
        if now-self.started >= .08:
            self.armed = False
            return self.target
        return None
