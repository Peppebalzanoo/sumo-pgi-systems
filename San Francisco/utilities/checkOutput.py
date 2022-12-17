import xml.etree.ElementTree as ET


def get_vehicle_from_xml():
    tree = ET.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


def check_stops(filename, strategia, scenario):
    file = open(filename, "a")
    tree = ET.parse("../output/" + strategia + "/" + scenario + "/stops.xml")
    root = tree.getroot()
    for vecID in get_vehicle_from_xml():
        count = 0
        for stop in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            count += 1
        if count > 1:
            print("VecID:", vecID, "ha effettuato più di una fermata (" + str(count) + ")", file=file)
    file.close()


def check_route(filename, strategia, scenario):
    file = open(filename, "w")

    tree = ET.parse("../output/" + strategia + "/" + scenario + "/vehroute.xml")
    root = tree.getroot()
    for vecID in get_vehicle_from_xml():
        count = 0
        first_list = []
        for route in root.findall(".//vehicle/[@id='" + vecID + "']//routeDistribution//route"):
            temp_list = list(route.attrib["edges"].split(" "))
            if count == 0:
                first_list = temp_list
                count += 1
            else:
                if all(edg in temp_list for edg in first_list) is False:
                    print("VecID:", vecID, "ha un percorso inconsistente", file=file)
                    break
    file.close()


def run(strategia, scenario):
    filename = "check_output_" + strategia + "_" + scenario + ".txt"
    check_route(filename, strategia, scenario)
    check_stops(filename, strategia, scenario)


def main():
    run("strategia1", "100%")
    # run("strategia1", "75%")
    # run("strategia1", "50%")

    run("strategia2", "100%")
    # run("strategia2", "75%")
    # run("strategia2", "50%")

    # run("strategia3", "100%")
    # run("strategia3", "75%")
    # run("strategia3", "50%")


if __name__ == "__main__":
    main()
