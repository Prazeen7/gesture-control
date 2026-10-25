import unittest
from motion import PalmScroll, palm_source

class PalmScrollTests(unittest.TestCase):
    def test_return_stroke_cannot_reverse_latched_scroll(self):
        scroll = PalmScroll()
        scroll.update('palm_latched', .5, 4, .015, 0)
        self.assertGreater(scroll.update('palm_latched', .45, 4, .015, .1), 0)
        self.assertGreater(scroll.update('palm_latched', .7, 4, .015, .2), 0)
        self.assertGreater(scroll.update('palm_latched', .7, 4, .015, .3), 0)
        scroll.mode = None  # Closing the palm ends this gesture.
        self.assertEqual(scroll.update('palm_latched', .5, 4, .015, .4), 0)
        self.assertLess(scroll.update('palm_latched', .55, 4, .015, .5), 0)

    def test_latched_scroll_waits_for_clear_direction(self):
        scroll = PalmScroll()
        scroll.update('palm_latched', .5, 4, .015, 0)
        self.assertEqual(scroll.update('palm_latched', .505, 4, .015, .1), 0)
        self.assertEqual(scroll.stroke_direction, 0)

    def test_either_palm_and_left_priority(self):
        self.assertEqual(palm_source(False, True), 'left')
        self.assertEqual(palm_source(True, False), 'right')
        self.assertEqual(palm_source(True, True), 'left')
        self.assertIsNone(palm_source(False, False))

    def test_switching_palms_reanchors_without_scroll_jump(self):
        scroll = PalmScroll()
        scroll.update('palm', .3, 4, .015, 0)
        scroll.update('palm', .25, 4, .015, .03)
        scroll.mode = None
        self.assertEqual(scroll.update('palm', .8, 4, .015, .06), 0)
        self.assertLess(scroll.update('palm', .85, 4, .015, .09), 0)

    def test_swipe_direction_and_stationary_stop(self):
        scroll = PalmScroll()
        scroll.update('palm', .5, 4, .015, 0)
        self.assertGreater(scroll.update('palm', .45, 4, .015, .03), 0)
        self.assertEqual(scroll.update('palm', .45, 4, .015, .06), 0)
        self.assertLess(scroll.update('palm', .55, 4, .015, .09), 0)

    def test_auto_continues_last_direction_without_motion(self):
        scroll = PalmScroll()
        scroll.update('palm', .5, 4, .015, 0)
        scroll.update('palm', .55, 4, .015, .03)
        scroll.update('auto', .55, 4, .015, .06)
        total = sum(scroll.update('auto', .55, 4, .015, .06+i/30) for i in range(1,31))
        self.assertLessEqual(total, -19)
        scroll.reset()
        self.assertEqual(scroll.update('auto', .5, 4, .015, 2, pointing_up=False), 0)
        self.assertLess(scroll.update('auto', .5, 4, .015, 2.1), 0)

    def test_new_gesture_does_not_jump(self):
        scroll = PalmScroll()
        scroll.update('palm', .5, 4, .015, 0)
        scroll.update('palm', .4, 4, .015, .03)
        scroll.mode = None
        self.assertEqual(scroll.update('palm', .9, 4, .015, 1), 0)

if __name__ == '__main__':
    unittest.main()
