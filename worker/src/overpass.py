import os
import sys
import re
import logging
import logging.config
import yaml
from argparse import ArgumentParser
import requests
from requests.compat import urljoin
import xml.etree.ElementTree as ET

import common


def ovp_query(config, bbox):
    log = logging.getLogger(__name__)
    ways = []
    relations = []
    for name in config["layers"]:
        log.info("Generating overpass query for layer: " + name)

        for shape in ["ways", "areas", "complex"]:
            if shape in config["layers"][name]:
                log.info("Processing " + shape)
                for source in config["layers"][name][shape]:
                    log.info("Using source " + source)
                    if shape == "complex":
                        relations.append("rel[{}]{}".format(config["layers"][name][shape][source], bbox))
                    else:
                        ways.append("way[{}]{}".format(config["layers"][name][shape][source], bbox))

    q = "("
    if len(ways) > 0:   
        q += ";".join(ways) + ";"
    if len(relations) > 0:
        q += ";".join(relations) + ";"
    q += ");(._;>;);out;"
    log.debug("Overpass QL: " + q)
    return q


def ovp_download(endpoint, query):
    r = requests.post(endpoint, data=query)
    return r.content

def get_osm(min_lat, min_lon, max_lat, max_lon, config):
    log = logging.getLogger(__name__)
    log.info("Creating contours for B: {} L: {} T: {} R: {}".format(
        min_lat, min_lon, max_lat, max_lon))

    # Create the overpass query from the config file
    bbox = (min_lat, min_lon, max_lat, max_lon)
    query = ovp_query(config, bbox)
    log.info("Query: " + query)

    # Get the data using the overpass API
    log.info("Downloading data from " + config["overpass"]["endpoint"])
    data = ovp_download(config["overpass"]["endpoint"], query)

    # Parse XML so we can add the "bounds" element
    log.info("Parsing XML")
    root = ET.fromstring(data)
    attrib = {"minlat": str(min_lat), "minlon": str(min_lon),
              "maxlat": str(max_lat), "maxlon": str(max_lon)}
    ET.SubElement(root, "bounds", attrib)
    return root

def main ():
    # Configure logging
    common.setup_logging()
    log = logging.getLogger(__name__)
    log.info("Overpass - Starting")

    # Set up command line interface
    parser = ArgumentParser()
    parser.add_argument(
            "outputfile",
            help="The output filename."
            )
    parser.add_argument(
            "--config", 
            dest="configfile",
            default="conf/all.yaml",
            help="Config file to use. Defaults to ./conf/all.yaml"
            )
    parser.add_argument(
            "min_lat",
            type=float,
            help="Minimum latitude"
            )
    parser.add_argument(
            "min_lon",
            type=float,
            help="Minimum longitude"
            )
    parser.add_argument(
            "max_lat",
            type=float,
            help="Maximum latitude"
            )
    parser.add_argument(
            "max_lon",
            type=float,
            help="Maximum longitude"
            )

    # Parse the command line
    args = parser.parse_args()

    # Get the full filenames
    if args.outputfile:
        outfile = os.path.abspath(args.outputfile)
    else:
        log.error("No output filename provided")

    configfile = os.path.abspath(args.configfile)

    # Load the config
    config = common.load_config(configfile)

    root = get_osm(args.min_lat, args.min_lon, args.max_lat, args.max_lon, config)

    # Write out the file
    tree = ET.ElementTree(root)
    with open(outfile, "wb") as f:
        tree.write(f, encoding="UTF-8", xml_declaration=True)
                
    # And we are done!
    log.info("Processing completed")


if __name__ == "__main__":
    main()