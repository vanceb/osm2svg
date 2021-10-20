import os
import sys
import re
import logging
import logging.config
import yaml
import json
import copy
import datetime
import time
from argparse import ArgumentParser
import xml.etree.ElementTree as ET

import common
import overpass
import contours
import svgmap


def run_job(config, jobspec, osmfile=None):
    log = logging.getLogger(__name__)
    start = time.time()

    if "user" in jobspec:
        if "email" in jobspec["user"] and "name" in jobspec["user"]:
            user = jobspec["user"]["name"]
        else:
            user = "Anonymous"
    log.info("Starting job for {} <{}>".format(user, jobspec["user"]["email"]))

    # Save the job
    jobfile = user + '_{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + ".json"
    jobfile = os.path.abspath(os.path.join(config["options"]["datadir"], "jobs", jobfile))
    with open (jobfile, "w") as f:
        json.dump(jobspec, f)

    # Create a deep copy of the config as we are going to modify it
    config = copy.deepcopy(config)

    # Trim unwanted layers from the config
    delete = [key for key in config["layers"] if key not in jobspec["layers"]]
    for key in delete:
        del config["layers"][key]

    # Set the interval
    interval = 10
    if "contours" in jobspec:
        if "interval" in jobspec["contours"]:
            interval = int(jobspec["contours"]["interval"])

    # Get the bounds
    minlat = float(jobspec["bounds"]["minlat"])
    minlon = float(jobspec["bounds"]["minlon"])
    maxlat = float(jobspec["bounds"]["maxlat"])
    maxlon = float(jobspec["bounds"]["maxlon"])

    # Get the dimensions
    x_mm = None
    y_mm = None
    if "x_mm" in jobspec["bounds"]:
        x_mm = float(jobspec["bounds"]["x_mm"])
    if "y_mm" in jobspec["bounds"]:
        y_mm = float(jobspec["bounds"]["y_mm"])

    # Provide a default dimension if none provided
    if x_mm is None and y_mm is None:
        x_mm = 200.0

    # Get the data from overpass
    osm = overpass.get_osm(minlat, minlon, maxlat, maxlon, config)

    # Save the osm data if needed
    if osmfile is not None:
        with open(osmfile, "wb") as f:
            tree = ET.ElementTree(osm)
            tree.write(f, encoding="UTF-8", xml_declaration=True)

            
    # Get the contour lines if wanted
    if "contours" in jobspec["layers"]:
        contours.add_contours(config["srtm"], interval, minlat, minlon, maxlat, maxlon, osm)

    # Create the svg map
    svg = svgmap.osm_to_svg(osm, config, x_mm, y_mm)
    
    end = time.time()
    log.info("Job for {} took {}".format(user, end - start))

    return svg


def main():
    # Set up command line interface
    parser = ArgumentParser()
    parser.add_argument(
            "jobspec",
            help="The filename of the job spec json file."
            )
    parser.add_argument(
            "--datadir", 
            dest="datadir",
            default="/data",
            help="Base data directory under which we expect to find the `conf` and `logs` directories"
            )
    parser.add_argument(
            "--config",
            dest="config",
            default="all.yaml",
            help="The config file to use, defaults to all.yaml"
            )
    parser.add_argument(
            "--saveosm",
            dest="saveosm",
            action="store_true",
            default=False,
            help="Save OSM data alonside job"
            )

    # Parse the command line
    args = parser.parse_args()

    # Get the full filenames
    datadir = os.path.abspath(args.datadir)
    logsdir = os.path.join(datadir, "logs")
    confdir = os.path.join(datadir, "conf")
    if os.path.isfile(args.config):
        config_file = args.config
    else:
        config_file = os.path.join(datadir, "conf", args.config)
        if not os.path.isfile(config_file):
            raise FileNotFoundError("The config file could not be found")

    # Configure logging
    log_conf = os.path.join(confdir, "logging.yaml")
    common.setup_logging(default_path=log_conf)
    log = logging.getLogger(__name__)
    log.info("OSM2SGV - Starting")

    if args.jobspec:
        jobfile = os.path.abspath(args.jobspec)
    else:
        log.error("No jobspec filename provided")

    job = os.path.splitext(jobfile)[0]
    svgfile = job + ".svg"

    osmfile = None
    if args.saveosm is not None:
        osmfile = job + ".osm"

    # Load the config
    config = common.load_config(config_file)

    # Load the jobspec
    with open(jobfile, "r") as f:
        jobspec = json.load(f)

    # Create the svg
    svg = run_job(config, jobspec, osmfile)

    # Write it to disk
    job = os.path.splitext(jobfile)[0]
    svgfile = job + ".svg"
    svgmap.svg_write(svg, svgfile)
    


if __name__ == "__main__":
    main()
