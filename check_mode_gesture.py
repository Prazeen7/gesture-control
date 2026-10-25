import unittest
from unittest.mock import patch
from types import SimpleNamespace as Point
from interactions import ModeCycle, thumbs_up
from engine import GestureEngine
OPTIONS=dict(mode='Mouse',two_hands=True,hud_enabled=False,values=dict(mouse_speed=1,smooth=.5,vertical_range=.2,pinch_threshold=.045,click_cooldown=.25,drag_hold=.45,scroll_threshold=.015,scroll_step=2))

class ModeGestureTests(unittest.TestCase):
    def test_hold_fires_once_and_requires_release(self):
        gesture=ModeCycle()
        self.assertIsNone(gesture.update(True,0))
        self.assertIsNone(gesture.update(True,1))
        self.assertEqual(gesture.update(True,1.3),'switch')
        self.assertIsNone(gesture.update(True,5))
        self.assertTrue(gesture.blocked)
        gesture.update(False,6)
        self.assertEqual(gesture.update(False,6.3),'release')
        self.assertFalse(gesture.blocked)
        gesture.update(True,7)
        self.assertEqual(gesture.update(True,8.3),'switch')

    def test_brief_pose_does_not_switch(self):
        gesture=ModeCycle()
        gesture.update(True,0)
        self.assertIsNone(gesture.update(False,.5))
        gesture.update(True,.6)
        self.assertIsNone(gesture.update(True,1.3))

    def thumb(self):
        lm=[Point(x=.5,y=.8,z=0) for _ in range(21)]
        lm[3]=Point(x=.5,y=.5,z=0)
        lm[4]=Point(x=.5,y=.35,z=0)
        lm[5]=Point(x=.5,y=.6,z=0)
        return Point(landmark=lm)

    def test_thumb_must_be_up_and_other_fingers_folded(self):
        lm=self.thumb().landmark
        self.assertTrue(thumbs_up(lm,[False]*4))
        self.assertFalse(thumbs_up(lm,[True,False,False,False]))
        lm[4]=Point(x=.7,y=.49,z=0)
        self.assertFalse(thumbs_up(lm,[False]*4))

    @patch('engine.pyautogui')
    def test_cycle_sync_and_resume_after_release(self, mouse):
        worker=GestureEngine(OPTIONS)
        worker.running=True
        thumb=self.thumb()
        worker.process_mode_gesture(None,thumb,0)
        worker.process_mode_gesture(None,thumb,1.3)
        self.assertEqual(worker.control_mode.get(),'Volume')
        self.assertFalse(worker.running)
        worker.process_mode_gesture(None,thumb,4)
        self.assertEqual(worker.control_mode.get(),'Volume')
        worker.process_mode_gesture(None,None,5)
        worker.process_mode_gesture(None,None,5.3)
        self.assertTrue(worker.running)
        worker.process_mode_gesture(None,thumb,6)
        worker.process_mode_gesture(None,thumb,7.3)
        self.assertEqual(worker.control_mode.get(),'Air keyboard')
        worker.configure(OPTIONS)
        self.assertEqual(worker.control_mode.get(),'Air keyboard')
        worker.process_mode_gesture(None,None,8)
        worker.process_mode_gesture(None,None,8.3)
        worker.process_mode_gesture(None,thumb,9)
        worker.process_mode_gesture(None,thumb,10.3)
        self.assertEqual(worker.control_mode.get(),'Mouse')

    @patch('engine.pyautogui')
    def test_paused_stays_paused_and_one_hand_works(self, mouse):
        worker=GestureEngine(dict(OPTIONS,two_hands=False))
        worker.process_mode_gesture(self.thumb(),None,0)
        worker.process_mode_gesture(self.thumb(),None,1.3)
        self.assertEqual(worker.control_mode.get(),'Volume')
        worker.process_mode_gesture(None,None,2)
        worker.process_mode_gesture(None,None,2.3)
        self.assertFalse(worker.running)

    @patch('engine.pyautogui')
    def test_manual_mode_selection_cancels_pending_resume(self, mouse):
        worker=GestureEngine(OPTIONS)
        worker.running=True
        worker.process_mode_gesture(None,self.thumb(),0)
        worker.process_mode_gesture(None,self.thumb(),1.3)
        worker.select_mode('Air keyboard')
        worker.process_mode_gesture(None,None,3)
        self.assertFalse(worker.running)
        self.assertFalse(worker.resume_after_gesture)

if __name__=='__main__':
    unittest.main()
