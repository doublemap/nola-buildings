from __future__ import print_function

import re
import xml.etree.ElementTree as ET
import sys

import expansions

"""Script to process Kokomo address data in OSM format, and generate
a cleaned up, porperly tagged OSM file."""

INITIAL_ID = -747


def main(infile):
    osm = ET.parse(infile)
    root = osm.getroot()

    count_skipped = 0

    # tree for storing good nodes
    processed_root = newroot()

    # tree for storing nodes that have problems (unparseable addrs)
    problems_root = newroot()

    for node in root:
        house_numb_node = node.find("tag[@k='HOUSE_NUMB']")
        if house_numb_node is None:
            log("Skipping node without HOUSE_NUMB")
            count_skipped += 1
            continue

        dir_node = node.find("tag[@k='DIR']")
        street_node = node.find("tag[@k='STREET']")
        type_node = node.find("tag[@k='TYPE']")
        address_la_node = node.find("tag[@k='ADDRESS_LA']")

        house_numb_text = house_numb_node.attrib['v']
        if dir_node:
            dir_text = dir_node.attrib['v']
        else:
            dir_text = None
        street_text = capitalize(street_node.attrib['v'])
        address_la_text = address_la_node.attrib['v']
        if type_node is not None:
            type_text = type_node.attrib['v']
        else:
            log("%s does not have a street type" % address_la_text)
            type_text = None

        status_node = node.find("tag[@k='STATUS']")
        if status_node and status_node.attrib['v'] == "RETIRED":
            log("Skipping retired addr: " + address_la_text)
            count_skipped += 1
            continue

        if type_text in expansions.road_types:
            type_text = expansions.road_types[type_text]
        elif type_text is not None:
            log("Could not expand street type " + type_text)
            type_text = capitalize(type_text)

        if dir_text and dir_text in expansions.directions:
            dir_text = expansions.directions[dir_text]
        elif dir_text:
            log("Could not expand direction " + dir_text)
        else: # don't do anything if there is no street direction
            pass

        street = " ".join(filter(None, [dir_text, street_text, type_text]))

        newnode(processed_root, node.attrib['lat'], node.attrib['lon'], {
            "addr:housenumber": house_numb_text,
            "addr:street": street
            })
        log('%s\t\t%s' % (house_numb_text, street))

    log("----")
    log("%d nodes skipped" % count_skipped)
    log("%d nodes total" % len(root))

    processed_doc = ET.ElementTree(processed_root)
    processed_doc.write(sys.stdout, encoding="UTF-8")


def capitalize(txt):
    return " ".join(map(capitalize_word, txt.split(" ")))


def capitalize_word(txt):
    """Capitalizes one word."""
    return txt[0].upper() + txt[1:].lower()


def newroot():
    root = ET.Element("osm")
    root.attrib['version'] = '0.6'
    root.attrib['upload'] = 'true'
    root.attrib['generator'] = 'erjiang/kokomo-addresses'
    return root


def newnode(root, lat, lon, tags={}):
    "Creates and returns a new <node> element."
    n = ET.Element("node")
    n.attrib['id'] = newid()
    n.attrib['lat'] = lat
    n.attrib['lon'] = lon
    n.attrib['visible'] = "true"
    root.append(n)

    for k, v in tags.iteritems():
        n.append(ET.Element("tag", attrib={
            "k": k,
            "v": v
            }))

    return n


def newid():
    "Generates the next (negative) ID number."
    global INITIAL_ID
    INITIAL_ID -= 1
    return str(INITIAL_ID)


def parse_addr(text):
    matches = re.match('(\\d+)\\s+(.+)', text)
    if not matches:
        return None

    housenumber = matches.group(1)
    street = expand_street(matches.group(2))

    return (housenumber, street)


def expand_street(text):
    # expand directions
    def expand_dir(abbr_match):
        abbr = abbr_match.group()
        if abbr in expansions.directions:
            return expansions.directions[abbr]
        else:
            return abbr
    text = re.sub("\\b[NSEW]{,2}\\b", expand_dir, text)

    # expand road type
    def expand_road(abbr_match):
        abbr = abbr_match.group()
        if abbr in expansions.road_types:
            return expansions.road_types[abbr]
        else:
            return abbr
    text = re.sub('\\b\\w{,5}$', expand_road, text)
    return text


def log(text):
    if isinstance(text, str):
        sys.stderr.write(text)
    else:
        sys.stderr.write(repr(text))
    sys.stderr.write("\n")


if __name__ == "__main__":
    main(sys.stdin)
