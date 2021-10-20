import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'K@35emzx%9%sco8H'
    MAP_CONFIG = {
        "options": {"datadir": "/data"},
        "srtm": {
            "options": {
                "datadir": "/data/srtm",
                "credentials": "/data/conf/credentials.yaml"
            },
            "data": {
                "url_template": "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/<GRID>.SRTMGL1.hgt.zip",
                "samples": 3601
            }
        },
        "overpass": {
            "endpoint": "https://overpass-api.de/api/interpreter"
        },
        "layers": {
            "forests": {
                "attrib": {
                    "stroke": "none",
                    "stroke-width": "0.2",
                    "fill": "#00AF00"
                },
                "areas": {
                    "wood": "natural=wood",
                    "forest": "landuse=forest",
                },
                "complex": {
                    "wood": "natural=wood",
                    "forest": "landuse=forest",
                }
            },
            "sand": {
                "attrib": {
                    "stroke": "none",
                    "stroke-width": "0.2",
                    "fill": "#FCE45F"
                },
                "areas": {
                    "sand": "natural=sand",
                    "beach": "natural=beach",
                    "dune": "natural=dune"
                },
                "complex": {
                    "sand": "natural=sand",
                    "beach": "natural=beach",
                    "dune": "natural=dune"
                },
            },
            "waterways": {
                "attrib": {
                    "stroke": "none",
                    "stroke-width": "0.2",
                    "fill": "#00E7E0"
                },
                "ways": {
                    "water": "natural=water"
                }
            },
            "water": {
                "attrib": {
                    "stroke": "none",
                    "stroke-width": "0.2",
                    "fill": "#00E7E0"
                },
                "areas": {
                    "water": "natural=water",
                },
                "complex": {
                    "waterway": "waterway",
                    "water": "natural=water"
                }
            },
            "airstrips": {
                "attrib": {
                    "stroke": "#348CFF",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "runway": "aeroway=runway",
                    "airstrip": "aeroway=airstrip"
                }
            },
            "contours": {
                "attrib": {
                    "stroke": "#C18200",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "contour": "contour=elevation"
                }
            },
            "buildings": {
                "attrib": {
                    "stroke": "none",
                    "stroke-width": "0.2",
                    "fill": "#C3DE00"
                },
                "areas": {
                    "building": "building"
                },
                "complex": {
                    "building": "building"
                }
            },
            "footpaths": {
                "attrib": {
                    "stroke": "#B3B3B3",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "pedestrian": "highway=pedestrian",
                    "footway": "highway=footway",
                    "path": "highway=path"
                }
            },
            "tracks": {
                "attrib": {
                    "stroke": "#95AA00",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "track": "highway=track",
                    "service": "highway=service"
                }
            },
            "residential": {
                "attrib": {
                    "stroke": "#FF7800",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "residential": "highway=residential"
                }
            },
            "minor_roads": {
                "attrib": {
                    "stroke": "#A80000",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "tertiary": "highway=tertiary",
                    "unclassified": "highway=unclassified"
                }
            },
            "major_roads": {
                "attrib": {
                    "stroke": "#FF0000",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "trunk": "highway=trunk",
                    "trunk_link": "highway=trunk_link",
                    "primary": "highway=primary",
                    "primary_link": "highway=primary_link",
                    "secondary": "highway=secondary",
                    "secondary_link": "highway=secondary_link",
                }
            },
            "motorways": {
                "attrib": {
                    "stroke": "#6200FF",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "motorway": "highway=motorway",
                    "motorway_link": "highway=motorway_link",
                }
            },
            "railways": {
                "attrib": {
                    "stroke": "#7F7F7F",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "railway": "railway"
                }
            },
            "coastline": {
                "attrib": {
                    "stroke": "#FF00FF",
                    "stroke-width": "0.2",
                    "fill": "none"
                },
                "ways": {
                    "coastline": "natural=coastline"
                }
            }
        }
    }

