import unittest
from motion import screen_target, follow, ScrollMotion

class MotionTests(unittest.TestCase):
    def test_vertical_edges_relative_to_comfortable_height(self):
        for center in (.3, .5, .7):
            self.assertAlmostEqual(screen_target(.5, center-.1, 1920, 1080, 1, .2, center)[1], 1)
            self.assertAlmostEqual(screen_target(.5, center+.1, 1920, 1080, 1, .2, center)[1], 1078)

    def test_lower_travel_reaches_edges_sooner(self):
        self.assertAlmostEqual(screen_target(.5, .55, 1920, 1080, 1, .1)[1], 1078)

    def test_hold_scroll_both_directions_and_stop(self):
        scroll = ScrollMotion()
        self.assertEqual(scroll.update(.5, .015, 2, 0), 0)
        total = sum(scroll.update(.45, .015, 2, i/30) for i in range(1, 31))
        self.assertGreater(total, 5)
        self.assertEqual(scroll.update(.5, .015, 2, 1.03), 0)
        self.assertLess(sum(scroll.update(.55, .015, 2, 1.03+i/30) for i in range(1, 31)), -5)
        scroll.reset()
        self.assertEqual(scroll.update(.9, .015, 2, 3), 0)

    def test_scroll_rate_independent_of_frame_rate(self):
        totals = []
        for fps in (15, 30, 60):
            scroll = ScrollMotion()
            scroll.update(.5, .015, 2, 0)
            totals.append(sum(scroll.update(.45, .015, 2, i/fps) for i in range(1, fps+1)) + scroll.remainder)
        self.assertAlmostEqual(min(totals), max(totals))

    def test_dead_zone_does_not_scroll(self):
        scroll = ScrollMotion()
        scroll.update(.5, .015, 2, 0)
        self.assertEqual(sum(scroll.update(.5+(-1)**i*.005, .015, 2, i/30) for i in range(1, 61)), 0)

    def test_follow_is_bounded_and_suppresses_jitter(self):
        self.assertEqual(follow((100, 100), (101, 100), .5, .03), (100, 100))
        x, y = follow((0, 0), (1000, 1000), .5, .03)
        self.assertTrue(0 < x < 1000 and 0 < y < 1000)

if __name__ == '__main__':
    unittest.main()
