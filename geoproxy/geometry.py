#!/usr/bin/env python


class Coordinate:
    def __init__(self, lat, lon, elev=0.0):
        self.latitude = float(lat)
        self.longitude = float(lon)
        self.elevation = float(elev)

    def __eq__(self, b):
        return self.latitude == b.latitude \
            and self.longitude == b.longitude \
            and self.elevation == b.elevation

    def __str__(self):
        return "Lat: {}, Long: {}, Elev: {}".format(self.latitude, self.longitude, self.elevation)


class BoundingBox:
    def __init__(self):
        self.top_left = None
        self.top_right = None
        self.bottom_left = None
        self.bottom_right = None

    def set_bl_tr(self, bl, tr):
        # google format
        self.bottom_left = bl
        self.top_right = tr
        self.top_left = Coordinate(tr.latitude, bl.longitude)
        self.bottom_right = Coordinate(bl.latitude, tr.longitude)

    def set_tl_br(self, tl, br):
        # here format
        self.top_left = tl
        self.bottom_right = br
        self.top_right = Coordinate(tl.latitude, br.longitude)
        self.bottom_left = Coordinate(br.latitude, tl.longitude)

    def __str__(self):
        return "Bounding Box:\n TL: {}\n TR: {}\n BL: {}\n BR: {}".format(
            self.top_left, self.top_right, self.bottom_left, self.bottom_right)
