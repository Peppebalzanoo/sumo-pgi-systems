import os
import random
import sys
import traci
from os.path import exists
from sumolib import checkBinary
import xml.etree.ElementTree as ElementTree

LATO_INIT = 500

# * ********************************************************************************************************************************************************************* * #
# (vecID: parkingID)
vecID_to_parked_dictionary = {}

# (vecID: last_route[..])
vecID_to_last_route_dictionary = {}

# (vecID:, coordinateXY_lane_dest)
vecID_to_dest_lane_position_dictionary = {}

# * ********************************************************************************************************************************************************************* * #

# (laneID: parkingID)
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

def sort_parking_by_distance_current(list_of_tuple_parkID_index, curr_edgeID, vec_position):
    list_of_tuple_parkID_index_dist = []
    for curr_tuple in list_of_tuple_parkID_index:
        parkID = curr_tuple[0]
        park_index = curr_tuple[1]
        start_parkID = traci.parkingarea.getStartPos(parkID)
        dist = traci.simulation.getDistanceRoad(curr_edgeID, vec_position, curr_edgeID, start_parkID, True)
        list_of_tuple_parkID_index_dist.append((parkID, park_index, dist))
    return sorted(list_of_tuple_parkID_index_dist, key=lambda tupl: tupl[2])


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
        vec_xml = elem.attrib["id"]
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


def get_list_indexes_xml_from_edge(edgeID):
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
    list_indexes = get_list_indexes_xml_from_edge(edgeID)
    if curr_lane_index != 0 and curr_lane_index in list_indexes:
        return curr_lane_index
    else:
        return 0


def get_destination_xml(vecID):
    tree = ElementTree.parse("san_francisco.rou.xml")
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

def check_parking_position(vecID, vec_position, parkingID):
    start_park_pos = traci.parkingarea.getStartPos(parkingID)
    end_park_pos = traci.parkingarea.getEndPos(parkingID)
    if start_park_pos <= vec_position <= end_park_pos:
        return True
    return False

def check_stop_already_set(vecID, parkingID):
    tuple_of_stop_data = traci.vehicle.getStops(vecID)
    for i in range(0, len(tuple_of_stop_data)):
        curr_stop_data = tuple_of_stop_data[i]
        if curr_stop_data.stoppingPlaceID == parkingID:
            return True
    return False

def clear_stop(vecID, parkingID):
    tuple_of_stop_data = traci.vehicle.getStops(vecID)
    trovato = False
    i = 0
    while i in range(0, len(tuple_of_stop_data)) and trovato is False:
        curr_stop_data = tuple_of_stop_data[i]
        if curr_stop_data.stoppingPlaceID == parkingID:
            traci.vehicle.replaceStop(vecID, i, "")
            trovato = True
            fln = open("log_strategia2.txt", "a")
            print("[INFO clear_stops()]: Il veicolo:", vecID, "HA RIMOSSO:", curr_stop_data.stoppingPlaceID, "perchè NON HA PIU' POSTI DISPONIBILI", file=fln)
            fln.close()

def clear_others_stops(vecID, new_parkingID):
    tuple_of_stop_data = traci.vehicle.getStops(vecID)
    for i in range(1, len(tuple_of_stop_data)):
        curr_stop_data = tuple_of_stop_data[i]
        traci.vehicle.replaceStop(vecID, i, "")
        fln = open("log_strategia2.txt", "a")
        print("[INFO clear_others_stops()]: Il veicolo:", vecID, "HA RIMOSSO:", curr_stop_data.stoppingPlaceID, "perchè HA SETTATO:", new_parkingID, file=fln)
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

def get_start_coordinateXY_from_lane(destEdgeID, index):
    coordinateXY = traci.simulation.convert2D(destEdgeID, 0.0, index, False)
    return coordinateXY

def set_coordinate(vecID, curr_lane_index):
    coordinateXY = get_start_coordinateXY_from_lane(get_destination_xml(vecID), curr_lane_index)
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

    else:  # Il veicolo, nel prossimo step, raggiungerà una destinazione
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

# (vecID, list_lanes[...])
vecID_to_available_lanes = {}

def get_available_lanes(vecID):
    list_aviable_lane = []

    if vecID_to_available_lanes.get(vecID) is None:
        # Tutte le corsie che hanno un parcheggio
        list_lane_parking = list(lane_to_parking_dictionary.keys())

        curr_lato = LATO_INIT
        dest_lane_coordinateXY = vecID_to_dest_lane_position_dictionary.get(vecID)

        limit_infX = dest_lane_coordinateXY[0] - curr_lato / 2
        limit_infY = dest_lane_coordinateXY[1] - curr_lato / 2
        limit_supX = dest_lane_coordinateXY[0] + curr_lato / 2
        limit_supY = dest_lane_coordinateXY[1] + curr_lato / 2

        idx = 0
        while idx in range(0, len(list_lane_parking)):
            temp_lane = list_lane_parking[idx]
            temp_edge = traci.lane.getEdgeID(temp_lane)
            temp_index = get_index_xml_of_lane_from_edge_and_lane(temp_edge, temp_lane)
            temp_coordinateXY = get_start_coordinateXY_from_lane(temp_edge, temp_index)
            if limit_infX <= temp_coordinateXY[0] <= limit_supX and limit_infY <= temp_coordinateXY[1] <= limit_supY:
                list_aviable_lane.append(temp_lane)
            idx += 1

            # Controllo se sto uscendo dal while e se non ho trovato nessuna lane con un parcheggio nell'area corrente di ricerca
            if idx >= len(list_lane_parking) and len(list_aviable_lane) == 0:
                if curr_lato < 4000:
                    fln = open("log_strategia2.txt", "a")
                    print("[#CASO#]", vecID, "non ha trovato nessun parcheggio nell'area corrente di ricerca:", curr_lato)
                    fln.close()
                    curr_lato = curr_lato * 2
                    # Devo aggiornare le coordinate del limite inferiore e superiore
                    limit_infX = dest_lane_coordinateXY[0] - curr_lato / 2
                    limit_infY = dest_lane_coordinateXY[1] - curr_lato / 2
                    limit_supX = dest_lane_coordinateXY[0] + curr_lato / 2
                    limit_supY = dest_lane_coordinateXY[1] + curr_lato / 2
                    idx = 0

        # Salvo le lanes calcolate
        vecID_to_available_lanes[vecID] = list_aviable_lane
    else:
        # Se ho già calcolato le lanes disponibili
        list_aviable_lane = vecID_to_available_lanes.get(vecID)

    return list_aviable_lane

# * ********************************************************************************************************************************************************************* * #

# (vecID : (list_ordred_parking[...], index)))

vecID_to_list_parking_index = {}

def get_ordred_parkings(list_aviable_lane):
    temp_dict = {}
    for lane in list_aviable_lane:
        parkingID = lane_to_parking_dictionary.get(lane)
        capacity = int(traci.simulation.getParameter(parkingID, "parkingArea.capacity"))
        temp_dict[parkingID] = capacity

    sort_dict = dict(reversed(sorted(temp_dict.items(), key=lambda item: item[1])))
    return list(sort_dict.keys())


def calculate_parkings(vecID):
    # Controllo se per questo veicolo non ho mai calcolato/caricato i parcheggi
    if vecID_to_list_parking_index.get(vecID) is None:
        # Controllo se i parcheggi sono salvati nel file
        if exists("./strategia2_config/parkings/parks" + vecID + ".txt"):
            list_desc_parking = []
            # Recupero i parcheggi
            with open("./strategia2_config/parkings/parks" + vecID + ".txt") as f:
                for line in f:
                    list_desc_parking.append(line.strip())
            # Setto i parcheggi nel dizionario
            vecID_to_list_parking_index[vecID] = (list_desc_parking, 0)
        else:
            # Calcolo i parcheggi
            print(" Il veicolo", vecID, "sta calcolando i parcheggi disponibili nell'area corrente di ricerca...")
            list_aviable_lane = get_available_lanes(vecID)
            list_desc_parking = get_ordred_parkings(list_aviable_lane)

            # Setto i parcheggi nel dizionario
            vecID_to_list_parking_index[vecID] = (list_desc_parking, 0)

            # Salvo i parcheggi nel file
            fln = open("./strategia2_config/parkings/parks" + vecID + ".txt", "w")
            for elem in list_desc_parking:
                print(elem, file=fln)
            fln.close()

# * ********************************************************************************************************************************************************************* * #

def set_route_to_parking_edge(vecID, curr_edgeID, last_edgeID):
    # Recupero la lista dei parcheggi
    list_parking = list(vecID_to_list_parking_index.get(vecID)[0])

    # Recupero l'index associato al prossimo parcheggio che devo visistare
    idx = vecID_to_list_parking_index.get(vecID)[1]

    if idx <= len(list_parking) - 1:
        parkingID = list_parking[idx]

        # Recupero l'edge dalla corsia associata al parcheggio
        lane_parking = traci.parkingarea.getLaneID(parkingID)
        edge_parking = traci.lane.getEdgeID(lane_parking)

        # Aggiorno idx
        vecID_to_list_parking_index[vecID] = (list_parking, idx + 1)

        new_route = calculate_new_route(vecID, curr_edgeID, last_edgeID, edge_parking)

        fln = open("log_strategia2.txt", "a")
        print("[INFO set_route()]: Il veicolo", vecID, "SI STA DIRIGENDO VERSO IL PROSSIMO PIÙ GRANDE CON INDICE:", idx, file=fln)
        fln.close()

        try:
            # Setto il nuovo percorso calcolato
            traci.vehicle.setRoute(vecID, new_route)
        except traci.TraCIException as e:
            traci.vehicle.changeTarget(vecID, edge_parking)
            fln = open("log_strategia2.txt", "a")
            print("[EXCEPETION set_route()]: Il veicolo", vecID, "HA SOLLEVATO", e, file=fln)
            fln.close()

# * ********************************************************************************************************************************************************************* * #

def set_parking_on_current_edge(vecID, curr_edgeID, curr_position, curr_lane_index):
    # Recupero i parcheggi nella strada corrente
    list_of_tuple_parkID_index = get_parkings_and_index_from_edge(curr_edgeID)
    list_of_tuple_parkID_index_dist = sort_parking_by_distance_current(list_of_tuple_parkID_index, curr_edgeID, curr_position)


    if len(list_of_tuple_parkID_index_dist) > 0:
        idx = 0
        setted = False

        while idx <= len(list_of_tuple_parkID_index_dist) - 1 and setted is False:

            curr_tuple_parkID_index_dist = list_of_tuple_parkID_index_dist[idx]
            parkingID = curr_tuple_parkID_index_dist[0]
            parking_index = curr_tuple_parkID_index_dist[1]

            # Controllo la disponibilità di posti effettivamente liberi e la posizione
            if check_parking_aviability(parkingID) is True and check_parking_position(vecID, curr_position, parkingID) is True:

                # Controllo se devo far cambiare lane al veicolo
                if curr_lane_index != parking_index:
                    traci.vehicle.changeLane(vecID, parking_index, 1)

                try:
                    # (900sec == 10min, 10800sec == 3hrs)
                    random_parking_time = random.randint(900, 10800)
                    if check_stop_already_set(vecID, parkingID) is False:
                        traci.vehicle.setParkingAreaStop(vecID, parkingID, random_parking_time)

                        # Controllo ed elimino le fermate settate prima di quest'ultima
                        clear_others_stops(vecID, parkingID)

                        fln = open("log_strategia2.txt", "a")
                        print("[INFO set_parking()]: Il veicolo", vecID, "HA SETTATO LA FERMATA A", parkingID, "lungo la strada verso il più grande", file=fln)
                        fln.close()

                    # Forzo l'uscita dal for per evitare che venga settata qualche altra fermata
                    setted = True

                except traci.TraCIException as e:
                    pass
            else:
                # Controllo se non ci sono più posti disponibili
                if check_parking_aviability(parkingID) is False:
                    fln = open("log_strategia2.txt", "a")
                    print("[INFO set_parking()]: Il veicolo", vecID, "NON E' RIUSCITO A PARCHEGGIARE IN:", parkingID, "PER INDISPONIBILITA' DI POSTI LIBERI", file=fln)
                    fln.close()
                    # Controllo se avevo già settato la fermata
                    if check_stop_already_set(vecID, parkingID) is True:

                        # Elimino la fermata settata a questo parcheggio
                        clear_stop(vecID, parkingID)

            idx += 1

# * ********************************************************************************************************************************************************************* * #

def routine(vecID, curr_laneID, curr_edgeID, last_edgeID, expected_index):
    # Controllo se non sono arrivato al mio indirizzo di partenza, cioè destinazione xml oppure a una destinazione casuale
    if last_edgeID != get_depart_xml(vecID):

        # Assegno le coordinate (x, y) del suo indirizzo di destinazione xml
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
                                fln = open("log_strategia2.txt", "a")
                                print("[INFO routine()]: Il veicolo", vecID, "HA SETTATO LA FERMATA A", parkingID, "nella strada di destinazione XML", file=fln)
                                fln.close()
                            else:
                                fln = open("log_strategia2.txt", "a")
                                print("[INFO routine()]: Il veicolo", vecID, "HA SETTATO LA FERMATA A", parkingID, "nella strada dove è stato indirizzato", parkingID, file=fln)
                                print("[INFO routine()]: Il veicolo", vecID, "curr_edgeID:", curr_edgeID, "last_edgeID:", last_edgeID, file=fln)
                                fln.close()

                        # Forzo l'uscita dal for per evitare che venga settata qualche altra fermata
                        setted = True

                    except traci.TraCIException as e:
                        pass
                else:
                    fln = open("log_strategia2.txt", "a")
                    print("[INFO routine()]: Il veicolo", vecID, "NON E' RIUSCITO A PARCHEGGIARE IN:", parkingID, "PER INDISPONIBILITA' DI POSTI LIBERI", file=fln)
                    fln.close()

                idx += 1

            # Se non sono riuscito a parcheggiarmi nei parcheggi presenti nella strada di destinazione
            if setted is False:
                calculate_parkings(vecID)
                set_route_to_parking_edge(vecID, curr_edgeID, last_edgeID)
        else:
            # Controllo se non mi sono mai parcheggiato e non ci sono parcheggi nella strada di destinazione corrente
            if vecID_to_parked_dictionary.get(vecID) is None and len(list_of_tuple_parkID_index) <= 0:
                # Se non ci sono parcheggi nella strada di destinazione
                calculate_parkings(vecID)
                set_route_to_parking_edge(vecID, curr_edgeID, last_edgeID)


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
                    routine(vecID, curr_laneID, curr_edgeID, last_edgeID, next_expected_index)
                else:
                    # Se trovo parcheggio mentre mi dirigo verso una destinazione
                    # Controllo se non mi sono mai parcheggiato e se ho raggiunto la mia destinazione xml e non ho trovato parcheggio (controllo se ho settato i parcheggi)
                    if vecID_to_parked_dictionary.get(vecID) is None and vecID_to_list_parking_index.get(vecID) is not None:
                        # Controllo se ci sono parcheggi nella strada corrente e setto le fermata
                        set_parking_on_current_edge(vecID, curr_edgeID, curr_position, curr_lane_index)

            else:
                # Se il veicolo è attualmente parcheggiato
                send_to_depart_xml(vecID)

                # Setto che il veicolo ha parcheggiato
                vecID_to_parked_dictionary[vecID] = True

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

    fln = open("log_strategia2.txt", "w")
    fln.close()

    # STRATEGIA: strategia2, SCENARIO: 100%
    # sumoCmd = [sumoBinary, "-c", "./strategia2_config/san_francisco_strategia2_100%.sumocfg", "--start"]
    # traci.start(sumoCmd)
    # run("strategia2", "100%")
    # traci.close()

    # STRATEGIA: strategia2, SCENARIO: 75%
    # sumoCmd = [sumoBinary, "-c", "./strategia2_config/san_francisco_strategia2_75%.sumocfg", "--start"]
    # traci.start(sumoCmd)
    # run("strategia2", "75%")
    # traci.close()

    # STRATEGIA: strategia2, SCENARIO: 50%
    sumoCmd = [sumoBinary, "-c", "./strategia2_config/san_francisco_strategia2_50%.sumocfg", "--start"]
    traci.start(sumoCmd)
    run("strategia2", "50%")
    traci.close()


# * ********************************************************************************************************************************************************************* * #

if __name__ == "__main__":
    main()
