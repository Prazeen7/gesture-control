import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace as NS
import numpy as np
from interactions import PinchDrag, keep_drag_mode
from engine import GestureEngine

OPTIONS=dict(mode='Mouse',two_hands=True,hud_enabled=False,values=dict(mouse_speed=1,smooth=.5,vertical_range=.2,pinch_threshold=.045,click_cooldown=.25,drag_hold=.45,scroll_threshold=.015,scroll_step=2))

def hand(open_palm=False):
    lm=[NS(x=.5,y=.9,z=0) for _ in range(21)]
    for tip,joint in ((8,6),(12,10),(16,14),(20,18)):
        lm[joint]=NS(x=.5,y=.6,z=0)
        lm[tip]=NS(x=.5,y=.3 if open_palm or tip==8 else .8,z=0)
    lm[4]=NS(x=.1,y=.5,z=0)
    return NS(landmark=lm)

class ClickReleaseTests(unittest.TestCase):
    def test_release_frame_keeps_mouse_until_pending_click_finishes(self):
        self.assertTrue(keep_drag_mode(False,1,False,'move'))
        self.assertTrue(keep_drag_mode(False,1,True,'move'))
        self.assertFalse(keep_drag_mode(False,None,False,'move'))

    def test_quick_camera_pinch_clicks_once(self):
        gesture=PinchDrag()
        gesture.update(False,0)
        gesture.update(True,.1)
        self.assertEqual(gesture.update(False,.133),'click')
        self.assertIsNone(gesture.update(False,.2))

    def test_cancel_still_never_clicks(self):
        gesture=PinchDrag()
        gesture.update(False,0)
        gesture.update(True,.1)
        self.assertIsNone(gesture.update(False,.2,enabled=False))

    def test_drag_release_is_up_without_click(self):
        gesture=PinchDrag()
        gesture.update(False,0)
        gesture.update(True,.1)
        self.assertEqual(gesture.update(True,.6),'down')
        self.assertEqual(gesture.update(False,.7),'up')

    @patch('engine.mp.solutions.drawing_utils.draw_landmarks')
    @patch('engine.pyautogui')
    def test_actual_frame_dispatch_clicks_before_open_palm_scroll(self, mouse, draw):
        class Failsafe(Exception): pass
        mouse.FailSafeException=Failsafe
        mouse.size.return_value=(1920,1080)
        mouse.position.return_value=(800,450)
        engine=GestureEngine(OPTIONS)
        engine.cap=Mock()
        engine.cap.read.return_value=(True,np.zeros((480,640,3),dtype=np.uint8))
        engine.hands=Mock()
        engine.hands.process.return_value=NS(multi_hand_landmarks=[hand(),hand(True)],
            multi_handedness=[NS(classification=[NS(label='Right')]),NS(classification=[NS(label='Left')])])
        engine.preview=Mock()
        engine.running=True
        engine.mode=engine.pending_mode='move'
        engine.current_x,engine.current_y=800,450
        engine.drag.armed=True
        engine.drag.started=1
        engine.pinch_active=True
        with patch('engine.time.monotonic',return_value=1.2):
            engine.tick()
        mouse.click.assert_called_once()
        mouse.scroll.assert_not_called()
        self.assertEqual(engine.status.get(),'CLICK')
        with patch('engine.time.monotonic',return_value=1.3):
            engine.tick()
        mouse.click.assert_called_once()
        self.assertEqual(engine.pending_mode,'palm_left')

if __name__=='__main__':
    unittest.main()
