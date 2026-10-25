"""Windows default-endpoint volume via Core Audio; no extra dependency."""
import ctypes
from ctypes import wintypes
import sys
import uuid


class GUID(ctypes.Structure):
    _fields_ = [('data', ctypes.c_ubyte*16)]

    def __init__(self, value):
        super().__init__()
        self.data[:] = uuid.UUID(value).bytes_le


class SystemVolume:
    def __init__(self):
        if sys.platform != 'win32':
            raise RuntimeError('System volume control currently requires Windows.')
        self.endpoint = ctypes.c_void_p()
        self.ole = ctypes.WinDLL('ole32')
        self.ole.CoUninitialize.restype = None
        self.ole.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
        result = self.ole.CoInitializeEx(None, 2)
        self.initialized = result in (0, 1)
        if result < 0 and (result & 0xffffffff) != 0x80010106:
            raise OSError('Cannot initialize Windows audio.')
        enum, device = ctypes.c_void_p(), ctypes.c_void_p()
        try:
            clsid = GUID('BCDE0395-E52F-467C-8E3D-C4579291692E')
            iid = GUID('A95664D2-9614-4F35-A746-DE8DB63617E6')
            create = self.ole.CoCreateInstance
            create.argtypes = [ctypes.POINTER(GUID), ctypes.c_void_p, wintypes.DWORD,
                               ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
            self.check(create(ctypes.byref(clsid), None, 23, ctypes.byref(iid), ctypes.byref(enum)))
            self.check(self.call(enum, 4, [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)],
                                 0, 1, ctypes.byref(device)))
            volume_iid = GUID('5CDF2C82-841E-4546-9722-0CF74078229A')
            self.check(self.call(device, 3, [ctypes.POINTER(GUID), wintypes.DWORD,
                                           ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
                                 ctypes.byref(volume_iid), 23, None, ctypes.byref(self.endpoint)))
        except Exception:
            self.close()
            raise
        finally:
            self.release(device)
            self.release(enum)

    @staticmethod
    def call(pointer, index, types, *args):
        table = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        fn = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *types)(table[index])
        return fn(pointer, *args)

    @staticmethod
    def check(result):
        if result < 0:
            raise OSError(f'Windows audio operation failed (0x{result & 0xffffffff:08x}).')

    @classmethod
    def release(cls, pointer):
        if pointer.value:
            cls.call(pointer, 2, [])
            pointer.value = None

    def get(self):
        value = ctypes.c_float()
        self.check(self.call(self.endpoint, 9, [ctypes.POINTER(ctypes.c_float)], ctypes.byref(value)))
        return value.value

    def set(self, value):
        self.check(self.call(self.endpoint, 7, [ctypes.c_float, ctypes.c_void_p],
                             max(0., min(1., value)), None))

    def close(self):
        self.release(self.endpoint)
        if getattr(self, 'initialized', False):
            self.ole.CoUninitialize()
            self.initialized = False
