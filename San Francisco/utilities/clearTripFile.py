import sys
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
# . = current node
# / = only 1 level of subelements
# // = all subelements


def insert_vec_type(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    diz = {"id": "passenger", "vClass": "passenger"}
    elem = ET.Element("vType", diz)
    root.insert(0, elem)
    new_root = ET.Element(root.tag)
    new_root.text = "\n"

    for vec in root.findall("./vType"):
        vec.tail = "\n \u0020"
        new_root.append(vec)

    for trip in root.findall(".//trip"):
        new_root.append(trip)
    new_tree = ET.ElementTree(new_root)
    new_tree.write(filename, encoding="utf-8", method="xml", xml_declaration=True)


def remove_attr(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    new_root = ET.Element(root.tag)
    new_root.text = "\n \u0020"
    for trip in root.findall(".//trip"):
        trip.text = ''
        for key in ["trip_type", "type", "color", "from_taz", "to_taz", "stat", "flag", "direction", "end"]:
            trip.attrib.pop(key)
        trip.attrib["depart"] = "0.00"
        new_root.append(trip)
    new_tree = ET.ElementTree(new_root)
    new_tree.write(filename, encoding="utf-8", method="xml", xml_declaration=True)

def remove_stop(input_filename, output_filename):
    tree = ET.parse(input_filename)
    root = tree.getroot()
    for trip in root.findall(".//trip"):
        trip.text = ''
        for stop in trip.findall(".//stop"):
            trip.remove(stop)
    tree.write(output_filename, encoding="utf-8",  method="xml", xml_declaration=True)

def main():
    parser = ArgumentParser(description="Clear trip-file")
    parser.add_argument("-trp", "--trip-file", help="the trip.trips.xml input filename")
    parser.add_argument("-o", "--output-file", help="the output.trips.xml filename")
    options = parser.parse_args()
    if options.trip_file is None or options.output_file is None:
        parser.print_help()
        sys.exit()
    else:
        remove_stop(options.trip_file, options.output_file)
        remove_attr(options.output_file)
        insert_vec_type(options.output_file)

if __name__ == "__main__":
    main()
