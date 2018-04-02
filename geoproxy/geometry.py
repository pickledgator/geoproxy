#!/usr/bin/env python

"""Collection of geometric support classes
"""


class Coordinate:
    """Container class for a geometric waypoint

    A single coordinate is comprised of a single lattitude, longitude and elevation
    measurements.

    Attributes:
        latitude (float): Value representing the latitude of the coordinate
        longitude (float): Value representing the longitude of the coordinate
        elevation (float): Value representing the elevation of the coordinate

    """

    def __init__(self, lat, lon, elev=0.0):
        """Constructor for a coordinate

        Args:
            lat (float): Float value representing the latitude of the coordinate
            lon (float): Float value representing the latitude of the coordinate
            elev (float): Float value representing the latitude of the coordinate

        """
        self.latitude = float(lat)
        self.longitude = float(lon)
        self.elevation = float(elev)

    def __eq__(self, b):
        """Equal operator for comparing coordinates

        Args:
            b (Coordinate): Object to compare against

        Returns:
            bool: If self object and parameter object are equal

        """
        return self.latitude == b.latitude \
            and self.longitude == b.longitude \
            and self.elevation == b.elevation

    def __str__(self):
        """String representation of a coordinate

        Returns:
            string: Human readable representation of the class

        """
        return "Lat: {}, Long: {}, Elev: {}".format(self.latitude, self.longitude, self.elevation)


class BoundingBox:
    """Container class for a box containing four coordinates as corners

    Attributes:
        top_left (Coordinate): Corner coordinate of the box
        top_right (Coordinate): Corner coordinate of the box
        bottom_left (Coordinate): Corner coordinate of the box
        bottom_right (Coordinate): Corner coordinate of the box

    """
    def __init__(self):
        self.top_left = None
        self.top_right = None
        self.bottom_left = None
        self.bottom_right = None

    def set_bl_tr(self, bl, tr):
        """Set the corners of the box based on the bottom left and top right coordinates

        This set function is used by the google geocoder. The other two coordinates of the
        bounding box will be set automatically.

        Args:
            bl (Coordinate): Bottom left corner coordinate of the box
            tr (Coordinate): Top right corner coordinate of the box

        """
        self.bottom_left = bl
        self.top_right = tr
        self.top_left = Coordinate(tr.latitude, bl.longitude)
        self.bottom_right = Coordinate(bl.latitude, tr.longitude)

    def set_tl_br(self, tl, br):
        """Set the corners of the box based on the top left and bottom right coordinates

        This set function is used by the here geocoder. The other two coordinates of the
        bounding box will be set automatically.

        Args:
            tl (Coordinate): Top left corner coordinate of the box
            br (Coordinate): Bottom right corner coordinate of the box

        """
        self.top_left = tl
        self.bottom_right = br
        self.top_right = Coordinate(tl.latitude, br.longitude)
        self.bottom_left = Coordinate(br.latitude, tl.longitude)

    def __str__(self):
        """String representation of a Bounding Box

        Returns:
            string: Human readable representation of the class

        """
        return "Bounding Box:\n TL: {}\n TR: {}\n BL: {}\n BR: {}".format(
            self.top_left, self.top_right, self.bottom_left, self.bottom_right)
