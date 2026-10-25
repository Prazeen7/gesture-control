import unittest
from motion import ScrollMotion

class ClickAndSpeedTests(unittest.TestCase):
    def test_scroll_above_ten_keeps_increasing(self):
        totals=[]
        for speed in (10, 20, 100):
            motion=ScrollMotion()
            motion.update(.5,.015,speed,0)
            total=sum(motion.update(.45,.015,speed,i/30) for i in range(1,31))
            totals.append(total+motion.remainder)
        self.assertAlmostEqual(totals[1], totals[0]*2)
        self.assertAlmostEqual(totals[2], totals[0]*10)

if __name__ == '__main__':
    unittest.main()
