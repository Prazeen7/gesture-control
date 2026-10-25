"""Frame-rate independent motion helpers (no camera or mouse side effects)."""
import math


def raised_fingers(landmarks):
    wrist = landmarks[0]
    def radius(i):
        p = landmarks[i]
        return math.hypot(p.x - wrist.x, p.y - wrist.y)
    return [radius(tip) > radius(joint) * 1.12
            for tip, joint in ((8, 6), (12, 10), (16, 14), (20, 18))]


def palm_source(right_open, left_open):
    # Prefer the left palm so the right hand can stay in its pointing pose.
    return 'left' if left_open else 'right' if right_open else None


class PalmScroll:
    """Palm swipes scroll directly; two fingers sustain the last direction."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.previous = None
        self.last_time = None
        self.remainder = 0.0
        self.direction = 0
        self.mode = None
        self.stroke_direction = 0

    def update(self, mode, y, amount, threshold, now, pointing_up=True):
        if mode != self.mode:
            self.previous = y
            self.last_time = now
            self.remainder = 0
            self.mode = mode
            self.stroke_direction = 0
            if mode == 'auto' and not self.direction:
                self.direction = 1 if pointing_up else -1
            return 0
        dt = max(0, min(.1, now - self.last_time))
        self.last_time = now
        if mode == 'palm_latched':
            # Return strokes cannot reverse an ongoing scroll. A closed hand
            # ends the gesture; reopening starts a new direction selection.
            if not self.stroke_direction:
                delta = self.previous - y
                if abs(delta) >= max(.008, threshold):
                    self.stroke_direction = 1 if delta > 0 else -1
                    self.direction = self.stroke_direction
            if self.stroke_direction:
                self.remainder += self.stroke_direction * amount * 5 * dt
        elif mode == 'palm':
            delta = self.previous - y
            if abs(delta) >= max(.002, threshold * .15):
                self.previous = y
                self.direction = 1 if delta > 0 else -1
                self.remainder += delta / .04 * amount
        elif mode == 'auto':
            self.remainder += self.direction * amount * 5 * dt
        steps = math.trunc(self.remainder)
        self.remainder -= steps
        return steps


def hand_roles(hands, handedness, two_hands):
    """MediaPipe handedness is for mirrored input, as used by the preview."""
    if not two_hands:
        return (hands[0] if hands else None), None
    roles = {}
    for hand, classification in zip(hands, handedness):
        label = classification.classification[0].label
        roles.setdefault(label, hand)
    return roles.get('Right'), roles.get('Left')


def screen_target(x, y, width, height, speed, vertical_range=0.20, center_y=0.5):
    # Center is calibrated to the user's comfortable fingertip height.
    nx = max(0.0, min(1.0, 0.5 + (x - 0.5) * speed / 0.7))
    ny = max(0.0, min(1.0, 0.5 + (y - center_y) * speed / vertical_range))
    return 1 + nx * (width - 3), 1 + ny * (height - 3)


def follow(current, target, responsiveness, dt):
    distance = math.hypot(target[0] - current[0], target[1] - current[1])
    # Suppress tiny tracking noise while allowing fast travel without heavy lag.
    if distance < 1.5:
        return current
    base = -math.log(max(0.001, 1 - responsiveness)) * 30
    alpha = 1 - math.exp(-(base + min(35, distance * 0.08)) * dt)
    return tuple(a + (b - a) * alpha for a, b in zip(current, target))


class ScrollMotion:
    def __init__(self):
        self.reset()

    def reset(self):
        self.anchor = None
        self.remainder = 0.0
        self.last_time = None

    def update(self, y, threshold, amount, now):
        if self.anchor is None:
            self.anchor = y
            self.last_time = now
            return 0
        dt = max(0, min(0.1, now - self.last_time))
        self.last_time = now
        delta = self.anchor - y
        if abs(delta) <= threshold:
            self.remainder = 0.0
            return 0
        # Displace slightly and hold to keep scrolling, like a joystick.
        rate = (abs(delta) - threshold) / 0.04 * amount * 5
        self.remainder += math.copysign(rate * dt, delta)
        steps = math.trunc(self.remainder)
        self.remainder -= steps
        return steps
