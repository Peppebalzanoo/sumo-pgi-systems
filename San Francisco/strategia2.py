import operator
import os
import sys
import traci
import random
from os.path import exists
from sumolib import checkBinary
import xml.etree.ElementTree as ElementTree

AREA_INIT = 500
exit_vehicle_report = {}


# * ********************************************************************************************************************************************************************* * #
def myprint(mylist):
    for elem in mylist:
        print(elem)


def myprintroute(curr_route_list):
    for idx in range(0, len(curr_route_list)):
        print("         ", curr_route_list[idx])
    print("     numero_nodi: ", len(curr_route_list))


def myprintinfo(vecID, curr_laneID, curr_edgeID, curr_lane_index, last_edgeID, distance_to_lastedge, space_on_next_step, curr_route_list):
    print("     *** INFORMAZIONI VEICOLO ***")
    print("     VEICOLO:", vecID, "curr_edgeID:", curr_edgeID, "last_edgeID:", last_edgeID, "curr_laneID:", curr_laneID, "curr_lane_index:", curr_lane_index)
    print("     dist_to_last:", distance_to_lastedge, "space_on_next:", space_on_next_step)
    print("     curr_route_list:")
    myprintroute(curr_route_list)


# * ********************************************************************************************************************************************************************* * #

# (vecID, coordinateXY_lane_dest)
vecID_to_dest_lane_position_dictionary = {}

# * ********************************************************************************************************************************************************************* * #

# (currLaneID, parkingID)
lane_to_parking_dictionary = {}


def set_lane_to_parking_dictionary():
    parkingIDs_list = traci.parkingarea.getIDList()
    for parkingID in parkingIDs_list:
        curr_laneID = traci.parkingarea.getLaneID(parkingID)
        lane_to_parking_dictionary[curr_laneID] = parkingID


# * ******************************************************************************************************************************************************************** * #

def get_vehicle_from_xml():
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


# * ********************************************************************************************************************************************************************* * #

def get_lane_xml_from_edge_and_index(edgeID, index):
    tree = ElementTree.parse('san_francisco.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


def get_indexes_xml_from_edge(edgeID):
    tree = ElementTree.parse('san_francisco.net.xml')
    root = tree.getroot()
    list_indexes = []
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        list_indexes.append(int(name.attrib['index']))
    return list_indexes


def get_index_xml_of_lane_from_edge_and_lane(edgeID, laneID):
    tree = ElementTree.parse('san_francisco.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@id='" + laneID + "']"):
        return int(name.attrib['index'])


def get_expected_index(edgeID, curr_lane_index):
    list_indexes = get_indexes_xml_from_edge(edgeID)
    if curr_lane_index != 0 and curr_lane_index in list_indexes:
        return curr_lane_index
    else:
        return 0


# * ********************************************************************************************************************************************************************* * #

def get_destination_xml(vecID):
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[len(list_edges) - 1]
    return None


# * ********************************************************************************************************************************************************************* * #

def get_depart_xml(vecID):
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[0]
    return None


# * ********************************************************************************************************************************************************************* * #

def get_distance_to_last(curr_edgeID, last_edgeID, curr_position):
    if curr_edgeID == last_edgeID:
        distance_tolast_edge = 0.0
    else:
        distance_tolast_edge = traci.simulation.getDistanceRoad(curr_edgeID, curr_position, last_edgeID, 0.0, True)

    return distance_tolast_edge


# * ********************************************************************************************************************************************************************* * #

def get_parking(laneID):
    return lane_to_parking_dictionary.get(laneID)


# * ********************************************************************************************************************************************************************* * #

def check_parking_aviability(parkingID):
    parking_capacity = int(traci.simulation.getParameter(parkingID, "parkingArea.capacity"))
    parking_occupancy = int(traci.simulation.getParameter(parkingID, "parkingArea.occupancy"))
    if parking_occupancy < parking_capacity:
        return True
    return False


def is_parking_already_setted(vecID, parkingID):
    tuple_of_stop_data = traci.vehicle.getStops(vecID, 1)
    for i in range(0, len(tuple_of_stop_data)):
        temp_stop_data = tuple_of_stop_data[i]
        if temp_stop_data.stoppingPlaceID == parkingID:
            return True
    return False


# * ********************************************************************************************************************************************************************* * #

def send_to_depart_xml(vecID):
    curr_route_list = traci.vehicle.getRoute(vecID)
    curr_last_edgeID = curr_route_list[len(curr_route_list) - 1]
    depart_edge_xml = get_depart_xml(vecID)
    if curr_last_edgeID != depart_edge_xml:
        traci.vehicle.changeTarget(vecID, depart_edge_xml)
        return True
    return False


# * ********************************************************************************************************************************************************************* * #

def get_start_coordinateXY_from_lane(destEdgeID, index):
    coordinateXY = traci.simulation.convert2D(destEdgeID, 0.0, index, False)
    return coordinateXY


def set_coordinate_lane_destination_xml(vecID, curr_lane_index):
    if vecID_to_dest_lane_position_dictionary.get(vecID) is None:
        coordinateXY = get_start_coordinateXY_from_lane(get_destination_xml(vecID), curr_lane_index)
        vecID_to_dest_lane_position_dictionary[vecID] = coordinateXY


# * ********************************************************************************************************************************************************************* * #

def get_available_lanes(vecID):
    # TUTTE LE CORSIE CHE HANNO UN PARCHEGGIO
    list_lane = list(lane_to_parking_dictionary.keys())

    curr_area = AREA_INIT
    dest_lane_coordinateXY = vecID_to_dest_lane_position_dictionary.get(vecID)

    limit_infX = dest_lane_coordinateXY[0] - curr_area / 2
    limit_infY = dest_lane_coordinateXY[1] - curr_area / 2
    limit_supX = dest_lane_coordinateXY[0] + curr_area / 2
    limit_supY = dest_lane_coordinateXY[1] + curr_area / 2

    idx = 0
    list_aviable_lane = []
    while idx in range(0, len(list_lane)):
        temp_lane = list_lane[idx]
        temp_edge = traci.lane.getEdgeID(temp_lane)
        temp_index = get_index_xml_of_lane_from_edge_and_lane(temp_edge, temp_lane)
        temp_coordinateXY = get_start_coordinateXY_from_lane(temp_edge, temp_index)
        if limit_infX <= temp_coordinateXY[0] <= limit_supX and limit_infY <= temp_coordinateXY[1] <= limit_supY:
            list_aviable_lane.append(temp_lane)
        idx += 1

        # ! Controllare questa porzione di codice
        # CONTROLLO SE STO USCENDO DAL WHILE E SE HO TROVATO ALMENO UNA LANE CON UN PARCHEGGIO NELL'AREA CORRENTE DI RICERCA
        if idx >= len(list_lane) and len(list_aviable_lane) == 0:
            if curr_area < 4000:
                curr_area = curr_area * 2
                # DEVO AGGIORNARE LE COORDINATE DEI LIMITE INFERIORE E SUPERIORE
                limit_infX = dest_lane_coordinateXY[0] - curr_area / 2
                limit_infY = dest_lane_coordinateXY[1] - curr_area / 2
                limit_supX = dest_lane_coordinateXY[0] + curr_area / 2
                limit_supY = dest_lane_coordinateXY[1] + curr_area / 2
                idx = 0
    return list_aviable_lane


# * ********************************************************************************************************************************************************************* * #

def get_ordred_parkings(list_aviable_lane):
    temp_dict = {}
    for lane in list_aviable_lane:
        parkingID = get_parking(lane)
        capacity = int(traci.simulation.getParameter(parkingID, "parkingArea.capacity"))
        temp_dict[parkingID] = capacity

    sort_dict = dict(reversed(sorted(temp_dict.items(), key=lambda item: item[1])))
    return list(sort_dict.keys())


# * ********************************************************************************************************************************************************************* * #

# (vecID, (list_ordred_parking, idx))), idx tiene traccia dell'ultimo parcheggio in cui abbiamo cercato posto libero
vecID_to_list_parking_index = {}


def calculate_parkings(vecID, curr_edgeID, last_edgeID, scenario):
    # Controllo se per questo veicolo non ho mai calcolato i parcheggi disponibili nell'area corrente di ricerca
    if vecID_to_list_parking_index.get(vecID) is None:

        # ! Commentato temporanemante
        # print(" Il veicolo", vecID, "sta calcolando i parcheggi disponibili nell'area corrente di ricerca...")
        # list_aviable_lane = get_available_lanes(vecID)
        # list_desc_parking = get_ordred_parkings(list_aviable_lane)
        # ! -------------------------

        if exists("./parkings/parks"+vecID+".txt"):
            # Read
            list_desc_parking = []
            with open("./parkings/parks"+vecID+".txt") as f:
                for line in f:
                    list_desc_parking.append(line.strip())
            vecID_to_list_parking_index[vecID] = (list_desc_parking, 0)
        else:
            print(" Il veicolo", vecID, "sta calcolando i parcheggi disponibili nell'area corrente di ricerca...")
            list_aviable_lane = get_available_lanes(vecID)
            list_desc_parking = get_ordred_parkings(list_aviable_lane)
            vecID_to_list_parking_index[vecID] = (list_desc_parking, 0)

            # Write
            fln = open("./parkings/parks"+vecID+".txt", "w")
            for elem in list_desc_parking:
                print(elem, file=fln)
            fln.close()

    # Recupero la lista dei parcheggi
    list_parking = vecID_to_list_parking_index.get(vecID)[0]
    idx = vecID_to_list_parking_index.get(vecID)[1]

    if idx <= len(list_parking) - 1:
        parkingID = list_parking[idx]

        # Aggiorno idx
        vecID_to_list_parking_index[vecID] = (list_parking, idx + 1)

        # Recupero l'edge dalla corsia associata al parcheggio
        lane_parking = traci.parkingarea.getLaneID(parkingID)
        edge_parking = traci.lane.getEdgeID(lane_parking)
        dest_edge = get_destination_xml(vecID)

        num_links = traci.lane.getLinkNumber(lane_parking)
        if num_links > 0:
            # Calcolo il nuovo percorso
            new_route = []

            if last_edgeID == dest_edge:
                route_stage = traci.simulation.findRoute(dest_edge, edge_parking)
                route_list = list(route_stage.edges)
                if curr_edgeID != dest_edge:
                    new_route.append(curr_edgeID)
                new_route += route_list
                last_route_map[vecID] = new_route
            else:
                old_route = last_route_map.get(vecID)
                if old_route is not None:
                    old_first = old_route[0]
                    if curr_edgeID == old_first:
                        # Caso 1:
                        new_route += old_route
                        route_stage = traci.simulation.findRoute(last_edgeID, edge_parking)
                        route_list = list(route_stage.edges)
                        route_list.pop(0)
                        new_route += route_list
                        last_route_map[vecID] = new_route
                    else:
                        # Caso 2
                        new_route = [curr_edgeID]
                        route_stage = traci.simulation.findRoute(last_edgeID, edge_parking)
                        route_list = list(route_stage.edges)
                        new_route += route_list
                        last_route_map[vecID] = new_route
                else:
                    raise "Non ho settato il vecchio route"
            try:
                # Setto il nuovo percorso calcolato
                traci.vehicle.setRoute(vecID, new_route)
            except traci.TraCIException as e:
                traci.vehicle.changeTarget(vecID, edge_parking)
                fln = open("exception.txt", "a")
                print("exception:", e, "veicolo:", vecID)
                fln.close()



# * ********************************************************************************************************************************************************************* * #

def routine(vecID, curr_laneID, curr_edgeID, last_edgeID, curr_route_list, last_laneID_excpected, expected_index, scenario):
    # Controllo se non sono arrivato al mio indirizzo di partenza, cioè destinazione xml oppure a una destinazione casuale
    if last_edgeID != get_depart_xml(vecID):

        # Assegno le coordinate (x, y) del suo indirizzo di destinazione xml
        set_coordinate_lane_destination_xml(vecID, expected_index)

        # Controllo se non mi sono mai parcheggiato
        if mappa.get(vecID) is None:
            # Controllo se nella lane di destinazione corrente c'è un parcheggio
            parkingID = get_parking(last_laneID_excpected)
            if parkingID is not None and check_parking_aviability(parkingID) is True and is_parking_already_setted(vecID, parkingID) is False:
                try:
                    # (900sec == 10min, 10800sec == 3hrs)
                    # ! random_parking_time = random.randint(900, 10800)
                    traci.vehicle.setParkingAreaStop(vecID, parkingID, 3)
                    mappa[vecID] = parkingID
                except traci.TraCIException as e:
                    calculate_parkings(vecID, curr_edgeID, last_edgeID, scenario)
            else:
                calculate_parkings(vecID, curr_edgeID, last_edgeID, scenario)


# * ********************************************************************************************************************************************************************* * #
def check_parking_position(vecID, vec_position, parkingID):
    start_park_pos = traci.parkingarea.getStartPos(parkingID)
    end_park_pos = traci.parkingarea.getEndPos(parkingID)
    if start_park_pos <= vec_position <= end_park_pos:
        return True
    return False


# vecID, (parking)
mappa = {}

last_route_map = {}


def run(strategia, scenario):
    set_lane_to_parking_dictionary()
    step = traci.simulation.getTime()  # step = 0.0

    while traci.simulation.getMinExpectedNumber() != 0:

        count = traci.vehicle.getIDCount()
        print("\n ###################### STEP: " + str(step) + " NUM_VEICOLI: " + str(count) + " STRATEGIA: " + strategia + " SCENARIO: " + scenario + " ######################")

        curr_vehicles_List = traci.vehicle.getIDList()
        for vecID in curr_vehicles_List:

            # Se il veicolo non è attualmente parcheggiato
            if traci.vehicle.isStoppedParking(vecID) is False:
                curr_route_list = traci.vehicle.getRoute(vecID)
                last_edgeID = curr_route_list[len(curr_route_list) - 1]
                curr_laneID = traci.vehicle.getLaneID(vecID)
                curr_position = traci.vehicle.getLanePosition(vecID)
                curr_speed = traci.vehicle.getSpeed(vecID)
                curr_acc = traci.vehicle.getAcceleration(vecID)
                curr_edgeID = traci.lane.getEdgeID(curr_laneID)
                curr_lane_index = traci.vehicle.getLaneIndex(vecID)
                leader_speed = traci.vehicle.getAllowedSpeed(vecID)
                max_decel = traci.vehicle.getDecel(vecID)
                distance_to_lastedge = float(get_distance_to_last(curr_edgeID, last_edgeID, curr_position))

                # Limite superiore della velocità nel prossimo step
                space_on_next_step = float(traci.vehicle.getFollowSpeed(vecID, curr_speed, distance_to_lastedge, leader_speed, max_decel))

                # myprintinfo(vecID, curr_laneID, curr_edgeID, curr_lane_index, last_edgeID, distance_to_lastedge, space_on_next_step, curr_route_list)

                # ___ ROUTINE ___ #
                if space_on_next_step >= distance_to_lastedge:
                    next_expected_index = get_expected_index(last_edgeID, curr_lane_index)
                    last_laneID_excpected = get_lane_xml_from_edge_and_index(last_edgeID, next_expected_index)
                    routine(vecID, curr_laneID, curr_edgeID, last_edgeID, curr_route_list, last_laneID_excpected, next_expected_index, scenario)
                else:
                    # Controllo se non ho trovato parcheggio a destinazione ed ho calcolato i parcheggi e non mi sono mai parcheggiato
                    if vecID_to_list_parking_index.get(vecID) is not None and mappa.get(vecID) is None:
                        # Controllo se trovo parcheggio mentre mi sto dirigendo verso quello più grande
                        parkingID = get_parking(curr_laneID)
                        if parkingID is not None and check_parking_aviability(parkingID) is True and is_parking_already_setted(vecID, parkingID) is False and check_parking_position(vecID, curr_position, parkingID) is True:
                            try:
                                # (900sec == 10min, 10800sec == 3hrs)
                                # ! random_parking_time = random.randint(900, 10800)
                                traci.vehicle.setParkingAreaStop(vecID, parkingID, 3)
                                mappa[vecID] = parkingID
                            except traci.TraCIException as e:
                                pass
            else:
                # Se il veicolo è attualmente parcheggiato
                send_to_depart_xml(vecID)

        traci.simulation.step()
        step = traci.simulation.getTime()  # step ++


# * ********************************************************************************************************************************************************************* * #

def main():
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumoBinary = checkBinary('sumo')
    # sumoBinary = 'sumo'

    fln = open("exception.txt", "w")
    fln.close()

    # STRATEGIA: strategia2, SCENARIO: 100%
    sumoCmd = [sumoBinary, "-c", "./strategia2_config/san_francisco_strategia2_100%.sumocfg", "--start"]
    traci.start(sumoCmd)
    run("strategia2", "100%")
    traci.close()

    # # STRATEGIA: strategia2, SCENARIO: 75%  # sumoCmd = [sumoBinary, "-c", "./strategia2_config/san_francisco_strategia2_75%.sumocfg", "--start"]  # traci.start(sumoCmd)  # run("strategia2", "75%")  # traci.close()  #  # # STRATEGIA: strategia2, SCENARIO: 50%  # sumoCmd = [sumoBinary, "-c", "./strategia2_config/san_francisco_strategia2_50%.sumocfg", "--start"]  # traci.start(sumoCmd)  # run("strategia2", "50%")  # traci.close()


if __name__ == "__main__":
    main()
