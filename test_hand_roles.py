import unittest
from types import SimpleNamespace as NS
from motion import hand_roles

class HandRoleTests(unittest.TestCase):
    def labels(self, *names):
        return [NS(classification=[NS(label=name)]) for name in names]

    def test_detection_order_does_not_swap_roles(self):
        right, left = object(), object()
        self.assertEqual(hand_roles([left, right], self.labels('Left','Right'), True), (right,left))
        self.assertEqual(hand_roles([right, left], self.labels('Right','Left'), True), (right,left))

    def test_left_only_never_moves_cursor(self):
        left = object()
        self.assertEqual(hand_roles([left], self.labels('Left'), True), (None,left))

    def test_right_only_can_move_without_actions(self):
        right = object()
        self.assertEqual(hand_roles([right], self.labels('Right'), True), (right,None))

    def test_one_hand_accepts_either_hand(self):
        left = object()
        self.assertEqual(hand_roles([left], self.labels('Left'), False), (left,None))
        self.assertEqual(hand_roles([], [], True), (None,None))

if __name__ == '__main__':
    unittest.main()
