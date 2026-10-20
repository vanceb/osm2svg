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
    log = logging.getLogger(__name__)
    headers = {
        'User-Agent': 'osm2svg/1.0 (github.com/vanceb/osm2svg)',
        'Accept': '*/*',
    }
    r = requests.post(endpoint, data=query, headers=headers, timeout=120)
    if r.status_code != 200:
        log.error("Overpass API returned HTTP %d: %s", r.status_code, r.text[:500])
        raise Exception(f"Overpass API error {r.status_code}: {r.text[:500]}")
    return r.content

def get_osm(min_lat, min_lon, max_lat, max_lon, config):
    log = logging.getLogger(__name__)
    log.info("Creating contours for B: {} L: {} T: {} R: {}".format(
        min_lat, min_lon, max_lat, max_lon))

    # Create the overpass query from the config file
    bbox = (min_lat, min_lon, max_lat, max_lon)
    query = ovp_query(config, bbox)
    log.info("Query: " + query)

    # Get the data using the overpass API with retry/fallback support
    endpoints = config.get("overpass", {}).get("endpoints", [config["overpass"]["endpoint"]])
    last_error = None
    data = None
    for i, endpoint in enumerate(endpoints):
        log.info("Downloading data from %s", endpoint)
        try:
            data = ovp_download(endpoint, query)
            log.info("Successfully fetched OSM data from %s", endpoint)
            break
        except Exception as e:
            last_error = e
            log.warning("Failed to fetch from %s (attempt %d/%d): %s", endpoint, i+1, len(endpoints), e)
            if i < len(endpoints) - 1:
                log.info("Retrying with next endpoint...")
                continue
            raise Exception(f"All Overpass API endpoints failed. Last error: {last_error}")

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