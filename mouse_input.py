"""Native Windows drag motion, including a real mouse-input event."""
import ctypes
import sys


class MouseInput(ctypes.Structure):
    _fields_ = [('dx',ctypes.c_int32),('dy',ctypes.c_int32),
                ('mouseData',ctypes.c_uint32),('dwFlags',ctypes.c_uint32),
                ('time',ctypes.c_uint32),('dwExtraInfo',ctypes.c_size_t)]


class InputPayload(ctypes.Union):
    _fields_ = [('mi',MouseInput)]


class Input(ctypes.Structure):
    _anonymous_ = ('payload',)
    _fields_ = [('type',ctypes.c_uint32),('payload',InputPayload)]


def move_drag_cursor(x, y, width, height, sender=None):
    """Move while the existing left-button hold remains active.

    No additional DOWN event is emitted: Windows interprets those as state
    changes, not an indication that a button is still held.
    """
    if sys.platform != 'win32' and sender is None:
        import pyautogui
        pyautogui.moveTo(x,y)
        return
    if sender is None:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        sender = user32.SendInput
        sender.argtypes = [ctypes.c_uint,ctypes.POINTER(Input),ctypes.c_int]
        sender.restype = ctypes.c_uint
    # Absolute input maps 0..65535 to the primary monitor, as cursor mapping does.
    dx = round(max(0,min(width-1,x))*65535/max(1,width-1))
    dy = round(max(0,min(height-1,y))*65535/max(1,height-1))
    event = Input(type=0,mi=MouseInput(dx,dy,0,0x8001,0,0))
    if sender(1,ctypes.byref(event),ctypes.sizeof(Input)) != 1:
        raise OSError('Windows rejected drag motion. Pause control and check the target app permissions.')
