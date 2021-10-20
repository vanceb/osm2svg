# SRTM data downloadable in 1 degree squares from
# https://e4ftl01.cr.usgs.gov/MEASURES/
#
# Various data accuracies are available.  I am using
# 1 arc second data which is stored:
# https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/
# 
# You need to register to be able to download the data
# https://urs.earthdata.nasa.gov/users/new
#

import os
import sys
import math
import logging
import logging.config
import yaml
import re
from argparse import ArgumentParser

import xml.etree.ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth
from requests.compat import urljoin

import numpy as np
from skimage import measure

from zipfile import ZipFile

import common


# Session code from: 
# https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
#
# overriding requests.Session.rebuild_auth to mantain headers when redirected
class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

   # Overrides from the library to keep headers when redirected to or from
   # the NASA auth host.

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                        del headers['Authorization']
        return


def download(url, config):
    log = logging.getLogger(__name__)
    log.info("Downloading: " + url)

    credsfile = os.path.abspath(config["options"]["credentials"])
    creds = common.load_config(credsfile)

    datadir = config["options"]["datadir"]

    # extract the filename from the url to be used when saving the file
    filename = os.path.join(datadir, url[url.rfind('/')+1:])  
    filename = os.path.abspath(filename) 
    # create session with the user credentials that will be used to
    # authenticate access to the data
    session = SessionWithHeaderRedirection(creds["username"], creds["password"])

    try:
        # submit the request using the session
        response = session.get(url, stream=True)
        if response.status_code == 200:
            # save the file
            with open(filename, 'wb') as fd:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    fd.write(chunk)
                log.info("Successfully saved to " + filename)
        elif response.status_code == 401:
            log.error("Unauthorized to get the data. "  + 
                    "Have you put your login details into " +
                    "the credentials.yaml file?")
            log.error("If you don't have a login go to " +
                    "https://ers.cr.usgs.gov/register/")
        elif response.status_code == 404:
            log.warning("Unable to find: " + url)
            log.warning("Maybe its in the sea? (No data)")
        else:
            # raise an exception in case of http errors
            print(response.status_code)
            response.raise_for_status()  

    except requests.exceptions.HTTPError as e:
        # handle any errors here
        log.error(e)


def get_SRTM_grid(lat, lon):
    x = math.floor(lon)
    y = math.floor(lat)
    grid = ""

    if y < 0:
        grid += "S{:02d}".format(-y)
    else:
        grid += "N{:02d}".format(y)
    if x < 0:
        grid += "W{:03d}".format(-x)
    else:
        grid += "E{:03d}".format(x)

    return grid


def get_SRTM_grid_list(min_lat, min_lon, max_lat, max_lon):
    log = logging.getLogger(__name__)
    log.info("Getting SRTM data for {} {} {} {}".format(
        min_lat, min_lon, max_lat, max_lon))

    grids = []
    # Get the SRTM 1 degree boundaries
    l = math.floor(min_lon)
    r = math.ceil(max_lon)
    t = math.ceil(max_lat)
    b = math.floor(min_lat)

    for x in range(l, r):
        for y in range(b, t):
            grids.append(get_SRTM_grid(y, x))

    return grids


def get_SRTM_data(config, min_lat, min_lon, max_lat, max_lon):
    log = logging.getLogger(__name__)

    grids = get_SRTM_grid_list(min_lat, min_lon, max_lat, max_lon)

    # Ensure that the data directory exists
    datadir = config["options"]["datadir"]
    os.makedirs(datadir, exist_ok=True)

    # Make sure we have the data
    for grid in grids:
        log.info("Checking data for grid " + grid)
        # Check to see whether we already have this data
        filename = os.path.join(datadir, grid + ".hgt")
        filename = os.path.abspath(filename)

        if os.path.exists(filename):
            log.info("Data available: " + filename)
        else:
            template = config["data"]["url_template"]
            url = template.replace("<GRID>", grid, 1)
            zipfilename = os.path.join(datadir, url[url.rfind('/')+1:])  
            # Download
            if not os.path.exists(zipfilename):
                download(url, config)
            # If still not downloaded it may be sea (no data)
            if not os.path.exists(zipfilename):
                datafile = os.path.join(datadir, grid + ".hgt")
                log.warning("Data not downloaded - Touching " + datafile +
                            " If you want to redownload please delete this file")
                open(datafile, "a").close()

            # Unzip
            if os.path.exists(zipfilename):
                log.info("Unzipping: " + zipfilename)
                with ZipFile(zipfilename, "r") as zipf:
                    zipf.extractall(datadir)


def constrain(value, max):
    if value < 0:
        value = 0
    elif value > max:
        value = max
    return value


def contour(config, interval, min_lat, min_lon, max_lat, max_lon):
    log = logging.getLogger(__name__)

    # Make sure we have the SRTM tiles
    get_SRTM_data(config, min_lat, min_lon, max_lat, max_lon)

    # Define some variables to ease code readability
    datadir = config["options"]["datadir"]
    samples = config["data"]["samples"]

    # Create the root OSM node and the bounds tag
    root = ET.Element("osm")
    ET.SubElement(root, "bounds", 
            {"minlat": str(min_lat),
             "minlon": str(min_lon),
             "maxlat": str(max_lat),
             "maxlon": str(max_lon)})

    # Start ID counter for nodes and ways
    id = 1000000000

    # Get each data file for the area of interest
    grids = get_SRTM_grid_list(min_lat, min_lon, max_lat, max_lon)
    for grid in grids:
        log.debug("Grid: " + grid)
        # Set up some base data for each grid
        lat_sign = 1
        lon_sign = 1
        if grid[0] == "S":
            lat_sign = -1
        if grid[3] == "W":
            lon_sign = -1
        base_lat = int(grid[1:3]) * lat_sign
        base_lon = int(grid[4:]) * lon_sign


        # Generate the contours for a single SRTM tile
        filename = os.path.join(datadir, grid + ".hgt")
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # Checking size > 0 allows us to "touch" empty files to prevent downloads
            with open(filename, "rb") as f:
                # Each data is 16bit signed integer(i2) - big endian(>)
                elevations = np.fromfile(f, np.dtype('>i2'), samples*samples)\
                        .reshape((samples, samples))


                # Work out the data we want to process from this tile
                log.debug("base_lat: {}, base_lon: {}".format(base_lat, base_lon))
                log.debug("min_lat: {}, min_lon: {}, max_lat: {}, max_lon: {}".format(min_lat, min_lon, max_lat, max_lon))


                # Convert lat/lon to array indexes
                top = int(((base_lat + 1) - max_lat) * (samples - 1))
                top = constrain(top, samples)
                btm = int(((base_lat + 1) - min_lat) * (samples - 1))
                btm = constrain(btm, samples)
                lft = int((min_lon - base_lon) * (samples - 1))
                lft = constrain(lft, samples)
                rgt = int((max_lon - base_lon) * (samples - 1))
                rgt = constrain(rgt, samples)

                # Get co-ords for top left corner of the array
                # so we can convert back to lat/lon
                top_lat = base_lat + 1 - top / (samples - 1)
                lft_lon = base_lon + lft / (samples - 1)

                # Subset the array
                log.info("Subsetting data to: [{}:{}, {}:{}]".format(top, btm, lft, rgt))
                subset = elevations[top:btm, lft:rgt]
                x_range = rgt - lft
                y_range = btm - top
                log.debug("NP - Width: {}, Height: {}".format(x_range, y_range))

                # Get the lowest and highest points in the range
                max = np.amax(subset)
                min = np.amin(subset)
                if min == -32768:
                    # Missing height data is given the value -32768
                    log.warning("There are holes in your SRTM data, " +
                                "setting min height to -40m")
                    min = -40

                log.info("min height: {}, max height: {}".format(min, max))

                # Loop through the contour heights from min to max
                for height in range(interval * (min // interval) + interval,
                        interval * (max // interval) + interval, interval):
                    log.info("Processing contour at height " + str(height))

                    for line in measure.find_contours(subset, height):
                        nd_refs = []
                        for nd in line:
                            id += 1
                            nd_refs.append(id)
                            attr = {"id": str(id),
                                    "lat": str(top_lat - nd[0] / (samples - 1)),
                                    "lon": str(lft_lon + nd[1] / (samples - 1))
                                    }
                            ET.SubElement(root, "node", attr)
                            #log.debug("{} => {}".format(str(nd), str(attr)))

                        id += 1
                        way = ET.SubElement(root, "way", {"id": str(id)})
                        for nr in nd_refs:
                            ET.SubElement(way, "nd", {"ref": str(nr)})

                        ET.SubElement(way, "tag", {"k": "contour", "v": "elevation"})
                        ET.SubElement(way, "tag", {"k": "ele", "v": str(height)})
        else:
            log.warning("SRTM file {} has no content. Maybe in the sea?".format(filename))

    return root


def osm_write(root, filename):
    log = logging.getLogger(__name__)
    log.info("Writing OSM contours file to " + filename)
    tree = ET.ElementTree(root)
    with open(filename, "wb") as f:
        tree.write(f, encoding="UTF-8", xml_declaration=True)


def main():
    # Set up command line interface
    parser = ArgumentParser()
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
    parser.add_argument(
            "outputfile",
            help="The output filename"
            )
    parser.add_argument(
            "--config", 
            dest="configfile",
            default="conf/srtm.yaml",
            help="Config file to use. Defaults to ./conf/srtm.yaml"
            )
    parser.add_argument(
            "--interval", 
            dest="interval",
            type=int,
            default=10,
            help="The distance between contours in meters, defaults to 10"
            )

    # Parse the command line
    args = parser.parse_args()

    # Get the full filenames
    outfile = os.path.abspath(args.outputfile)
    configfile = os.path.abspath(args.configfile)


    common.setup_logging()
    log = logging.getLogger(__name__)

    config = common.load_config(configfile)
    config["outputfile"] = outfile

    log.info("Creating contours for B: {} L: {} T: {} R: {}".format(
        args.min_lat, args.min_lon, args.max_lat, args.max_lon))

    credsfile = config["options"]["credentials"]
    log.debug("Loading credentials from " + credsfile)
    config["creds"] = common.load_config(credsfile)

    osm = contour(config, args.interval, args.min_lat, args.min_lon, args.max_lat,
            args.max_lon)

    osm_write(osm, config["outputfile"])

if __name__ == "__main__":
    main()
