"""An independent OpenCV preview; a window move cannot block tracking."""
from queue import Queue, Empty, Full
from threading import Thread, Event
import cv2


class CameraPreview(Thread):
    def __init__(self, on_close):
        super().__init__(name='gesture-preview', daemon=True)
        self.frames = Queue(maxsize=1)
        self.finished = Event()
        self.on_close = on_close
        self.title = 'Gesture Camera - Q to stop'

    def submit(self, frame):
        if self.finished.is_set():
            return
        try:
            self.frames.put_nowait(frame)
        except Full:
            try:
                self.frames.get_nowait()
            except Empty:
                pass
            try:
                self.frames.put_nowait(frame)
            except Full:
                pass

    def close(self):
        self.finished.set()

    def run(self):
        opened = False
        try:
            while not self.finished.is_set():
                try:
                    frame = self.frames.get(timeout=.05)
                except Empty:
                    continue
                cv2.imshow(self.title, frame)
                opened = True
                if (cv2.waitKey(1) & 0xff == ord('q') or
                        cv2.getWindowProperty(self.title, cv2.WND_PROP_VISIBLE) < 1):
                    self.on_close()
                    break
        except cv2.error:
            self.on_close()
        finally:
            self.finished.set()
            if opened:
                try:
                    cv2.destroyWindow(self.title)
                except cv2.error:
                    pass
