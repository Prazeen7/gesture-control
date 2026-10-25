"""Camera backend fallback, including cleanup of failed attempts."""
import sys
import cv2


def open_camera(index):
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if sys.platform == 'win32' else [cv2.CAP_ANY]
    for backend in backends:
        cap = None
        ready = False
        try:
            cap = cv2.VideoCapture(index, backend)
            if not cap.isOpened():
                continue
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            for _ in range(5):
                ok, frame = cap.read()
                if ok and frame is not None and frame.size:
                    ready = True
                    return cap
        except cv2.error:
            pass
        finally:
            if cap is not None and not ready:
                cap.release()
    raise RuntimeError(f'No usable camera at index {index}. An index only works if a camera exists there. '
                       'Try index 0, close other camera apps, and check Windows camera access.')
