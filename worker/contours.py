import os
import sys
import logging
import logging.config
import yaml
from argparse import ArgumentParser
import re

import xml.etree.ElementTree as ET

import common
import srtm


def osm_read(filename):
    log = logging.getLogger(__name__)
    log.info("Reading OSM file from " + filename)
    filename = os.path.abspath(filename)
    with open(filename, "r") as f:
        osm_string = f.read()
    # Strip the default namespace so we don't prefix every tag with ns0
    re.sub(r'\sxmlns="[^"]+"', '', osm_string, count=1)
    return ET.fromstring(osm_string)


def osm_write(root, filename):
    log = logging.getLogger(__name__)
    log.info("Writing OSM file with contours to " + filename)
    tree = ET.ElementTree(root)
    with open(filename, "wb") as f:
        tree.write(f, encoding="UTF-8", xml_declaration=True)


def add_contours(config, interval, minlat, minlon, maxlat, maxlon, osm):
    # Build the contours from the SRTM data
    contours = srtm.contour(config, interval, minlat, minlon, maxlat, maxlon)

    # Remove the bounds tag so we can iterate through all others
    bounds = contours.find("./bounds")
    contours.remove(bounds)

    # Loop over the rest of the data adding contours to osm file
    for child in contours:
        osm.append(child)

    return osm


def main():
    # Set up command line interface
    parser = ArgumentParser()
    parser.add_argument(
            "osmfile",
            help="The OSM filename to which you want to add contours"
            )
    parser.add_argument(
            "outfile",
            nargs='?',
            help="The OSM filename to which you want to add contours"
            )
    parser.add_argument(
            "--interval", 
            dest="interval",
            type=int,
            default=10,
            help="The distance between contours in meters, defaults to 10"
            )
    parser.add_argument(
            "--config", 
            dest="configfile",
            default="conf/srtm.yaml",
            help="Config file to use. Defaults to ./conf/srtm.yaml"
            )

    # Parse the command line
    args = parser.parse_args()

    # Get the full filenames
    osmfile = os.path.abspath(args.osmfile)
    configfile = os.path.abspath(args.configfile)
    if not args.outfile:
        outfile = osmfile
    else:
        outfile = os.path.abspath(args.outfile)

    common.setup_logging()
    log = logging.getLogger(__name__)

    # Load the SRTM transformation config file
    config = common.load_config(configfile)

    # Load the credentials for USGS height data (SRTM)
    creds = common.load_config("./conf/credentials.yaml")
    config["creds"] = creds

    # Read the OSM file
    osm = osm_read(osmfile)

    # Get the bounds of the file
    bounds = osm.find("./bounds")
    minlat = float(bounds.attrib["minlat"])
    minlon = float(bounds.attrib["minlon"])
    maxlat = float(bounds.attrib["maxlat"])
    maxlon = float(bounds.attrib["maxlon"])
    log.info("Read bonds from OSM file: {} {} {} {}".format(minlat, minlon,
        maxlat, maxlon))

    # Add contours to the OSM file
    add_contours(config, args.interval, minlat, minlon, maxlat, maxlon, osm)

    # Write out the osm file
    osm_write(osm, outfile)

if __name__ == "__main__":
    main()
