import os
import sys
import traci
import random
from sumolib import checkBinary
import xml.etree.ElementTree as ElementTree

LATO_INIT = 500
TIME = 600

# * ********************************************************************************************************************************************************************* * #
# (vecID, parkingID)
vecID_to_parked_dictionary = {}

# (vecID, last_route[..])
vecID_to_last_route_dictionary = {}

# (vecID, coordinateXY_lane_dest)
vecID_to_dest_lane_position_dictionary = {}

# * ********************************************************************************************************************************************************************* * #

# (laneID, parkingID)
lane_to_parking_dictionary = {}


def set_lane_to_parking_dictionary():
    parkingIDs_list = traci.parkingarea.getIDList()
    for parkingID in parkingIDs_list:
        curr_laneID = traci.parkingarea.getLaneID(parkingID)
        lane_to_parking_dictionary[curr_laneID] = parkingID


def get_parkings_and_index_from_edge(edgeID):
    list_of_tuple_parkID_index = []
    list_lanes = get_list_lanes_xml_form_edge(edgeID)
    for laneID in list_lanes:
        parkID = lane_to_parking_dictionary.get(laneID)
        if parkID is not None:
            park_index = get_index_xml_of_lane_from_edge_and_lane(edgeID, laneID)
            list_of_tuple_parkID_index.append((parkID, park_index))
    return list_of_tuple_parkID_index


def sort_parking_by_distance_routine(list_of_tuple_parkID_index, curr_edgeID, vec_position, last_edgeID):
    list_of_tuple_parkID_index_dist = []
    for curr_tuple in list_of_tuple_parkID_index:
        parkID = curr_tuple[0]
        park_index = traci.parkingarea.getStartPos(parkID)
        start_parkID = traci.parkingarea.getStartPos(parkID)
        dist = traci.simulation.getDistanceRoad(curr_edgeID, vec_position, last_edgeID, start_parkID, True)
        list_of_tuple_parkID_index_dist.append((parkID, park_index, dist))
    return sorted(list_of_tuple_parkID_index_dist, key=lambda tupl: tupl[2])
# * ********************************************************************************************************************************************************************* * #


def get_vehicle_from_xml():
    tree = ElementTree.parse("san_francisco.rou.xml")
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


def get_list_lanes_xml_form_edge(edgeID):
    tree = ElementTree.parse("san_francisco.net.xml")
    root = tree.getroot()
    list_lanes = []
    for lane in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        laneID = lane.attrib["id"]
        list_lanes.append(laneID)
    return list_lanes


def get_lane_xml_from_edge_and_index(edgeID, index):
    tree = ElementTree.parse("san_francisco.net.xml")
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


def get_indexes_xml_from_edge(edgeID):
    tree = ElementTree.parse("san_francisco.net.xml")
    root = tree.getroot()
    list_indexes = []
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        list_indexes.append(int(name.attrib['index']))
    return list_indexes


def get_index_xml_of_lane_from_edge_and_lane(edgeID, laneID):
    tree = ElementTree.parse("san_francisco.net.xml")
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@id='" + laneID + "']"):
        return int(name.attrib['index'])


def get_expected_index(edgeID, curr_lane_index):
    list_indexes = get_indexes_xml_from_edge(edgeID)
    if curr_lane_index != 0 and curr_lane_index in list_indexes:
        return curr_lane_index
    else:
        return 0


def get_destination_xml(vecID):
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[len(list_edges) - 1]
    return None


def get_depart_xml(vecID):
    tree = ElementTree.parse("san_francisco.rou.xml")
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

def check_parking_aviability(parkingID):
    parking_capacity = int(traci.simulation.getParameter(parkingID, "parkingArea.capacity"))
    parking_occupancy = int(traci.simulation.getParameter(parkingID, "parkingArea.occupancy"))
    if parking_occupancy < parking_capacity:
        return True
    return False


def check_stop_already_set(vecID, parkingID):
    tuple_of_stop_data = traci.vehicle.getStops(vecID)
    for i in range(0, len(tuple_of_stop_data)):
        curr_stop_data = tuple_of_stop_data[i]
        if curr_stop_data.stoppingPlaceID == parkingID:
            return True
    return False

def clear_others_stops(vecID, new_parkingID):
    tuple_of_stop_data = traci.vehicle.getStops(vecID)
    for i in range(1, len(tuple_of_stop_data)):
        curr_stop_data = tuple_of_stop_data[i]
        traci.vehicle.replaceStop(vecID, i, "")
        fln = open("log_strategia1.txt", "a")
        print("[INFO clear_stops()]: Il veicolo:", vecID, "HA RIMOSSO:", curr_stop_data.stoppingPlaceID, "perchè HA SETTATO:", new_parkingID, file=fln)
        fln.close()

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

def get_start_coordinate_from_destination_lane(destEdgeID, index):
    coordinateXY = traci.simulation.convert2D(destEdgeID, 0.0, index, False)
    return coordinateXY


def set_coordinate(vecID, curr_lane_index):
    coordinateXY = get_start_coordinate_from_destination_lane(get_destination_xml(vecID), curr_lane_index)
    vecID_to_dest_lane_position_dictionary[vecID] = coordinateXY


def check_coordinate_is_not_already_set(vecID):
    if vecID_to_dest_lane_position_dictionary.get(vecID) is None:
        return True
    return False


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


def calculate_new_route(vecID, curr_edgeID, last_edgeID, random_edgeID):
    new_route = []
    dest_edge_xml = get_destination_xml(vecID)
    # Il veicolo, nel prossimo step, raggiungerà la sua destinazione xml
    if last_edgeID == dest_edge_xml:
        route_stage1 = traci.simulation.findRoute(curr_edgeID, dest_edge_xml)
        route_list1 = list(route_stage1.edges)
        new_route += route_list1
        route_stage2 = traci.simulation.findRoute(dest_edge_xml, random_edgeID)
        route_list2 = list(route_stage2.edges)
        route_list2.pop(0)
        new_route += route_list2

    else:  # Il veicolo, nel prossimo step, raggiungerà una destinazione
        # Recupero il percorso da curr_edge a last_edge
        route_list1 = calculate_route_from_curr_edge_to_last_edge(vecID, curr_edgeID)
        new_route += route_list1
        route_stage2 = traci.simulation.findRoute(last_edgeID, random_edgeID)
        route_list2 = list(route_stage2.edges)
        route_list2.pop(0)
        new_route += route_list2

    # Salvo il percorso
    vecID_to_last_route_dictionary[vecID] = new_route
    return new_route


# * ********************************************************************************************************************************************************************* * #

# (vecID: (lato, counter) )
vecID_to_lato_counter_dictionary = {}


def load_vecID_to_lato_counter_dictionary(val):
    for vecID in get_vehicle_from_xml():
        vecID_to_lato_counter_dictionary[vecID] = (val, 0)


def update_vecID_to_lato_counter_dictionary(vecID, area, counter):
    if vecID_to_lato_counter_dictionary.get(vecID)[0] != area or vecID_to_lato_counter_dictionary.get(vecID)[1] != counter:
        vecID_to_lato_counter_dictionary[vecID] = (area, counter)


def reset_vecID_to_lato_counter_dictionary(vecID):
    if vecID_to_lato_counter_dictionary.get(vecID)[0] != LATO_INIT or vecID_to_lato_counter_dictionary.get(vecID)[1] != 0:
        vecID_to_lato_counter_dictionary[vecID] = (LATO_INIT, 0)



def get_parking(laneID):
    return lane_to_parking_dictionary.get(laneID)

# * ********************************************************************************************************************************************************************* * #

# (vecID, (counter_step, started))
vec_to_searchtime_started_dictionary = {}


def load_vec_to_searchtime_started_dictionary():
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle"):
        vecID = elem.attrib['id']
        vec_to_searchtime_started_dictionary[vecID] = (0, False)


def update_vec_to_searchtime_started_dictionary(vecID, counter, started):
    vec_to_searchtime_started_dictionary[vecID] = (counter, started)


def reset_vec_to_searchtime_started_dictionary(vecID):
    if vec_to_searchtime_started_dictionary.get(vecID)[0] != 0 or vec_to_searchtime_started_dictionary.get(vecID)[1] is not False:
        vec_to_searchtime_started_dictionary[vecID] = (0, False)


def check_time(vecID, count):
    if count == TIME:
        if vecID_to_lato_counter_dictionary.get(vecID)[1] < 3:
            update_vecID_to_lato_counter_dictionary(vecID, vecID_to_lato_counter_dictionary.get(vecID)[0] * 2, vecID_to_lato_counter_dictionary.get(vecID)[1] + 1)
            update_vec_to_searchtime_started_dictionary(vecID, 0, True)
        else:
            send_to_depart_xml(vecID)
            reset_vecID_to_lato_counter_dictionary(vecID)
            reset_vec_to_searchtime_started_dictionary(vecID)

# * ********************************************************************************************************************************************************************* * #

def get_available_edges(vecID, curr_edgeID, expected_index, last_edgeID, list_tuple_links):
    tupla_lato_counter = vecID_to_lato_counter_dictionary.get(vecID)
    curr_lato = tupla_lato_counter[0]
    dest_lane_positionXY = vecID_to_dest_lane_position_dictionary.get(vecID)
    limit_infX = dest_lane_positionXY[0] - curr_lato / 2
    limit_infY = dest_lane_positionXY[1] - curr_lato / 2
    limit_supX = dest_lane_positionXY[0] + curr_lato / 2
    limit_supY = dest_lane_positionXY[1] + curr_lato / 2

    list_available = []
    for i in range(0, len(list_tuple_links)):
        temp_tuple = list_tuple_links[i]
        temp_lane = temp_tuple[0]
        temp_edge = traci.lane.getEdgeID(temp_lane)

        if temp_edge != curr_edgeID and temp_edge != last_edgeID:
            temp_index = get_expected_index(temp_edge, expected_index)
            curr_coordinateXY = get_start_coordinate_from_destination_lane(temp_edge, temp_index)

            if limit_infX <= curr_coordinateXY[0] <= limit_supX and limit_infY <= curr_coordinateXY[1] <= limit_supY:
                list_available.append(temp_edge)

    return list_available

# * ********************************************************************************************************************************************************************* * #

def search_random_edge_for_parking(vecID, curr_edgeID, curr_laneID, expected_index, last_edgeID, last_laneID_excpected, scenario):
    # Notifico che da questo momento il veicolo sta cercando parcheggio
    update_vec_to_searchtime_started_dictionary(vecID, vec_to_searchtime_started_dictionary.get(vecID)[0], True)

    num_links = traci.lane.getLinkNumber(last_laneID_excpected)
    list_tuple_links = traci.lane.getLinks(last_laneID_excpected)  # Una lista di tuple

    if num_links >= 1:
        exit_cond = False
        while vecID_to_lato_counter_dictionary.get(vecID)[1] < 3 and exit_cond is False:
            list_available_edgs = get_available_edges(vecID, curr_edgeID, expected_index, last_edgeID, list_tuple_links)

            if len(list_available_edgs) > 0:
                random_edgeID = random.choice(list_available_edgs)

                # Calcolo il nuovo percorso
                new_route = calculate_new_route(vecID, curr_edgeID, last_edgeID, random_edgeID)

                try:
                    # Setto il nuovo percorso calcolato
                    traci.vehicle.setRoute(vecID, new_route)

                except traci.TraCIException as e:
                    traci.vehicle.changeTarget(vecID, random_edgeID)
                    fln = open("log_strategia1.txt", "a")
                    print("[EXCEPETION set_route()]: Il veicolo", vecID, "HA SOLLEVATO", e, file=fln)
                    fln.close()

                exit_cond = True

            else:
                update_vecID_to_lato_counter_dictionary(vecID, vecID_to_lato_counter_dictionary.get(vecID)[0] * 2, vecID_to_lato_counter_dictionary.get(vecID)[1] + 1)
                update_vec_to_searchtime_started_dictionary(vecID, 0, True)

        # Controllo se sono uscito perché ho aumentato la superficie di ricerca al massimo
        if vecID_to_lato_counter_dictionary.get(vecID)[1] >= 3 and exit_cond is False:
            send_to_depart_xml(vecID)
            reset_vecID_to_lato_counter_dictionary(vecID)
            reset_vec_to_searchtime_started_dictionary(vecID)
    else:
        # Non c'è nessuna strada collegata a quella corrente
        file = open("log_strategia1.txt", "a")
        print("[INFO search()]: Il veicolo", vecID, "è uscito perchè NON CI SONO PIU' STRADE FISICAMENTE PERCORRIBILI", file=file)
        file.close()


# * ********************************************************************************************************************************************************************* * #

def routine(vecID, curr_edgeID, curr_laneID, last_edgeID, last_laneID_excpected, expected_index, scenario):
    # Controllo se non sono arrivato al mio indirizzo di partenza, cioè destinazione xml oppure a una destinazione casuale
    if last_edgeID != get_depart_xml(vecID):

        # Assegno al veicolo le coordinate (x, y) del suo indirizzo di destinazione xml
        if check_coordinate_is_not_already_set(vecID) is True:
            set_coordinate(vecID, expected_index)

        # Recupero la lista di parcheggi nella strada di destinazione
        list_of_tuple_parkID_index = get_parkings_and_index_from_edge(last_edgeID)
        list_of_tuple_parkID_index_dist = sort_parking_by_distance_routine(list_of_tuple_parkID_index, curr_edgeID, traci.vehicle.getLanePosition(vecID), last_edgeID)

        # Controllo se non mi sono mai parcheggiato e se ci sono parcheggi nella strada di destinazione
        if vecID_to_parked_dictionary.get(vecID) is None and len(list_of_tuple_parkID_index_dist) > 0:
            idx = 0
            setted = False
            while idx <= len(list_of_tuple_parkID_index_dist) - 1 and setted is False:

                curr_tuple_parkID_index_dist = list_of_tuple_parkID_index_dist[idx]
                parkingID = curr_tuple_parkID_index_dist[0]
                parking_index = curr_tuple_parkID_index_dist[1]

                # Controllo la disponibilità di posti effettivamente liberi prima dello step che mi permette di arrivare a destinazione
                if check_parking_aviability(parkingID) is True:

                    try:
                        # (900sec == 10min, 10800sec == 3hrs)
                        random_parking_time = random.randint(900, 10800)
                        if check_stop_already_set(vecID, parkingID) is False:
                            traci.vehicle.setParkingAreaStop(vecID, parkingID, random_parking_time)

                            # Controllo ed elimino le fermate settate prima di quest'ultima
                            clear_others_stops(vecID, parkingID)

                            if last_edgeID == get_destination_xml(vecID):
                                fln = open("log_strategia1.txt", "a")
                                print("[INFO routine()]: Il veicolo", vecID, "HA SETTATO LA FERMATA A", parkingID, "nella strada di destinazione XML", file=fln)
                                fln.close()
                            else:
                                fln = open("log_strategia1.txt", "a")
                                print("[INFO routine()]: Il veicolo", vecID, "HA SETTATO LA FERMATA A", parkingID, "nella strada dove è stato indirizzato", parkingID, file=fln)
                                fln.close()

                            reset_vec_to_searchtime_started_dictionary(vecID)

                            # Forzo l'uscita dal for per evitare che venga settata qualche altra fermata
                            setted = True

                    except traci.TraCIException as e:
                        pass
                else:
                    fln = open("log_strategia1.txt", "a")
                    print("[INFO routine()]: Il veicolo", vecID, "NON E' RIUSCITO A PARCHEGGIARE IN:", parkingID, "PER INDISPONIBILITA' DI POSTI LIBERI", file=fln)
                    fln.close()

                idx += 1

            # Se non sono riuscito a parcheggiarmi nei parcheggi presenti nella strada di destinazione
            if setted is False:
                search_random_edge_for_parking(vecID, curr_edgeID, curr_laneID, expected_index, last_edgeID, last_laneID_excpected, scenario)
        else:
            # Controllo se non mi sono mai parcheggiato e non ci sono parcheggi nella strada di destinazione corrente
            if vecID_to_parked_dictionary.get(vecID) is None and len(list_of_tuple_parkID_index) <= 0:
                # Se non ci sono parcheggi nella strada di destinazione
                search_random_edge_for_parking(vecID, curr_edgeID, curr_laneID, expected_index, last_edgeID, last_laneID_excpected, scenario)


# * ********************************************************************************************************************************************************************* * #

def run(strategia, scenario):
    load_vecID_to_lato_counter_dictionary(LATO_INIT)
    set_lane_to_parking_dictionary()
    load_vec_to_searchtime_started_dictionary()

    step = traci.simulation.getTime()  # step = 0.0

    while traci.simulation.getMinExpectedNumber() != 0:
        count = traci.vehicle.getIDCount()

        print("\n ###################### STEP: " + str(step) + " NUM_VEICOLI: " + str(count) + " STRATEGIA: " + strategia + " SCENARIO: " + scenario + " ######################")

        curr_vehicles_List = traci.vehicle.getIDList()

        for vecID in curr_vehicles_List:

            # Se il veicolo non è attualmente parcheggiato
            if traci.vehicle.isStoppedParking(vecID) is False:

                # Controllo se il veicolo ha iniziato la ricerca del parcheggio
                started_research = vec_to_searchtime_started_dictionary.get(vecID)[1]
                if started_research is True:
                    count_timeslice = vec_to_searchtime_started_dictionary.get(vecID)[0] + 1
                    update_vec_to_searchtime_started_dictionary(vecID, count_timeslice, True)
                    check_time(vecID, count_timeslice)

                curr_route_list = traci.vehicle.getRoute(vecID)
                last_edgeID = curr_route_list[len(curr_route_list) - 1]
                curr_laneID = traci.vehicle.getLaneID(vecID)
                curr_position = traci.vehicle.getLanePosition(vecID)
                curr_speed = traci.vehicle.getSpeed(vecID)
                curr_edgeID = traci.lane.getEdgeID(curr_laneID)
                curr_lane_index = traci.vehicle.getLaneIndex(vecID)
                leader_speed = traci.vehicle.getAllowedSpeed(vecID)
                max_decel = traci.vehicle.getDecel(vecID)
                distance_to_lastedge = float(get_distance_to_last(curr_edgeID, last_edgeID, curr_position))

                # Limite superiore della velocità nel prossimo step
                space_on_next_step = float(traci.vehicle.getFollowSpeed(vecID, curr_speed, distance_to_lastedge, leader_speed, max_decel))

                # Se il veicolo nel prossimo step arriverà a una destinazione
                if space_on_next_step >= distance_to_lastedge:
                    next_expected_index = get_expected_index(last_edgeID, curr_lane_index)
                    last_laneID_excpected = get_lane_xml_from_edge_and_index(last_edgeID, next_expected_index)

                    routine(vecID, curr_edgeID, curr_laneID, last_edgeID, last_laneID_excpected, next_expected_index, scenario)
            else:
                # Se il veicolo è attualmente parcheggiato
                send_to_depart_xml(vecID)

                # Setto che il veicolo ha parcheggiato
                vecID_to_parked_dictionary[vecID] = True

                reset_vecID_to_lato_counter_dictionary(vecID)

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

    fln = open("log_strategia1.txt", "w")
    fln.close()

    # STRATEGIA: strategia1, SCENARIO: 100%
    # sumoCmd = [sumoBinary, "-c", "./strategia1_config/san_francisco_strategia1_100%.sumocfg", "--start"]
    # traci.start(sumoCmd)
    # run("strategia1", "100%")
    # traci.close()

    # STRATEGIA: strategia1, SCENARIO: 75%
    # sumoCmd = [sumoBinary, "-c", "./strategia1_config/san_francisco_strategia1_75%.sumocfg", "--start"]
    # traci.start(sumoCmd)
    # run("strategia1", "75%")
    # traci.close()

    # STRATEGIA: strategia1, SCENARIO: 50%
    sumoCmd = [sumoBinary, "-c", "./strategia1_config/san_francisco_strategia1_50%.sumocfg", "--start"]
    traci.start(sumoCmd)
    run("strategia1", "50%")
    traci.close()


# * ********************************************************************************************************************************************************************* * #

if __name__ == "__main__":
    main()
