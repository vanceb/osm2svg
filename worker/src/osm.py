import os
import sys
import logging
import logging.config
import yaml
import xml.etree.ElementTree as ET
from pyproj import CRS, Transformer

# Representation of an OSM node
# A geographic point defined by a lat/lon
class Node (object):


    def __init__(self, id=None, lat=None, lon=None, xml=None):
        self.__id = id
        self.__lat = lat
        self.__lon = lon
        if xml is not None:
            self.fromXML(xml)

    def __str__(self):
        return "id: {} ({:01.2f}, {:01.2f})".format(self.id, self.lat, self.lon)

    def __repr__(self):
        return type(self).__name__ + "({}, {}, {})".format(self.id, self.lat, self.lon)

    def __eq__(self, other):
        return (self.lat == other.lat) and (self.lon == other.lon)

    @property
    def id(self):
        return self.__id

    @property
    def lat(self):
        return self.__lat

    @lat.setter
    def lat(self, lat):
        if type(lat) == str:
            lat = float(lat)

        if lat >= -90.0 and lat <= 90:
            self.__lat = lat
        else:
            raise ValueError

    @property
    def lon(self):
        return self.__lon

    @lon.setter
    def lon(self, lon):
        if type(lon) == str:
            lon = float(lon)
        if lon > -180 and lon <= 180:
            self.__lon = lon

    def fromXML(self, element):
        if element is not None and element.tag == "node":
            self.__id = element.attrib["id"]
            self.lat = element.attrib["lat"]
            self.lon = element.attrib["lon"]
        else:
            raise ValueError

    # Very minimal XML missing all of the tags from the original data!
    def toXML(self, parent):
        if self.id is not None:
            attrs = {"id": self.id,
                     "lat": self.lat,
                     "lon": self.lon
                    }
            ET.SubElement(parent, "node", attrs)
        return parent


# Class representing an OSM way which is a list of node IDs
class Way (list):


    def __init__(self, id=None, xml=None):
        self.__id = id
        if xml is not None:
            self.fromXML(xml)

    def __str__(self):
        return "id: {}: {}".format(self.id, str(list(self)))

    def __repr__(self):
        return type(self).__name__ + "({}, {})".format(self.id, str(list(self)))

    @property
    def id(self):
        return self.__id

    def is_closed(self):
        return self[0] == self[-1]

    def fromXML(self, element):
        if element is not None and element.tag == "way":
            self.__id = element.attrib["id"]
            for nd in element.findall("./nd"):
                self.append(nd.attrib["ref"])
        else:
            raise ValueError

    # Very minimal XML missing all of the tags from the original data!
    def toXML(self, parent):
        if self.__id is not None:
            attrs = {"id": self.__id}
            way = ET.SubElement(parent, "way", attrs)
            for ref in self:
                attrs = {"ref": ref}
                ET.SubElement(way, "nd", attrs)
        return parent


class Member(object):


    def __init__(self, mtype, ref, role):
        self.type = mtype
        self.ref = ref
        self.role = role


class Relation(object):


    def __init__(self, id):
        self.__id = id
        self.__members = []
        self.__by_role = {}

    @property
    def id(self):
        return self.__id

    @property
    def members(self):
        return self.__members

    @property
    def roles(self):
        if len(self.__by_role) > 0:
            return list(self.__by_role.keys)

    def add(self, member):
        if type(member) == Member:
            self.__members.append(member)
            if member.role in self.__by_role:
                self.__by_role[member.role].append(member)
            else:
                self.__by_role[member.role] = [member]
        else:
            raise ValueError

    def remove(self, id):
        if id in self.__members:
            self.__members.remove(id)
            for role in self.__by_role:
                if id in self.__by_role[role]:
                    self.__by_role[role].remove(id)
                    if len(self.__by_role[role]) == 0:
                        self.__by_role.pop(role)

    def get_role_members(self, role):
        if role in self.__by_role:
            return self.__by_role[role]
        else:
            raise ValueError



class OSMData(object):


    def __init__(self, filename=None):
        self.__root = None
        self.__bounds = None
        self.__nodes = {}
        self.__ways = {}
        self.__relations = {}
        if filename is not None:
            self.load(filename)


    @property
    def bounds(self):
        return self.__bounds


    def load(self, filename):
        log = logging.getLogger(__name__)
        fullpath = os.path.abspath(filename)

        # Parse the file
        log.info("Reading data file: " + fullpath)
        tree = ET.parse(fullpath)
        self.__root =  tree.getroot()
        self.fromXML(self.__root)


    def fromXML(self, root):
        log = logging.getLogger(__name__)
        self.__root = root

        # Get the bounding box from the data file
        b = self.__root.find("./bounds")
        self.__bounds = {
                "minlat": b.attrib["minlat"],
                "minlon": b.attrib["minlon"],
                "maxlat": b.attrib["maxlat"],
                "maxlon": b.attrib["maxlon"]
                }
        log.info("Geographic bounds of the data: " + str(self.__bounds))

        self.__parse_ways()

    # Parse the ways into lists of Nodes
    # Then place them into a dictionary referenced by ID
    def __parse_ways(self):
        log = logging.getLogger(__name__)
        log.info("Indexing ways...")
        # Index node data by id for fast lookup
        nodes = self.__root.findall("./node")
        for node in nodes:
            n = Node()
            n.fromXML(node)
            self.__nodes[n.id] = n

        # Index way data by id for fast lookup
        ways = self.__root.findall("./way")
        for way in ways:
            wy = Way()
            wy.fromXML(way)
            self.__ways[wy.id] = wy


    # Pulls together a list of nodes that for the way
    def path(self, way_id):

        path = []
        if way_id in self.__ways:
            for nid in self.__ways[way_id]:
                path.append(self.__nodes[nid])
        else: 
            raise ValueError

        return path


    # Returns a list of Nodes that match the xpath
    def get_nodes(self, xpath):
        nodes = []
        for node in self.__root.findall(xpath):
            if node.tag == "node":
                nid = node.attrs["id"]
                nodes.append(self.__nodes[nid])
            else:
                raise ValueError

        return nodes


    # Returns a list of lists of Nodes
    # Each sublist defines a way
    def get_ways(self, xpath):
        ways = []
        for way in self.__root.findall(xpath):
            if way.tag == "way":
                wid = way.attrib["id"]
                ways.append(self.path(wid))
            else:
                raise ValueError

        return ways


    # Returns a list of dictionaries
    # Each dictionary (hopefully) contains 2 keys "inner" and "outer"
    # Each of these expand to a list of Nodes that define the ways
    # that make up the complex relational object
    def get_relations(self, xpath):
        log = logging.getLogger(__name__)

        relations = []

        # relation = Node,Way,Relation - Stuff we expect to get back...
        for relation in self.__root.findall(xpath):
            if relation.tag == "relation":
                # There is an extra layer of indirection in the data
                members =  relation.findall("./member[@type='way']")
                log.debug("Found {} member ways".format(len(members)))
                inner = []
                outer = []
                ways_left = {}
                endpoints = {"inner": {}, "outer":{}}
                for member in members:
                    way_id = member.attrib["ref"]
                    role = member.attrib["role"]
                    if role not in ["inner", "outer"]:
                        log.error("Bad role: " + role)
                    else:
                        if way_id in self.__ways:
                            if len(self.__ways[way_id]) > 1:
                                # Add it for processing
                                ways_left[way_id] = role
                                # Capture the endpoints of the ways
                                start = role + str(self.__nodes[self.__ways[way_id][0]].id)
                                end =   role + str(self.__nodes[self.__ways[way_id][-1]].id)
                                if start not in endpoints[role]:
                                    endpoints[role][start] = [way_id]
                                else:
                                    endpoints[role][start].append(way_id)
                                if end not in endpoints[role]:
                                    endpoints[role][end] = [way_id]
                                else:
                                    endpoints[role][end].append(way_id)
                            else:
                                log.warning("Short way " + way_id)
                        else:
                            log.warning("Missing way: " + way_id)

                log.debug("Endpoints " + str(endpoints))
                
                for role in endpoints:
                    for jn in endpoints[role]:
                        if endpoints[role][jn][0] in ways_left:
                            # Mark the way as processed by removing it
                            log.debug("Way " + endpoints[role][jn][0])
                            del ways_left[endpoints[role][jn][0]]

                            # Make sure that we have a matching endpoint
                            if len(endpoints[role][jn]) != 2:
                                log.error("Unclosed multipolygon " + relation.attrib["id"])

                            # Look for islands (self-closed way)
                            elif endpoints[role][jn][0] == endpoints[role][jn][1]:
                                # We have a self closed way (polygon)
                                log.debug("Found island " + endpoints[role][jn][0])
                                if role == "inner":
                                    inner.append(self.path(endpoints[role][jn][0]))
                                elif role == "outer":
                                    outer.append(self.path(endpoints[role][jn][0]))
                                else:
                                    log.error("unregonised role " + role)
                            else:
                                # General open way that needs to be joined
                                begin = endpoints[role][jn][0]
                                nextway = endpoints[role][jn][1]
                                # Start the chain
                                chain = self.path(begin)

                                log.debug("Start of chain: " + str(chain))

                                while nextway in ways_left:
                                    # Mark the way as processed by removing it
                                    del ways_left[nextway]
                                    log.debug("Way " + nextway)

                                    # Join this way to the chain
                                    if (self.__ways[nextway][0] == chain[-1].id):
                                        # The start of the next way matches the end of the chain
                                        chain = chain + self.path(nextway)

                                    elif (self.__ways[nextway][-1] == chain[-1].id):
                                        # The end of the next matches the end of the chain
                                        chain = chain + list(reversed(self.path(nextway)))

                                    elif (self.__ways[nextway][0] == chain[0].id):
                                        # The start of the next way matches the start of the chain
                                        chain = list(reversed(self.path(nextway))) + chain

                                    elif (self.__ways[nextway][-1] == chain[0].id):
                                        # The end of the next way matches the start of the chain
                                        chain = self.path(nextway) + chain

                                    else:
                                        log.error("Broken chain " + nextway)
                                    
                                    # Follow the chain
                                    for junction in endpoints[role]:
                                        if nextway in endpoints[role][junction]:
                                            if len(endpoints[role][junction]) > 1:
                                                if nextway == endpoints[role][junction][0]:
                                                    n = endpoints[role][junction][1]
                                                else:
                                                    n = endpoints[role][junction][0]
                                            else:
                                                log.error("Missing way causing incomplete chain")
                                            if n in ways_left:                                                    
                                                nextway = n
                                                break
                                    
                                # Check to see that the chain is closed
                                if chain[0].id != chain[-1].id:
                                    log.error ("Incomplete chain " + nextway)

                                # Add the chain anyway so can debug or recover
                                if role == "inner":
                                    inner.append(chain)
                                elif role == "outer":
                                    outer.append(chain)
                                else:
                                    log.error("Unrecognised role " + role)
            else:
                raise ValueError
            
            relations.append({"outer": outer, "inner": inner})

        return relations



def main():
    pass


if __name__ == "__main__":
    main()