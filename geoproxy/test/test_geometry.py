#!/usr/bin/env python

from geoproxy.geometry import Coordinate
from geoproxy.geometry import BoundingBox
import unittest


class TestGeometry(unittest.TestCase):
    def test_coordinate(self):
        coord = Coordinate(1.0, 2.0)
        self.assertEqual(coord.latitude, 1.0)
        self.assertEqual(coord.longitude, 2.0)
        self.assertEqual(coord.elevation, 0.0)
        self.assertEqual(str(coord), "Lat: 1.0, Long: 2.0, Elev: 0.0")

    def test_coordinate_str(self):
        coord = Coordinate("1.0", "2.0", "0.0")
        self.assertEqual(coord.latitude, 1.0)
        self.assertEqual(coord.longitude, 2.0)
        self.assertEqual(coord.elevation, 0.0)

    def test_bounding_box(self):
        coord1 = Coordinate("0.0", "0.0")
        coord2 = Coordinate("1.0", "1.0")
        bb = BoundingBox()
        self.assertIsNone(bb.top_left)
        self.assertIsNone(bb.top_right)
        bb.set_tl_br(coord1, coord2)
        self.assertEqual(bb.top_left, coord1)
        self.assertEqual(bb.bottom_right, coord2)
        self.assertEqual(bb.top_right, Coordinate(coord1.latitude, coord2.longitude))
        self.assertEqual(bb.bottom_left, Coordinate(coord2.latitude, coord1.longitude))
        bb.set_bl_tr(Coordinate(coord2.latitude, coord1.longitude),
                     Coordinate(coord1.latitude, coord2.longitude))
        self.assertEqual(bb.top_left, coord1)
        self.assertEqual(bb.bottom_right, coord2)


if __name__ == '__main__':
    unittest.main()
