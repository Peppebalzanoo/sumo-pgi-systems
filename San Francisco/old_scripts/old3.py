import os
import sys
import traci
from os.path import exists
from sumolib import checkBinary
import xml.etree.ElementTree as ElementTree

AREA_INIT = 500

# * ********************************************************************************************************************************************************************* * #
# (vecID, parkingID)
vecID_to_parkingID_dictionary = {}

# (vecID, last_route[])
vecID_to_last_route_dictionary = {}

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
    tree = ElementTree.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml

# * ********************************************************************************************************************************************************************* * #

def get_lane_xml_from_edge_and_index(edgeID, index):
    tree = ElementTree.parse('../san_francisco.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']

def get_indexes_xml_from_edge(edgeID):
    tree = ElementTree.parse('../san_francisco.net.xml')
    root = tree.getroot()
    list_indexes = []
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        list_indexes.append(int(name.attrib['index']))
    return list_indexes

def get_index_xml_of_lane_from_edge_and_lane(edgeID, laneID):
    tree = ElementTree.parse('../san_francisco.net.xml')
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
    tree = ElementTree.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[len(list_edges) - 1]
    return None

# * ********************************************************************************************************************************************************************* * #

def get_depart_xml(vecID):
    tree = ElementTree.parse('../san_francisco.rou.xml')
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

def check_parking_position(vecID, vec_position, parkingID):
    start_park_pos = traci.parkingarea.getStartPos(parkingID)
    end_park_pos = traci.parkingarea.getEndPos(parkingID)
    if start_park_pos <= vec_position <= end_park_pos:
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

# (vecID, list_lanes[...])
vecID_to_available_lanes = {}

# def calculate_lanes_parking(list_temp, expected_index):
#     list_lane_parking = []
#     # Seleziono solo le lanes con indice consistente
#     for lane in list_temp:
#         tmp_edg = traci.lane.getEdgeID(lane)
#         max_idx = len(get_indexes_xml_from_edge(tmp_edg))-1
#         park_idx = get_index_xml_of_lane_from_edge_and_lane(tmp_edg, lane)
#         if expected_index == park_idx:
#             list_lane_parking.append(lane)
#         elif expected_index != park_idx and expected_index > max_idx:
#             if park_idx == 0:
#                 list_lane_parking.append(lane)
#     return list_lane_parking

# ? Si potrebbe prevedere di calcolare tutte le lanes presenti nell'area di ricerca
# ? Salvandole in una struttura contente infomazione anche del loro indice
# ? Così che non si debba di volta in volta ricalcolare le coordinate cartesiane
# ? Ma si farà solamente un confronto tra l'indice expceted_index e gli inidici delle corsie nella struttura
# ? Così da selezionare solo le lanes adatte alla situazione e quindi i parcheggi adatti

def get_available_lanes(vecID, expected_index):

    list_aviable_lane = []
    if vecID_to_available_lanes.get(vecID) is None:
        # Tutte le corsie che hanno un parcheggio
        list_lane_parking = list(lane_to_parking_dictionary.keys())

        curr_area = AREA_INIT
        dest_lane_coordinateXY = vecID_to_dest_lane_position_dictionary.get(vecID)

        limit_infX = dest_lane_coordinateXY[0] - curr_area / 2
        limit_infY = dest_lane_coordinateXY[1] - curr_area / 2
        limit_supX = dest_lane_coordinateXY[0] + curr_area / 2
        limit_supY = dest_lane_coordinateXY[1] + curr_area / 2

        idx = 0
        while idx in range(0, len(list_lane_parking)):
            temp_lane = list_lane_parking[idx]
            temp_edge = traci.lane.getEdgeID(temp_lane)
            temp_index = get_index_xml_of_lane_from_edge_and_lane(temp_edge, temp_lane)
            temp_coordinateXY = get_start_coordinateXY_from_lane(temp_edge, temp_index)
            if limit_infX <= temp_coordinateXY[0] <= limit_supX and limit_infY <= temp_coordinateXY[1] <= limit_supY:
                list_aviable_lane.append(temp_lane)
            idx += 1

            # ! Controllare questa porzione di codice ####################################################################################
            # Controllo se sto uscendo dal while e se non ho trovato nessuna lane con un parcheggio nell'area corrente di ricerca
            if idx >= len(list_lane_parking) and len(list_aviable_lane) == 0:
                if curr_area < 4000:
                    fln = open("../caso_strategia3.txt", "a")
                    print("VecID:", vecID, "nessun parcheggio nell'area corrente di ricerca:", curr_area)
                    fln.close()
                    curr_area = curr_area * 2
                    # Devo aggiornare le coordinate del limite inferiore e superiore
                    limit_infX = dest_lane_coordinateXY[0] - curr_area / 2
                    limit_infY = dest_lane_coordinateXY[1] - curr_area / 2
                    limit_supX = dest_lane_coordinateXY[0] + curr_area / 2
                    limit_supY = dest_lane_coordinateXY[1] + curr_area / 2
                    idx = 0
            # ! ####################################################################################

        # Salvo le lanes calcolate
        vecID_to_available_lanes[vecID] = list_aviable_lane
    else:
        # Se ho già calcolato le lanes disponibili
        list_aviable_lane = vecID_to_available_lanes.get(vecID)

    return list_aviable_lane

# * ********************************************************************************************************************************************************************* * #

def get_ordred_parkings(list_aviable_lane):
    temp_dict = {}
    for lane in list_aviable_lane:
        parkingID = get_parking(lane)
        capacity = int(traci.simulation.getParameter(parkingID, "parkingArea.capacity"))
        occupancy = int(traci.simulation.getParameter(parkingID, "parkingArea.occupancy"))
        temp_dict[parkingID] = capacity - occupancy

    sort_dict = dict(reversed(sorted(temp_dict.items(), key=lambda item: item[1])))
    return list(sort_dict.keys())

# * ********************************************************************************************************************************************************************* * #
def calculate_route_from_curr_edge_to_last_edge(vecID, curr_edgeID):
    # Recupero il precedente percorso salvato
    old_route = list(vecID_to_last_route_dictionary.get(vecID))
    trovato_curr_edge = False
    route_list1 = []
    for edg in old_route:
        if edg == curr_edgeID:
            trovato_curr_edge = True
            route_list1.append(edg)
        elif edg != curr_edgeID and trovato_curr_edge is True:
            route_list1.append(edg)

    return route_list1


def calculate_new_route(vecID, curr_edgeID, last_edgeID, edge_parking):
    new_route = []
    dest_edge_xml = get_destination_xml(vecID)
    # Il veicolo, nel prossimo step, raggiungerà la sua destinazione xml
    if last_edgeID == dest_edge_xml:
        route_stage1 = traci.simulation.findRoute(curr_edgeID, dest_edge_xml)
        route_list1 = list(route_stage1.edges)
        new_route += route_list1
        route_stage2 = traci.simulation.findRoute(dest_edge_xml, edge_parking)
        route_list2 = list(route_stage2.edges)
        route_list2.pop(0)
        new_route += route_list2

    else:   # Il veicolo, nel prossimo step, raggiungerà una destinazione
        # Recupero il percorso da curr_edge a last_edge
        route_list1 = calculate_route_from_curr_edge_to_last_edge(vecID, curr_edgeID)
        new_route += route_list1
        route_stage2 = traci.simulation.findRoute(last_edgeID, edge_parking)
        route_list2 = list(route_stage2.edges)
        route_list2.pop(0)
        new_route += route_list2

    # Salvo il percorso
    vecID_to_last_route_dictionary[vecID] = new_route
    return new_route

# * ********************************************************************************************************************************************************************* * #

# (vecID, (list_ordred_parking, idx))), idx tiene traccia dell'ultimo parcheggio in cui abbiamo cercato posto libero
vecID_to_list_parking_index = {}

def calculate_parkings(vecID, curr_edgeID, last_edgeID, last_laneID_excpected, expected_index):
    # Controllo se per questo veicolo non ho mai calcolato i parcheggi disponibili nell'area corrente di ricerca
    if vecID_to_list_parking_index.get(vecID) is None:
        # ! Commentato temporanemante ####################################################################################
        # print(" Il veicolo", vecID, "sta calcolando i parcheggi disponibili nell'area corrente di ricerca...")
        # list_aviable_lane = get_available_lanes(vecID, expected_index)
        # list_desc_parking = get_ordred_parkings(list_aviable_lane)
        # vecID_to_list_parking_index[vecID] = (list_desc_parking, 0)
        # ! ####################################################################################

        # # # ! Porzione di codice temporanea ####################################################################################
        if exists("./parks/parks"+vecID+".txt"):
            # Read
            list_desc_parking = []
            with open("./parks/parks"+vecID+".txt") as f:
                for line in f:
                    list_desc_parking.append(line.strip())
            vecID_to_list_parking_index[vecID] = (list_desc_parking, 0)
        else:
            print(" Il veicolo", vecID, "sta calcolando i parcheggi disponibili nell'area corrente di ricerca...")
            list_aviable_lane = get_available_lanes(vecID, expected_index)
            list_desc_parking = get_ordred_parkings(list_aviable_lane)
            vecID_to_list_parking_index[vecID] = (list_desc_parking, 0)

            # Write
            fln = open("./parks/parks"+vecID+".txt", "w")
            for elem in list_desc_parking:
                print(elem, file=fln)
            fln.close()
        # ! ####################################################################################


    # Recupero la lista dei parcheggi
    list_parking = list(vecID_to_list_parking_index.get(vecID)[0])

    # Recupero l'index associato al prossimo parcheggio che devo visistare
    idx = vecID_to_list_parking_index.get(vecID)[1]

    if idx <= len(list_parking) - 1:
        parkingID = list_parking[idx]

        # Recupero l'edge dalla corsia associata al parcheggio
        lane_parking = traci.parkingarea.getLaneID(parkingID)
        edge_parking = traci.lane.getEdgeID(lane_parking)
        # index_lane_parking = get_index_xml_of_lane_from_edge_and_lane(edge_parking, lane_parking)

        # Aggiorno idx
        vecID_to_list_parking_index[vecID] = (list_parking, idx + 1)

        new_route = calculate_new_route(vecID, curr_edgeID, last_edgeID, edge_parking)

        try:
            # Setto il nuovo percorso calcolato
            traci.vehicle.setRoute(vecID, new_route)
        except traci.TraCIException as e:
            traci.vehicle.changeTarget(vecID, edge_parking)
            fln = open("exception_strategia3.txt", "a")
            print("exception:", e, "veicolo:", vecID, file=fln)
            fln.close()

# * ********************************************************************************************************************************************************************* * #

def routine(vecID, curr_laneID, curr_edgeID, last_edgeID, curr_route_list, last_laneID_excpected, expected_index):
    # Controllo se non sono arrivato al mio indirizzo di partenza, cioè destinazione xml oppure a una destinazione casuale
    if last_edgeID != get_depart_xml(vecID):

        # Assegno le coordinate (x, y) del suo indirizzo di destinazione xml
        set_coordinate_lane_destination_xml(vecID, expected_index)

        # Controllo se non mi sono mai parcheggiato
        if vecID_to_parkingID_dictionary.get(vecID) is None:
            # Controllo se nella lane di destinazione corrente c'è un parcheggio
            parkingID = get_parking(last_laneID_excpected)
            if parkingID is not None and check_parking_aviability(parkingID) is True:
                try:
                    # (900sec == 10min, 10800sec == 3hrs)
                    # ! random_parking_time = random.randint(900, 10800)
                    if is_parking_already_setted(vecID, parkingID) is False:
                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 3)
                        # Salvo il parcheggio
                        vecID_to_parkingID_dictionary[vecID] = parkingID
                except traci.TraCIException as e:
                    calculate_parkings(vecID, curr_edgeID, last_edgeID, last_laneID_excpected, expected_index)
            else:
                # Se non c'è parcheggio OPPURE se non ci sono posti disponibili
                calculate_parkings(vecID, curr_edgeID, last_edgeID, last_laneID_excpected, expected_index)

# * ********************************************************************************************************************************************************************* * #

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

                # ___ ROUTINE ___ #
                if space_on_next_step >= distance_to_lastedge:
                    next_expected_index = get_expected_index(last_edgeID, curr_lane_index)
                    last_laneID_excpected = get_lane_xml_from_edge_and_index(last_edgeID, next_expected_index)
                    routine(vecID, curr_laneID, curr_edgeID, last_edgeID, curr_route_list, last_laneID_excpected, next_expected_index)
                else:
                    # Controllo se non ho trovato parcheggio a destinazione xml ed ho calcolato i parcheggi e non mi sono mai parcheggiato
                    if vecID_to_list_parking_index.get(vecID) is not None and vecID_to_parkingID_dictionary.get(vecID) is None:
                        # Controllo se trovo parcheggio mentre mi sto dirigendo verso quello più grande
                        parkingID = get_parking(curr_laneID)
                        if parkingID is not None and check_parking_aviability(parkingID) is True and check_parking_position(vecID, curr_position, parkingID) is True:
                            try:
                                # (900sec == 10min, 10800sec == 3hrs)
                                # ! random_parking_time = random.randint(900, 10800)

                                if is_parking_already_setted(vecID, parkingID) is False:
                                    traci.vehicle.setParkingAreaStop(vecID, parkingID, 3)
                                    # Salvo il parcheggio
                                    vecID_to_parkingID_dictionary[vecID] = parkingID

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
    # sumoBinary = checkBinary('sumo-gui')

    fln = open("exception_strategia3.txt", "w")
    fln.close()
    fln = open("../caso_strategia3.txt", "w")
    fln.close()

    # STRATEGIA: strategia3, SCENARIO: 100%
    sumoCmd = [sumoBinary, "-c", "./strategia3_config/san_francisco_strategia3_100%.sumocfg", "--start"]
    traci.start(sumoCmd)
    run("strategia3", "100%")
    traci.close()

# * ********************************************************************************************************************************************************************* * #

if __name__ == "__main__":
    main()
