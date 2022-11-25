import os
import sys
import xml.etree.ElementTree as ElementTree
from argparse import ArgumentParser

import sumolib
from sumolib.net.edge import Edge


def main():
    parser = ArgumentParser(description="Generate vehicle from an trip-file")
    parser.add_argument("-net", "--net-file", help="the network.net.xml input filename")
    parser.add_argument("-trp", "--trip-file", help="the trip.trips.xml input filename")
    parser.add_argument("-vtp", "--vehicle-type", help="the vehicle-type")
    parser.add_argument("-o", "--output-file", help="the output.rou.net filename")
    options = parser.parse_args()
    if options.trip_file is None or (options.vehicle_type is None or options.vehicle_type not in ['passenger']) or options.net_file is None or options.output_file is None:
        parser.print_help()
        sys.exit()
    else:
        net = sumolib.net.readNet(options.net_file)
        tree = ElementTree.parse(options.trip_file)
        root = tree.getroot()

        with open(options.output_file, 'w') as outf:
            if os.path.getsize(options.output_file) == 0:
                sumolib.xml.writeHeader(outf, root="routes")
                print('<vType id="vecType" vClass="' + options.vehicle_type + '"/>', file=outf)
            idx = 0
            for elem in root.findall(".//trip"):
                startXML = elem.attrib["from"]
                endXML = elem.attrib["to"]
                depart = elem.attrib["depart"]
                print("Sto generato il percorso più veloce da", startXML, "a", endXML, "con depart time", depart, "...")

                start_edgeID = net.getEdge(startXML)
                end_edgeID = net.getEdge(endXML)
                tupla_ret = net.getShortestPath(start_edgeID, end_edgeID)  # Una tupla di tuple : tupla_ret[ tupla [elem1,...,elemN] , cost]
                tupla = tupla_ret[0]
                shortest_path = []
                for edg in tupla:
                    shortest_path.append(Edge.getID(edg))
                print('    <vehicle id="%s" type="vecType" depart="%s">' % (idx, depart), file=outf)
                print('        <route edges="%s"/>' % (" ".join(e for e in shortest_path)), file=outf)
                print('    </vehicle>', file=outf)
                idx += 1
            print("</routes>", file=outf)
            outf.close()



if __name__ == "__main__":
    main()
