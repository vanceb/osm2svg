import os
import sys
import logging
import logging.config
import math
import re
import yaml
from argparse import ArgumentParser
import xml.etree.ElementTree as ET


from common import setup_logging


# Reads the svg file stripping the default namespace
# to make searching easier...
# Add it back during the write
def svg_read(filename):
    log = logging.getLogger(__name__)
    fullpath = os.path.abspath(filename)

    if os.path.exists(fullpath):
        # Parse the file
        log.info("Reading svg file: " + fullpath)
        with open(fullpath) as f:
            xmlstring = f.read()

        # Remove the default namespace definition
        xmlstring = re.sub('\\sxmlns="[^"]+"', '', xmlstring, count=1)
        root = ET.fromstring(xmlstring)
        return root
    else:
        log.error("the svg file does not exist: " + fullpath)
        sys.exit()


# Write out the xml data and add back the default xmlns
def svg_write(root, filename, pretty=True):
    log = logging.getLogger(__name__)
    # Add back the default namespace
    root.attrib["xmlns"] = "http://www.w3.org/2000/svg"
    log.info("Writing svg file to " + filename)
    if pretty:
        root = indent(root)
    tree = ET.ElementTree(root)
    with open(filename, "wb") as f:
        tree.write(f, encoding="UTF-8", xml_declaration=True)


# Indent function for pretty printing
def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem      

def get_bounds(svg):
    log = logging.getLogger(__name__)
    vb = svg.attrib["viewBox"]
    l, t, w, h = vb.split(" ")
    log.info("Bounds: {} {} {} {}".format(l, t, w, h))
    return (float(l), float(t), float(w), float(h))

def new_svg(l, t, w, h):
    svg = ET.Element("svg")
    set_bounds(svg, l, t, w, h)
    return svg

def set_bounds(svg, l, t, w, h):
    svg.attrib["viewBox"] = " ".join((\
                            str(round(l, 2)), 
                            str(round(t, 2)), 
                            str(round(w, 2)),
                            str(round(h, 2))))
    svg.attrib["width"] = str(round(w, 2)) + "mm"
    svg.attrib["height"] = str(round(h, 2)) + "mm"


def add_to_path(d, cmnd, x, y):
    d.append(cmnd)
    d.append(str(round(x, 2)))
    d.append(str(round(y, 2)))
    return d


def svg_clip(svg, left=None, top=None, width=None, height=None, decimal_places=1, pretty=True):
    log = logging.getLogger(__name__)
    l, t, w, h = get_bounds(svg)
    # Calculate the Union of the rectangles
    if left is None:
        left = l
    if top is None:
        top = t
    if width is None:
        width = w
    if height is None:
        height = h
    if l + w > left + width:
        w = left + width - l
    if t + h > top + height:
        h = top + height - t
    if l < left:
        w = w - (left - l)
        l = left
    if t < top:
        h = h - (top - t)
        t = top

    # Round values
    t = round(t, decimal_places)
    l = round(l, decimal_places)
    w = round(w, decimal_places)
    h = round(h, decimal_places)

    log.info("Clipping to: l: {}, t: {}, w: {}, h: {}".format(l, t, w, h))
    set_bounds(svg, l,t,w,h)

    # Get all the paths
    paths = svg.findall(".//path")
    log.info("Found {} paths".format(len(paths)))
    for path in paths:
        d = str(path.attrib["d"])
        parts = d.split()

        # Prepare for the start of a path
        d2 = []  
        i = 0
        x = None
        y = None
        prev_x = None
        prev_y = None
        bounds = None
        prev_bounds = None
        path_valid = False

        # Skip over anything at the start that isn't a move command
        try:
            while parts[i] not in "Mm":
                log.error("Path doesn't start with a move: " + str(parts[i]))
                i += 1
        except IndexError:
            log.error("Index out of range when looking for a valid start of the path")

        # Loop over the path instructions
        while i < len(parts):

            # Skip to the next command
            while parts[i] not in "MLZCmlzc":
                log.error("Unexpected data skipping: " + str(parts[i]))
                i += 1

            if parts[i] in "LMlm":
                # We expect an x and y position to follow
                prev_x = x
                prev_y = y
                try:
                    x = round(float(parts[i+1]), decimal_places)
                    y = round(float(parts[i+2]), decimal_places)
                except ValueError:
                    log.error("Unable to convert to float: {} {}".format(parts[i+1], parts[i+2]))
                    continue
                except IndexError:
                    log.error("Reached end of the path, expected x,y value")
                    break

                # Have we move a sufficient distance?
                if prev_x is not None and prev_y is not None and \
                    (x == prev_x and y == prev_y):
                    # We have not moved far enough away so drop the point
                    log.debug("Point to close to last, dropping last: ({},{})  ({},{})".format(x, y, prev_x, prev_y))
                else:
                    # Are we within bounds?
                    bounds = x <= l + w and x >= l and y <= t + h and y >= t
                    if prev_x is not None and prev_y is not None:
                        prev_bounds = prev_x <= l + w and prev_x >= l and prev_y <= t + h and prev_y >= t
                    else:
                        prev_bounds = None

                    # We have more than one point so we could have crossed bounds
                    if bounds != prev_bounds and prev_bounds is not None:
                        # Work out boundary crossing points
                        if x == prev_x and y == prev_y:
                            # Repeat of the same location
                            bx = None
                            tx = None
                            ly = None
                            ry = None

                        elif x == prev_x:
                            # Vertical line that cuts top or bottom
                            # Avoid divide by 0 condition
                            bx = x
                            tx = x
                            ly = None
                            ry = None

                        elif y == prev_y:
                            # Horizontal crossing cutting left or right
                            # Avoid m = 0 which gives divide by zero later
                            ry = y
                            ly = y
                            bx = None
                            tx = None

                        else:
                            # General case
                            # Equation of a straight line y = mx + c
                            m = (y - prev_y) / (x - prev_x)
                            c = y - m * x
                            # Top (y = t)
                            tx = (t - c) / m
                            # Bottom (y = t + h)
                            bx = (t + h - c) / m
                            # Left (x = l)
                            ly = l * m + c
                            # Right (x = l + w)
                            ry = (l + w) * m + c
                    else:
                        # We can't have crossed bounds
                        tx = None
                        bx = None
                        ly = None
                        ry = None

                    # Check to see whether the crossing points are within bounds
                    if tx is not None and (tx < l or tx > l + w):
                        tx = None
                    if bx is not None and (bx < l or bx > l + w):
                        bx = None
                    if ly is not None and (ly < t or ly > t + h):
                        ly = None
                    if ry is not None and (ry < t or ry > t + h):
                        ry = None

                    # Sanity check, count the valid crossing points
                    count = 0

                    if not path_valid:
                        # Deal with the starting of a path
                        if bounds:
                            # This is our first valid point
                            path_valid = True
                            if prev_x is not None and prev_y is not None:
                                # We are be coming in from out of bounds
                                # Crossing the top?
                                if prev_y < t and y >= t and tx is not None:
                                    count += 1
                                    d2 = add_to_path(d2, "M", tx - l, 0)
                                # Crossing the bottom?
                                if prev_y > t + h and y <= t + h and bx is not None:
                                    count += 1
                                    d2 = add_to_path(d2, "M", bx - l, h)
                                # Crossing the left
                                if prev_x < l and x >= l and ly is not None:
                                    count += 1
                                    d2 = add_to_path(d2, "M", 0, ly - t)
                                # Crossing the right
                                if prev_x > l + w and x <= l + w and ry is not None:
                                    count += 1
                                    d2 = add_to_path(d2, "M", w, ry - t)
                                # Add the current point
                                d2 = add_to_path(d2, "L", x - l, y - t)
                            else:
                                # The very first point is in bounds
                                count += 1
                                d2 = add_to_path(d2, "M", x - l, y - t)
                        else:
                            log.debug("Starting point(s) outside bounds, dropping: {} {}".format(x,y))

                    else:
                        # We already have at least one valid point in our path
                        if bounds is True and prev_bounds is False:
                            # We have entered the viewbox from outside
                            # Crossing the top?
                            if prev_y < t and y >= t and tx is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], tx - l, 0)
                            # Crossing the bottom?
                            if prev_y > t + h and y <= t + h and bx is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], bx - l, h)
                            # Crossing the left
                            if prev_x < l and x >= l and ly is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], 0, ly - t)
                            # Crossing the right
                            if prev_x > l + w and x <= l + w and ry is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], w, ry - t)
                            d2 = add_to_path(d2, "L", x - l, y - t)

                        elif bounds is False and prev_bounds is True:
                            # We have left the viewbox
                            if prev_y >= t and y < t and tx is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], tx - l, 0)
                            if prev_y <= t + h and y > t + h and bx is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], bx - l, h)
                            if prev_x >= l and x < l and ly is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], 0, ly - t)
                            if prev_x <= l + w and x > l + w and ry is not None:
                                count += 1
                                d2 = add_to_path(d2, parts[i], w, ry - t)
                        elif bounds is True and prev_bounds is True:
                            # We have stayed inside bounds
                            count += 1
                            d2 = add_to_path(d2, parts[i], x - l, y - t)
                        elif bounds is False and prev_bounds is False:
                            # We have stayed outside bounds
                            count += 1
                            log.debug("Dropping point outside bounds: {}, {}".format(x, y))
                        else:
                            log.error("This should be impossible!")

                        # Sanity check
                        if count == 0:
                            log.warning("We should have crossed bounds, but we can't find the crossing point {} {} {} {}".format(prev_x, prev_y, x, y))
                        elif count == 2:
                            log.debug("Possible diagonal corner crossing?")
                        elif count > 2:
                            log.error("We appear to have crossed 3 or more boundaries - impossible!")
                        else:
                            log.debug("{} crossing points". format(count))
                        log.debug("tx: {} bx: {} ly: {} ry: {}".format (tx,bx,ly,ry))

                i += 3

            elif parts[i] in "Zz":
                if path_valid:
                    d2.append("Z")
                    log.debug("Closing path")
                i += 1
            elif parts[i] in "Cc":
                endcmd = i + 6
                if endcmd <= len(parts):
                    while i <= endcmd:
                        d2.append(parts[i])
                        i += 1
                else:
                    log.error("Insufficient elements to complete an arc")
                    i += 1

            else:
                log.error("Unexpected command in path: " + parts[i])
                i += 1

        if path_valid:
            log.debug("Adding path: {}".format(d2))
            path.attrib["d"] = " ".join(d2)
        else:
            log.debug("Dropping empty path {}".format(d2))
    if pretty:
        svg = indent(svg)
    return svg
                

def main():
    setup_logging()

    parser = ArgumentParser()
    parser.add_argument(
            "svgfile",
            help="The svg file to be cropped"
            )
    parser.add_argument(
            "outputfile",
            nargs='?',
            help="If not supplied it will write back to the same file"
            )
    parser.add_argument(
            "--left",
            dest="left",
            type=float,
            help="Left coordinate of the bounding box"
            )
    parser.add_argument(
            "--top",
            dest="top",
            type=float,
            help="Top coordinate of the bounding box"
            )
    parser.add_argument(
            "--width",
            dest="width",
            type=float,
            help= "Width of the bounding box"
            )
    parser.add_argument(
            "--height",
            dest="height",
            type=float,
            help="Height of the bounding box"
            )
        
    # Parse the command line
    args = parser.parse_args()

    # Get the full filenames
    svgfile = os.path.abspath(args.svgfile)

    if args.outputfile:
        outputfile = os.path.abspath(args.outputfile)
    else:
        outputfile = svgfile

    # Read in the file
    svg = svg_read(svgfile)

    # Clip the svg
    new_svg = svg_clip(svg, args.left, args.top, args.width, args.height)

    # Write out the svg file
    svg_write(new_svg, outputfile)

if __name__ == "__main__":
    main()
