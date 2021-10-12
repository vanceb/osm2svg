import logging
import logging.config
import xml.etree.ElementTree as ET
from pyproj import CRS, Transformer

import osm

# Class representing a generic 2D point
# Used for representing the locations in a Cartesian coordinate system
class Point(object):

    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y


class Layer(object):

    def __init__(self, name):
        self.name = name
        self.attrib = {}
        self.paths = []


class SVG(object):


    def __init__(self, bounds, epsg=3857):
        self.__projection = Projection(epsg=epsg)
        self.geo_bounds = bounds
        self.__height = None
        self.__width = None
        self.__scale = None
        self.__inkscape = True
        self.layers = {}

    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, height):
        log = logging.getLogger(__name__)
        if type(height) is str:
            height = float(height)
        self.__height = height
        if self.__geo_bounds is not None:
            self.__scale = 1000 * (self.__geo_bounds["n"] - self.__geo_bounds["s"]) / self.__height 
            self.__width = 1000 * (self.__geo_bounds["e"] - self.__geo_bounds["w"]) / self.__scale
            log.info("Rescaled from height... Scale: 1:{:0.0f}, Width: {:0.0f}mm, Height: {:0.0f}mm".format(
                self.scale, self.width, self.height))
        else:
            raise ValueError("You need to set the geo_bounds before the height")

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        log = logging.getLogger(__name__)
        if type(width) is str:
            width = float(width)
        self.__width = width
        if self.__geo_bounds is not None:
            self.__scale = 1000 * (self.__geo_bounds["e"] - self.__geo_bounds["w"]) / self.__width
            self.__height = 1000 * (self.__geo_bounds["n"] - self.__geo_bounds["s"]) / self.__scale
            log.info("Rescaled from width... Scale: 1:{:0.0f}, Width: {:0.0f}mm, Height: {:0.0f}mm".format (
                self.scale, self.width, self.height))
        else:
            raise ValueError("You need to set the geo_bounds before the width")


    @property
    def scale(self):
        return self.__scale

    @scale.setter
    def scale(self, scale):
        log = logging.getLogger(__name__)
        if type(scale) is str:
            scale = float(scale)
        self.__scale = scale
        if self.__geo_bounds is not None:
            self.__width = 1000 * (self.__geo_bounds["e"] - self.__geo_bounds["w"]) / self.__scale
            self.__height = 1000 * (self.__geo_bounds["n"] - self.__geo_bounds["s"]) / self.__scale
            log.info("Rescaled... Scale: 1:{:0.0f}, Width: {:0.0f}mm, Height: {:0.0f}mm".format(
                self.scale, self.width, self.height))
        else:
            raise ValueError("You need to set the geo_bounds before the scale")


    @property
    def inkscape(self):
        return self.__inkscape

    @inkscape.setter
    def inkscape(self, tf):
        if type(tf) == bool:
            self.__inkscape = tf
        else:
            raise ValueError

    @property
    def geo_bounds(self):
        return self.__geo_bounds

    @geo_bounds.setter
    def geo_bounds(self, bounds):
        log = logging.getLogger(__name__)
        if type(bounds) == dict and \
                "minlat" in bounds and \
                "minlon" in bounds and \
                "maxlat" in bounds and \
                "maxlon" in bounds:
            self.__geo_bounds = bounds
            # Calculate northings and eastings in meters
            nd = osm.Node(lat=self.__geo_bounds["minlat"], lon=self.__geo_bounds["minlon"])
            p = self.__projection.transform(nd)
            self.__geo_bounds["s"] = p.y
            self.__geo_bounds["w"] = p.x
            nd = osm.Node(lat=self.__geo_bounds["maxlat"], lon=self.__geo_bounds["maxlon"])
            p = self.__projection.transform(nd)
            self.__geo_bounds["n"] = p.y
            self.__geo_bounds["e"] = p.x
            log.info("Geographic bounds: {}".format(str(self.geo_bounds)))
        else:
            raise ValueError


    def get_svg(self):
        log = logging.getLogger(__name__)
        if self.geo_bounds is None or self.scale is None:
            log.warning("Insufficient configuration to allow creation of the svg")
            return None
        else:
            # Generate the svg document properties
            dp = {"xmlns": "http://www.w3.org/2000/svg",
                "version": "1.1",
                "baseProfile": "full",
                "height": str(self.height) + "mm",
                "width": str(self.width) + "mm",
                "viewBox": "0 0 {} {}".format(self.width, self.height)
                }
            # Add inkscape xmlns if needed
            if self.inkscape:
                dp["xmlns:inkscape"] = "http://www.inkscape.org/namespaces/inkscape"

            # Create the root node
            svg = ET.Element('svg', dp)

            for layer in self.layers:
                l = self.layers[layer]
                log.info("Compiling layer: " + l.name)
                # Add a group to contain all of the layer data
                dp = dict(l.attrib)
                dp["id"] = l.name
                # Inkscape attributes for the layer
                if self.inkscape:
                    dp["inkscape:label"] = l.name
                    dp["inkscape:groupmode"] = "layer"
                g = ET.SubElement(svg, 'g', dp)

                for path in l.paths:
                    if type(path) is dict and "inner" in path and "outer" in path:
                        # This is a complex way
                        d = self.__complex(path)
                    elif type(path) is list:
                        # This is a way or area
                        d = self.__way(path)
                    else:
                        raise ValueError

                    # Add path to layer
                    fmt = {}
                    if "fill" in l.attrib:
                        fmt["fill"] = str(l.attrib["fill"])
                    else:
                        fmt["fill"] = "none"
                    if "stroke" in l.attrib:
                        fmt["stroke"] = str(l.attrib["stroke"])
                    else:
                        fmt["stroke"] = "none"
                    if "stroke-width" in l.attrib:
                        fmt["stroke-width"] = str(l.attrib["stroke-width"])                        

                    fmt["d"] = d
                    ET.SubElement(g, "path", fmt)
            return svg


    # https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order/1180256#1180256
    def __is_cw(self, path):
        min_x = float(path[0].lon)
        min_indices = [0]
        for i, point in enumerate(path):
            if float(point.lon) < min_x:
                min_x = float(point.lon)
                min_indices = [i]
            elif float(point.lon) == min_x:
                min_indices.append(i)

        min_point_index = min_indices[0]

        # In case we have more than one leftmost point
        if len(min_indices) > 1:
            # Look for min_y
            min_y = float(path[min_indices[0]].lat)
            for i, index in enumerate(min_indices):
                if float(path[index].lat) < min_y:
                    min_point_index = min_indices[i]

        a = path[(min_point_index + 1) % len(path)]
        b = path[min_point_index]
        c = path[(min_point_index - 1) % len(path)]
        v = (
                float(b.lon) * float(c.lat) + 
                float(a.lon) * float(b.lat) + 
                float(a.lat) * float(c.lon)
            ) - (
                float(a.lat) * float(b.lon) + 
                float(b.lat) * float(c.lon) + 
                float(a.lon) * float(c.lat)
            )
        if v > 0:
            return True
        else:
            return False


    def __complex(self, cx):
        log = logging.getLogger(__name__) 
        if "inner" not in cx or "outer" not in cx:
            log.error("Called __complex without 'inner' or 'outer' in the data")
            raise ValueError("Called __complex without 'inner' or 'outer' in the data")

        path = []
        # Below is rendering of complex relations
        for pth in cx["outer"]:
            # Check the direction of the polygon
            if self.__is_cw(pth):
                pth = list(reversed(pth))
            path.append(self.__way(pth))

        for pth in cx["inner"]:
            if len(pth) > 1:
                # Check the direction of the polygon
                if not self.__is_cw(pth):
                    pth = list(reversed(pth))
                path.append(self.__way(pth))

        return " ".join(path)


    def __way(self, wy):
        path = []
        if wy is not None and len(wy) > 0:
            # Deal with the first point
            p = self.__node(wy[0])
            # Move to start point
            path.append("M {:0.2f} {:0.2f}".format(p.x, p.y))
            if len(wy) > 1:
                # Do the rest of the points
                for nd in wy[1:]:
                    # Transfrom and scale
                    p = self.__node(nd)
                    # Line to next point
                    path.append("L {:0.2f} {:0.2f}".format(p.x, p.y))
        if wy[0].id == wy[-1].id:
            path.append("Z")
        return " ".join(path)


    def __node(self, nd):
        left = self.geo_bounds["w"]
        top = self.geo_bounds["n"]
        # Transfrom and scale
        if type(nd) is osm.Node:
            p = self.__projection.transform(nd)
            p.x = (p.x - left) * 1000 / self.scale
            p.y = - (p.y - top) * 1000 / self.scale
            return p
        else:
            return Point()



# Class used to convert between geo-referenced locations
# (Nodes and Ways) and cartesian coordinates (Points)
class Projection (object):


    def __init__(self, epsg=3857):
        # EPSG 3857 - Pseudo-Mercator projection
        #             giving Northings and Eastings in meters
        # EPSG 27700 - OSGB Ordnance Survey - Good for UK
        self.__to_crs = CRS.from_epsg(epsg)
        self.__from_crs = self.__to_crs.geodetic_crs
        self.__t = Transformer.from_crs(self.__from_crs, self.__to_crs)

    # Internal workhorse function for the transformation
    def __tf(self, lat, lon):
        # Project
        #y, x = self.__t.transform(lon, lat)
        x, y = self.__t.transform(lat, lon)
        return Point(x, y)

    # Transform a location into a Point
    def transform(self, n):
        if type(n) == osm.Node:
            return self.__tf(n.lat, n.lon)
        elif type(n) is list or type(n) is tuple and len(n) == 2:
            return self.__tf(n[0], n[1])
        elif type(n) is dict and "lat" in n and "lon" in n:
            return self.__tf(n["lat"], n["lon"])
        else:
            raise ValueError

    # Transform a Way or other sensible list type into a list of Points
    def transform_way(self, way):
        points = []
        if type(way) is list:
            if len(way) > 0:
                for p in way:
                    points.append(self.transform(p))
        else:
            raise ValueError

        return points

