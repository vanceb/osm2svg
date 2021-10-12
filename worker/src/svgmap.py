import os
import sys
import logging
import logging.config
import yaml
from argparse import ArgumentParser
import xml.etree.ElementTree as ET

import osm
from svg import SVG, Layer
import clipsvg
import common

def txt_attribution():
    attr = """
            The data used to create this svg map is copyright OpenStreetMap and its contributors.
            For full copyright information see https://www.openstreetmap.org/copyright
            The data is distributed under the Open Data Commons Open Database License.
            Details of this license can be found: https://opendatacommons.org/licenses/odbl/ 
           """
    return ET.Comment(attr)

def svg_attribution(height, width):
    attr = '''
    <g id="Attribution" 
        transform="scale(0.5 -0.5)"
        stroke="#B000A0"
        stroke-width="0.4"
        fill="none"
    >
        <path d="M 13.173 8.459 L 12.569 8.157 L 11.965 7.552 L 11.663 6.948 L 11.361 6.042 L 11.361 4.531 L 11.663 3.625 L 11.965 3.02 L 12.569 2.416 L 13.173 2.114 L 14.382 2.114 L 14.986 2.416 L 15.59 3.02 L 15.893 3.625 L 16.195 4.531 L 16.195 6.042 L 15.893 6.948 L 15.59 7.552 L 14.986 8.157 L 14.382 8.459 L 13.173 8.459"/>
        <path d="M 18.31 6.344 L 18.31 0 M 18.31 5.437 L 18.914 6.042 L 19.518 6.344 L 20.425 6.344 L 21.029 6.042 L 21.633 5.437 L 21.935 4.531 L 21.935 3.927 L 21.633 3.02 L 21.029 2.416 L 20.425 2.114 L 19.518 2.114 L 18.914 2.416 L 18.31 3.02"/>
        <path d="M 23.748 4.531 L 27.374 4.531 L 27.374 5.135 L 27.072 5.739 L 26.769 6.042 L 26.165 6.344 L 25.259 6.344 L 24.654 6.042 L 24.05 5.437 L 23.748 4.531 L 23.748 3.927 L 24.05 3.02 L 24.654 2.416 L 25.259 2.114 L 26.165 2.114 L 26.769 2.416 L 27.374 3.02"/>
        <path d="M 29.489 6.344 L 29.489 2.114 M 29.489 5.135 L 30.395 6.042 L 30.999 6.344 L 31.906 6.344 L 32.51 6.042 L 32.812 5.135 L 32.812 2.114"/>
        <path d="M 39.157 7.552 L 38.553 8.157 L 37.646 8.459 L 36.438 8.459 L 35.531 8.157 L 34.927 7.552 L 34.927 6.948 L 35.229 6.344 L 35.531 6.042 L 36.136 5.739 L 37.948 5.135 L 38.553 4.833 L 38.855 4.531 L 39.157 3.927 L 39.157 3.02 L 38.553 2.416 L 37.646 2.114 L 36.438 2.114 L 35.531 2.416 L 34.927 3.02"/>
        <path d="M 41.574 8.459 L 41.574 3.322 L 41.876 2.416 L 42.48 2.114 L 43.085 2.114 M 40.668 6.344 L 42.783 6.344"/>
        <path d="M 44.898 6.344 L 44.898 2.114 M 44.898 4.531 L 45.2 5.437 L 45.804 6.042 L 46.408 6.344 L 47.315 6.344"/>
        <path d="M 48.523 4.531 L 52.149 4.531 L 52.149 5.135 L 51.847 5.739 L 51.544 6.042 L 50.94 6.344 L 50.034 6.344 L 49.43 6.042 L 48.825 5.437 L 48.523 4.531 L 48.523 3.927 L 48.825 3.02 L 49.43 2.416 L 50.034 2.114 L 50.94 2.114 L 51.544 2.416 L 52.149 3.02"/>
        <path d="M 53.962 4.531 L 57.587 4.531 L 57.587 5.135 L 57.285 5.739 L 56.983 6.042 L 56.379 6.344 L 55.472 6.344 L 54.868 6.042 L 54.264 5.437 L 53.962 4.531 L 53.962 3.927 L 54.264 3.02 L 54.868 2.416 L 55.472 2.114 L 56.379 2.114 L 56.983 2.416 L 57.587 3.02"/>
        <path d="M 60.004 8.459 L 60.004 3.322 L 60.306 2.416 L 60.911 2.114 L 61.515 2.114 M 59.098 6.344 L 61.213 6.344"/>
        <path d="M 63.328 8.459 L 63.328 2.114 M 63.328 8.459 L 65.745 2.114 M 68.162 8.459 L 65.745 2.114 M 68.162 8.459 L 68.162 2.114"/>
        <path d="M 73.902 6.344 L 73.902 2.114 M 73.902 5.437 L 73.298 6.042 L 72.694 6.344 L 71.788 6.344 L 71.183 6.042 L 70.579 5.437 L 70.277 4.531 L 70.277 3.927 L 70.579 3.02 L 71.183 2.416 L 71.788 2.114 L 72.694 2.114 L 73.298 2.416 L 73.902 3.02"/>
        <path d="M 76.32 6.344 L 76.32 0 M 76.32 5.437 L 76.924 6.042 L 77.528 6.344 L 78.434 6.344 L 79.039 6.042 L 79.643 5.437 L 79.945 4.531 L 79.945 3.927 L 79.643 3.02 L 79.039 2.416 L 78.434 2.114 L 77.528 2.114 L 76.924 2.416 L 76.32 3.02"/>
        <path d="M 90.218 5.437 L 89.613 6.042 L 89.009 6.344 L 88.103 6.344 L 87.499 6.042 L 86.894 5.437 L 86.592 4.531 L 86.592 3.927 L 86.894 3.02 L 87.499 2.416 L 88.103 2.114 L 89.009 2.114 L 89.613 2.416 L 90.218 3.02"/>
        <path d="M 93.541 6.344 L 92.937 6.042 L 92.333 5.437 L 92.031 4.531 L 92.031 3.927 L 92.333 3.02 L 92.937 2.416 L 93.541 2.114 L 94.448 2.114 L 95.052 2.416 L 95.656 3.02 L 95.958 3.927 L 95.958 4.531 L 95.656 5.437 L 95.052 6.042 L 94.448 6.344 L 93.541 6.344"/>
        <path d="M 98.073 6.344 L 98.073 2.114 M 98.073 5.135 L 98.98 6.042 L 99.584 6.344 L 100.49 6.344 L 101.095 6.042 L 101.397 5.135 L 101.397 2.114"/>
        <path d="M 104.116 8.459 L 104.116 3.322 L 104.418 2.416 L 105.022 2.114 L 105.627 2.114 M 103.21 6.344 L 105.325 6.344"/>
        <path d="M 107.439 6.344 L 107.439 2.114 M 107.439 4.531 L 107.742 5.437 L 108.346 6.042 L 108.95 6.344 L 109.857 6.344"/>
        <path d="M 111.065 8.459 L 111.367 8.157 L 111.669 8.459 L 111.367 8.761 L 111.065 8.459 M 111.367 6.344 L 111.367 2.114"/>
        <path d="M 113.784 8.459 L 113.784 2.114 M 113.784 5.437 L 114.389 6.042 L 114.993 6.344 L 115.899 6.344 L 116.504 6.042 L 117.108 5.437 L 117.41 4.531 L 117.41 3.927 L 117.108 3.02 L 116.504 2.416 L 115.899 2.114 L 114.993 2.114 L 114.389 2.416 L 113.784 3.02" />
        <path d="M 119.525 6.344 L 119.525 3.322 L 119.827 2.416 L 120.431 2.114 L 121.338 2.114 L 121.942 2.416 L 122.848 3.322 M 122.848 6.344 L 122.848 2.114" />
        <path d="M 125.568 8.459 L 125.568 3.322 L 125.87 2.416 L 126.474 2.114 L 127.078 2.114 M 124.661 6.344 L 126.776 6.344" />
        <path d="M 130.1 6.344 L 129.495 6.042 L 128.891 5.437 L 128.589 4.531 L 128.589 3.927 L 128.891 3.02 L 129.495 2.416 L 130.1 2.114 L 131.006 2.114 L 131.61 2.416 L 132.215 3.02 L 132.517 3.927 L 132.517 4.531 L 132.215 5.437 L 131.61 6.042 L 131.006 6.344 L 130.1 6.344" />
        <path d="M 134.632 6.344 L 134.632 2.114 M 134.632 4.531 L 134.934 5.437 L 135.538 6.042 L 136.142 6.344 L 137.049 6.344" />
        <path d="M 141.581 5.437 L 141.279 6.042 L 140.372 6.344 L 139.466 6.344 L 138.559 6.042 L 138.257 5.437 L 138.559 4.833 L 139.164 4.531 L 140.674 4.229 L 141.279 3.927 L 141.581 3.322 L 141.581 3.02 L 141.279 2.416 L 140.372 2.114 L 139.466 2.114 L 138.559 2.416 L 138.257 3.02" />
        <path d="M 7.001 5.324 C 7.001 7.214 5.466 8.749 3.576 8.749 C 1.686 8.749 0.151 7.214 0.151 5.324 C 0.151 3.434 1.686 1.899 3.576 1.899 C 5.466 1.899 7.001 3.434 7.001 5.324 Z"/>
        <path d="M 5.161 4.083 C 4.446 3.398 3.287 3.398 2.572 4.083 C 1.857 4.768 1.857 5.879 2.572 6.565 C 3.287 7.25 4.446 7.25 5.161 6.565" />
    </g>
    '''

    xml = ET.fromstring(attr)
    xml.attrib['transform'] = "translate({} {}) ".format(width - 75, height) + xml.attrib['transform']
    return xml


def read_OSM_data(filename):
    log = logging.getLogger(__name__)
    fullpath = os.path.abspath(filename)

    if os.path.exists(fullpath):
        # Parse the file
        log.info("Reading data file: " + fullpath)
        tree = ET.parse(fullpath)
        return tree.getroot()

    else:
        log.error("Data file does not exist: " + fullpath)
        sys.exit()


def make_xpath(feature, source):
    log = logging.getLogger(__name__)
    xp = None
    if "=" in source:
        parts = source.split("=")
        if len(parts) != 2:
            log.error("Unable to correctly parse kv pair from " + source)
        else:
            if feature == "relation":
                xp = "./relation/tag[@k='type'][@v='multipolygon']/../tag[@k='{}'][@v='{}']/..".format(parts[0], parts[1])
            else:
                xp = "./{}/tag[@k='{}'][@v='{}']/..".format(feature, parts[0], parts[1])
    else:
        if feature == "relation":
            xp = "./relation/tag[@k='type'][@v='multipolygon']/../tag[@k='{}']/..".format(source)
        else:
            xp = "./{}/tag[@k='{}']/..".format(feature, source)
    log.info("Source: {}, XPath: {}".format(source, xp))
    return xp

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

def svg_write(root, filename, pretty=True):
    log = logging.getLogger(__name__)
    log.info("Writing svg file to " + filename)
    if pretty:
        root = indent(root)
    with open(filename, "wb") as f:
        tree = ET.ElementTree(root)
        tree.write(f, encoding="UTF-8", xml_declaration=True)


def osm_to_svg(osmdata, config, x_mm=None, y_mm=None, scale=None, no_inkscape=False, epsg=3857):
    """Gathers the OSM data needed to create the desired SVG
    
    Grabs data from the openstreetmap object based on the configuration
    then populates the svg.SVG object
    """

    log = logging.getLogger(__name__)

    # Parse the xml into a structure used to create the SVG
    if type(osmdata) == osm.OSMData:
        # Already processed into OSMData
        osmap = osmdata
    else:
        # Assume still XML
        osmap = osm.OSMData()
        osmap.fromXML(osmdata)
 

    # Create the svg structure
    svgdata = SVG(osmap.bounds, epsg=epsg)
    svgdata.inkscape = not no_inkscape

    if x_mm is not None and x_mm > 0:
        svgdata.width = x_mm
    if y_mm is not None and y_mm > 0:
        svgdata.height = y_mm
    # Set the scale
    if scale is not None and scale > 0:
        svgdata.scale = scale

    # Add the OSM paths we want to render in the SVG
    for name in config["layers"]:
        log.info("Compiling layer: " + name)
        l = Layer(name)
        l.attrib = config["layers"][name]["attrib"]
        for shape in ["ways", "areas", "complex"]:
            if shape in config["layers"][name]:
                log.info("Processing " + shape)
                for source in config["layers"][name][shape]:
                    log.info("Using source " + source)
                    if shape == "complex":
                        xp = make_xpath("relation", config["layers"][name][shape][source])
                        log.debug("XPath " + xp)
                        l.paths += osmap.get_relations(xp)
                    elif shape == "areas" or shape == "ways":
                        xp = make_xpath("way", config["layers"][name][shape][source])
                        log.debug("XPath " + xp)
                        l.paths += osmap.get_ways(xp)
                    else:
                        log.warning("Unrecognised shape in config " + shape)
                
        # Add layer to SVG
        if len(l.paths) == 0:
            log.info("No data found for layer {}, removing...".format(name))
        else:
            log.info("Found {} elements for layer {}".format(len(l.paths), name))
            svgdata.layers[name] = l

    # Generate the svg file based on the config and the map data
    svg = svgdata.get_svg()

    # Add OSM Copyright and attribution
    svg.insert(0, svg_attribution(y_mm, x_mm))
    svg.insert(0, txt_attribution())

    # Clip svg to viewBox
    clipsvg.svg_clip(svg)

    return svg


def main ():
    # Configure logging
    common.setup_logging()
    log = logging.getLogger(__name__)
    log.info("OSM to Lightburn - Starting")

    # Set up command line interface
    parser = ArgumentParser()
    parser.add_argument(
            "osmdatafile",
            help="The OSM data file containing map data"
            )
    parser.add_argument(
            "outputfile",
            nargs='?',
            help="The output filename.  If not supplied defaults to " +
                 "osmdatafile, but with the .svg extension"
            )
    parser.add_argument(
            "--config", 
            dest="configfile",
            default="conf/all.yaml",
            help="Config file to use. Defaults to ./conf/all.yaml"
            )
    parser.add_argument(
            "--scale",
            dest="scale",
            default=10000,
            type=int,
            help="Map scale set to 1:<this number>"
            )
    parser.add_argument(
            "--x_mm",
            dest="x_mm",
            type=int,
            help="The x dimension in mm.  If set this overrides scale."
            )
    parser.add_argument(
            "--y_mm",
            dest="y_mm",
            type=int,
            help="The y dimension in mm.  If set this overrides scale and x_mm."
            )
    parser.add_argument(
            "--no_inkscape",
            dest="no_inkscape",
            action="store_true",
            help="Do not add inkscape tags to the data"
            )
    parser.add_argument(
            "--epsg",
            dest="epsg",
            default=3857,
            type=int,
            help="""
The EPSG number to use for the map projection. 
Defaults to 3857 (Pseudo Mercator).  For the UK, OSGB is 27700.  
You can look up other projections that may be more accurate
for your country/locality.  This doesn't affect much
in the output but will give a more accurate distance and
therefore "scale" if it is set appropriately.  It can also affect
the size and position of map features if you are covering a very
large area.
"""
            )


    # Parse the command line
    args = parser.parse_args()

    # Get the full filenames
    datafile = os.path.abspath(args.osmdatafile)
    if args.outputfile:
        outfile = os.path.abspath(args.outputfile)
    else:
        outfile = os.path.splitext(datafile)[0] + ".svg"

    configfile = os.path.abspath(args.configfile)

    # Load the config
    config = common.load_config(configfile)

    # Load the data file
    osmdata = osm.OSMData(datafile)

    # Convert into svg
    svg = osm_to_svg(osmdata, config, args.x_mm, args.y_mm, args.scale, args.no_inkscape, args.epsg)
    #svg = get_svg(osmdata, config, args.x_mm, args.y_mm)

    # Write it to disk
    svg_write(svg, outfile)

    # And we are done!
    log.info("Processing completed")


if __name__ == "__main__":
    main()
