from os.path import exists
import xml.etree.ElementTree as ET
import traci

lane_to_edge_dict = {}

def calculate_lane_to_edge_dict():
    tree = ET.parse('../san_francisco.net.xml')
    root = tree.getroot()
    for edg in root.findall(".//edge"):
        edgeID = edg.attrib["id"]
        for lane in root.findall(".//edge/[@id='"+edgeID+"']/lane"):
            laneID = lane.attrib["id"]
            lane_to_edge_dict[laneID] = edgeID
def get_indexes_xml_from_edge(edgeID):
    tree = ET.parse('../san_francisco.net.xml')
    root = tree.getroot()
    list_indexes = []
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        list_indexes.append(int(name.attrib['index']))
    return list_indexes

def get_index_xml_of_lane_from_edge_and_lane(edgeID, laneID):
    tree = ET.parse('../san_francisco.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@id='" + laneID + "']"):
        return int(name.attrib['index'])

def get_vehicle_from_xml():
    tree = ET.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


# def check_parking_lanes(filename):
#     calculate_lane_to_edge_dict()
#     temp_dict = {}
#     file = open(filename, "a")
#
#     tree = ET.parse("../parking_capacity_100%/on_parking_100%.add.xml")
#     root = tree.getroot()
#     for park in root.findall(".//parkingArea"):
#         parkID = park.get("id")
#         laneID = park.get("lane")
#         temp_dict[parkID] = laneID
#
#     tree = ET.parse("../parking_capacity_100%/off_parking_100%.add.xml")
#     root = tree.getroot()
#     for park in root.findall(".//parkingArea"):
#         parkID = park.get("id")
#         laneID = park.get("lane")
#         temp_dict[parkID] = laneID
#
#     for parkID, lane in temp_dict.items():
#         curr_edge = lane_to_edge_dict.get(lane)
#         curr_index = get_index_xml_of_lane_from_edge_and_lane(curr_edge, lane)
#         list_indexes = get_indexes_xml_from_edge(curr_edge)
#         max_index = max(list_indexes)
#         print("parkingID:", parkID, "index:", curr_index, "max_index_lane:", max_index, file=file)
#     file.close()

def check_not_parking_vehicle(filename, strategia, scenario):
    file = open(filename, "a")
    tree = ET.parse("../output/"+strategia+"/"+scenario+"/stops.xml")
    root = tree.getroot()
    list_parked = []
    for vecID in get_vehicle_from_xml():
        for stop in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            list_parked.append(vecID)
    print("Veicoli Parcheggiati:",list_parked, file=file)
    not_parked = set(get_vehicle_from_xml()).difference(set(list_parked))
    print("Veicolo Non Parcheggiati", not_parked, file=file)
    file.close()



def check_stops(filename, strategia, scenario):
    file = open(filename, "a")
    tree = ET.parse("../output/"+strategia+"/"+scenario+"/stops.xml")
    root = tree.getroot()
    for vecID in get_vehicle_from_xml():
        count = 0
        for stop in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            count += 1
        if count > 1:
            print("VecID:", vecID, "ha effettuato più di una fermata (" + str(count) + ")", file=file)
    file.close()


def check_route(filename, strategia, scenario):
    file = open(filename, "a")

    tree = ET.parse("../output/"+strategia+"/"+scenario+"/vehroute.xml")
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
    file = open(filename, "w")
    file.close()
    check_route(filename, strategia, scenario)
    check_stops(filename, strategia, scenario)
    check_not_parking_vehicle(filename, strategia, scenario)


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
