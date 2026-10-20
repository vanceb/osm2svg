import os
import time
import logging
import xml.etree.ElementTree as ET
import subprocess
import requests

import common

# Geofabrik extract URL - England (516 MB, includes all of England + surrounding water)
ENGLAND_EXTRACT_URL = "https://download.geofabrik.de/europe/united-kingdom/england-latest.osm.pbf"


# Tag whitelist matching the layers in all.yaml
# Each: (key, [values]) — values=['*'] means any value for that key
TAG_WHITELIST = [
    # Highways
    ("highway", ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
                 "secondary", "secondary_link", "residential", "service", "tertiary", "unclassified",
                 "pedestrian", "footway", "path", "track"]),
    # Railways
    ("railway", ["*"]),
    # Aeroways
    ("aeroway", ["runway", "airstrip"]),
    # Natural features
    ("natural", ["wood", "sand", "beach", "dune", "water", "coastline"]),
    # Land use
    ("landuse", ["forest"]),
    # Buildings
    ("building", ["*"]),
    # Waterways
    ("waterway", ["*"]),
    # Contours
    ("contour", ["elevation"]),
]


def ensure_extract(datadir):
    """Download the England extract if it doesn't exist."""
    log = logging.getLogger(__name__)
    extract_dir = os.path.join(datadir, "extracts")
    extract_path = os.path.join(extract_dir, "england-latest.osm.pbf")

    os.makedirs(extract_dir, exist_ok=True)

    if os.path.exists(extract_path):
        log.info("England extract already exists: %s", extract_path)
        return extract_path

    log.info("Downloading England extract from Geofabrik...")
    log.info("This may take 2-5 minutes on first run (~516 MB)...")
    start = time.time()
    response = requests.get(ENGLAND_EXTRACT_URL, stream=True, timeout=600)
    response.raise_for_status()

    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    with open(extract_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                log.info("  %.1f%% (%.1f MB / %.1f MB)", pct, downloaded / 1024 / 1024, total / 1024 / 1024)

    elapsed = time.time() - start
    size_mb = os.path.getsize(extract_path) / (1024 * 1024)
    log.info("Download complete: %.1f MB in %.1f seconds", size_mb, elapsed)
    return extract_path


def _build_filter_args():
    """Build osmium 1.x positional filter expressions with type prefixes.
    Syntax: n/key=val, w/key=val, r/key=val (node, way, relation).
    Wildcards: n/key (any value for that key on that type)."""
    args = []
    for key, values in TAG_WHITELIST:
        for obj_type in ("n", "w", "r"):
            if values == ["*"]:
                args.append(f"{obj_type}/{key}")
            else:
                for val in values:
                    args.append(f"{obj_type}/{key}={val}")
    return args


def filter_extract(extract_path, minlat, minlon, maxlat, maxlon, datadir):
    """Extract OSM data for the given bounding box, then tag-filter it.
    Step 1: osmium extract --bbox (geographic filter)
    Step 2: osmium tags-filter (tag whitelist filter, type-prefixed expressions)
    Returns path to filtered XML file."""
    log = logging.getLogger(__name__)
    log.info("Filtering extract for bbox: %.6f,%.6f,%.6f,%.6f",
             minlat, minlon, maxlat, maxlon)

    output_dir = os.path.join(datadir, "filtered")
    os.makedirs(output_dir, exist_ok=True)
    intermediate_pbf = os.path.join(output_dir, "osm_data.tmp.pbf")
    output_xml = os.path.join(output_dir, "osm_data.osm")

    # Step 1: osmium extract --bbox LEFT,BOTTOM,RIGHT,TOP = minlon,minlat,maxlon,maxlat
    bbox = f"{minlon},{minlat},{maxlon},{maxlat}"
    cmd_extract = ["osmium", "extract", "--bbox", bbox, "-O", "-o", intermediate_pbf, extract_path]
    log.info("Step 1: osmium extract --bbox %s", bbox)
    log.info("Command: %s", " ".join(cmd_extract))
    start = time.time()
    result = subprocess.run(cmd_extract, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - start

    if result.returncode != 0:
        raise Exception(f"osmium extract failed (exit {result.returncode}) after {elapsed:.1f}s: {result.stderr[:500]}")

    if not os.path.exists(intermediate_pbf):
        raise Exception("osmium extract completed but intermediate PBF not found")

    log.info("Bbox extract: %.2f MB in %.1f seconds",
             os.path.getsize(intermediate_pbf) / (1024 * 1024), elapsed)

    # Step 2: osmium tags-filter with type-prefixed positional expressions
    # Required syntax for osmium 1.x: n/key=val, w/key=val, r/key=val
    # (no -k flag or -b bbox option in osmium 1.x)
    filter_args = _build_filter_args()
    cmd_filter = ["osmium", "tags-filter", intermediate_pbf,
                   "-f", "osm", "-O", "-o", output_xml] + filter_args

    log.info("Step 2: osmium tags-filter (%d expression args)", len(filter_args))
    start = time.time()
    result = subprocess.run(cmd_filter, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - start

    if result.returncode != 0:
        raise Exception(f"osmium tags-filter failed (exit {result.returncode}) after {elapsed:.1f}s: {result.stderr[:500]}")

    if not os.path.exists(output_xml):
        raise Exception("osmium tags-filter completed but output XML not found")

    # Clean up intermediate PBF
    try:
        os.remove(intermediate_pbf)
    except OSError:
        pass

    size_mb = os.path.getsize(output_xml) / (1024 * 1024)
    log.info("Filtered output: %.2f MB in %.1f seconds", size_mb, elapsed)
    return output_xml


def get_osm(minlat, minlon, maxlat, maxlon, config):
    """Get OSM data from the Geofabrik extract for the given bounding box."""
    log = logging.getLogger(__name__)
    log.info("Getting OSM data from Geofabrik extract: B:%.6f L:%.6f T:%.6f R:%.6f",
             minlat, minlon, maxlat, maxlon)

    datadir = config["options"]["datadir"]

    # Ensure the extract is downloaded
    extract_path = ensure_extract(datadir)

    # Filter to bounding box with tag whitelist
    xml_path = filter_extract(extract_path, minlat, minlon, maxlat, maxlon, datadir)

    # Parse XML and add bounds element (same format as overpass.py produces)
    log.info("Parsing filtered XML")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    attrib = {"minlat": str(minlat), "minlon": str(minlon),
              "maxlat": str(maxlat), "maxlon": str(maxlon)}
    ET.SubElement(root, "bounds", attrib)
    return root
