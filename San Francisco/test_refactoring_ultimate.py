#!/usr/bin/python
import os
import random
import sys
import xml.etree.ElementTree as ElementTree

import traci
from sumolib import checkBinary

AREA_INIT = 500
TIME_SLICE = 10
set_vec_parking_destinationXML = set()

# (destEdgeID, coordinateXY)
destedge_to_position_dictionary = {}

""" * ********************************************************************************************************************************************************************* * """

# (currLaneID, parkingID)
lane_to_parking_dictionary = {}


def set_lane_to_parking_dictionary():
    file = open("loadparking.txt", "w")
    parkingIDs_list = traci.parkingarea.getIDList()
    for parkingID in parkingIDs_list:
        curr_laneID = traci.parkingarea.getLaneID(parkingID)
        lane_to_parking_dictionary[curr_laneID] = parkingID
        print("LANE:", curr_laneID, "   PARKING:", lane_to_parking_dictionary[curr_laneID], file=file)
    file.close()


""" * ********************************************************************************************************************************************************************* * """

# (vecID, (lato, count_espansione) )
vecID_to_dynamicarea_counter_dictionary = {}


def load_vecID_to_dynamicarea_counter_dictionary(val):
    for vecID in get_vehicle_from_xml():
        vecID_to_dynamicarea_counter_dictionary[vecID] = (val, 0)


def update_vecID_to_dynamicarea_counter_dictionary(vecID, area, counter):
    if vecID_to_dynamicarea_counter_dictionary.get(vecID)[0] != area or vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] != counter:
        vecID_to_dynamicarea_counter_dictionary[vecID] = (area, counter)


def reset_vecID_to_dynamicarea_counter_dictionary(vecID):
    if vecID_to_dynamicarea_counter_dictionary.get(vecID)[0] != AREA_INIT or vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] != 0:
        vecID_to_dynamicarea_counter_dictionary[vecID] = (AREA_INIT, 0)


""" * ********************************************************************************************************************************************************************* * """


def get_start_coordinate_from_dest_edgee(destEdgeID, index):
    coordinateXY = traci.simulation.convert2D(destEdgeID, 0.0, index, False)
    return coordinateXY


""" * ********************************************************************************************************************************************************************* * """


def get_vehicle_from_xml():
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


""" * ********************************************************************************************************************************************************************* * """


def get_lane_xml_form_edge_and_index(edgeID, index):
    tree = ElementTree.parse('san_francisco.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


def get_indexes_xml_form_edge(edgeID):
    tree = ElementTree.parse('san_francisco.net.xml')
    root = tree.getroot()
    list_indexes = []
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        list_indexes.append(int(name.attrib['index']))
    return list_indexes


def get_expected_index(edgeID, curr_lane_index):
    list_indexes = get_indexes_xml_form_edge(edgeID)
    if curr_lane_index != 0 and curr_lane_index in list_indexes:
        return curr_lane_index
    else:
        return 0


""" * ********************************************************************************************************************************************************************* * """


def get_destination_xml(vecID):
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[len(list_edges) - 1]
    return None


""" * ********************************************************************************************************************************************************************* * """


def get_depart_xml(vecID):
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[0]
    return None


""" * ********************************************************************************************************************************************************************* * """


def get_distance_to_last(curr_edgeID, last_edgeID, curr_position):
    if curr_edgeID == last_edgeID:
        distance_tolast_edge = 0.0
    else:
        print("curr_edge:", curr_edgeID, "last_edge:", last_edgeID, "curr_posiiton:", curr_position)
        distance_tolast_edge = traci.simulation.getDistanceRoad(curr_edgeID, curr_position, last_edgeID, 0.0, True)

    return distance_tolast_edge


""" * ********************************************************************************************************************************************************************* * """


def get_parking(laneID):
    return lane_to_parking_dictionary.get(laneID)


""" * ********************************************************************************************************************************************************************* * """


def check_parking_aviability(parkingID):
    parking_capacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
    parking_occupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
    if parking_occupancy < parking_capacity:
        return True
    return False


def is_parking_already_setted(vecID, parkingID):
    tuple_of_stop_data = traci.vehicle.getStops(vecID, 10)
    if len(tuple_of_stop_data) == 0:
        return False
    else:
        print("*** [INFO] Stops:", tuple_of_stop_data)
        for i in range(0, len(tuple_of_stop_data)):
            temp_stop_data = tuple_of_stop_data[i]
            if temp_stop_data.stoppingPlaceID == parkingID:
                return True
        return False


""" * ********************************************************************************************************************************************************************* * """


def check_exit_vec(step):
    count = traci.vehicle.getIDCount()
    print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")
    if step != 0:
        # Controllo se qualche veicolo ha lasciato la simulazione
        if (len(traci.simulation.getArrivedIDList())) > 0:
            file = open("arrived_vehicle.txt", "a+")
            print("" + str(traci.simulation.getArrivedIDList()), file=file)
            file.close()


""" * ********************************************************************************************************************************************************************* * """


def send_to_destination_xml(vecID):
    currRouteList = traci.vehicle.getRoute(vecID)
    currLastEdgeID = currRouteList[len(currRouteList) - 1]
    destinationEdgeXML = get_destination_xml(vecID)
    if currLastEdgeID != destinationEdgeXML:
        traci.vehicle.changeTarget(vecID, destinationEdgeXML)
        traci.vehicle.setColor(vecID, (255, 255, 0))
        return True
    return False


def send_to_depart_xml(vecID):
    currRouteList = traci.vehicle.getRoute(vecID)
    currLastEdgeID = currRouteList[len(currRouteList) - 1]
    departEdgeXML = get_depart_xml(vecID)
    if currLastEdgeID != departEdgeXML:
        traci.vehicle.changeTarget(vecID, departEdgeXML)
        traci.vehicle.setColor(vecID, (255, 255, 0))
        return True
    return False


def set_coordinate_destination_xml(vecID, curr_lane_index):
    if destedge_to_position_dictionary.get(vecID) is None:
        coordinateXY = get_start_coordinate_from_dest_edgee(get_destination_xml(vecID), curr_lane_index)
        destedge_to_position_dictionary[vecID] = coordinateXY


""" * ********************************************************************************************************************************************************************* * """

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


def check_timeslice(vecID, count):
    if count == TIME_SLICE:
        if vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] < 3:
            print("     *** Aumento la superficie perchè sono passati", TIME_SLICE, "steps ***")
            update_vecID_to_dynamicarea_counter_dictionary(vecID, vecID_to_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
            update_vec_to_searchtime_started_dictionary(vecID, 0, True)
        else:
            destination_edgeXML = get_destination_xml(vecID)
            print("     Sono passati", TIME_SLICE, "steps")
            print("     Il veicolo ritornerà alla sua destinazione iniziale: " + str(destination_edgeXML) + " perchè NON è possibile aumentare la superficie")
            send_to_destination_xml(vecID)
            reset_vecID_to_dynamicarea_counter_dictionary(vecID)
            reset_vec_to_searchtime_started_dictionary(vecID)



""" * ********************************************************************************************************************************************************************* * """


def get_available_edges(vecID, curr_laneID, expected_index, last_laneID_excpected, list_tuple_links):
    tupla_vec = vecID_to_dynamicarea_counter_dictionary.get(vecID)
    curr_area = tupla_vec[0]
    destedges_posXY = destedge_to_position_dictionary.get(vecID)
    limit_infX = destedges_posXY[0] - curr_area / 2
    limit_infY = destedges_posXY[1] - curr_area / 2
    limit_supX = destedges_posXY[0] + curr_area / 2
    limit_supY = destedges_posXY[1] + curr_area / 2

    list_available = []

    for i in range(0, len(list_tuple_links)):
        temp_tuple = list_tuple_links[i]
        temp_lane = temp_tuple[0]
        temp_edge = ""

        if last_laneID_excpected is not None:
            if temp_lane != curr_laneID and temp_lane != last_laneID_excpected:
                temp_edge = traci.lane.getEdgeID(temp_lane)
        else:
            if temp_lane != curr_laneID:
                temp_edge = traci.lane.getEdgeID(temp_lane)

        if temp_edge != "":
            # print("@@@ temp_edge:", temp_edge)
            temp_index = get_expected_index(temp_edge, expected_index)
            # print("@@@ temp_index:", temp_index)
            curr_coordinateXY = get_start_coordinate_from_dest_edgee(temp_edge, temp_index)
            currX = curr_coordinateXY[0]
            currY = curr_coordinateXY[1]

            if limit_infX <= currX <= limit_supX and limit_infY <= currY <= limit_supY:
                list_available.append(temp_edge)

    return list_available


def search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected):
    # Veicolo alla ricerca di un parcheggio
    traci.vehicle.setColor(vecID, (255, 0, 0))

    # Notifico che da questo momento il veicolo sta cercando parcheggio
    update_vec_to_searchtime_started_dictionary(vecID, vec_to_searchtime_started_dictionary.get(vecID)[0], True)

    if last_laneID_excpected is not None:
        num_links = traci.lane.getLinkNumber(last_laneID_excpected)
        list_tuple_links = traci.lane.getLinks(last_laneID_excpected)  # Una lista di tuple
    else:
        num_links = traci.lane.getLinkNumber(curr_laneID)
        list_tuple_links = traci.lane.getLinks(curr_laneID)  # Una lista di tuple


    if num_links >= 1:
        exit_cond = False
        while vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] < 3 and exit_cond is False:
            list_available_edgs = get_available_edges(vecID, curr_laneID, expected_index, last_laneID_excpected, list_tuple_links)

            if len(list_available_edgs) > 0:
                random_edgID = random.choice(list_available_edgs)
                traci.vehicle.changeTarget(vecID, random_edgID)
                print("     Il veicolo ha scelto casualmente " + random_edgID)

                temp_random_index = get_expected_index(random_edgID, expected_index)
                temp_random_lane = get_lane_xml_form_edge_and_index(random_edgID, temp_random_index)
                temp_random_lane_length = traci.lane.getLength(temp_random_lane)

                curr_vec_edgID = traci.lane.getEdgeID((traci.vehicle.getLaneID(vecID)))
                curr_speed = traci.vehicle.getSpeed(vecID)
                leader_speed = traci.vehicle.getAllowedSpeed(vecID)
                gap_to_random_edgeID = get_distance_to_last(curr_vec_edgID, random_edgID, traci.vehicle.getLanePosition(vecID))
                max_decel = traci.vehicle.getDecel(vecID)

                space_on_next_next_step = traci.vehicle.getFollowSpeed(vecID, curr_speed, gap_to_random_edgeID, leader_speed, max_decel)
                if temp_random_lane_length <= space_on_next_next_step:
                    num_links_next = traci.lane.getLinkNumber(temp_random_lane)
                    if num_links_next >= 1:
                        links_next = traci.lane.getLinks(temp_random_lane)

                        if last_laneID_excpected is not None:
                            aviable_edges = get_available_edges(vecID, last_laneID_excpected, temp_random_index, temp_random_lane, links_next)
                        else:
                            aviable_edges = get_available_edges(vecID, curr_laneID, temp_random_index, temp_random_lane, links_next)

                        if len(aviable_edges) >= 1:
                            selected = None
                            for edg in aviable_edges:
                                idx = get_expected_index(edg, temp_random_index)
                                lane = get_lane_xml_form_edge_and_index(edg, idx)
                                length = traci.lane.getLength(lane)
                                if length > space_on_next_next_step:
                                    selected = edg
                                    break
                            if selected is not None:
                                traci.vehicle.changeTarget(vecID, selected)
                            else:
                                send_to_destination_xml(vecID)
                    else:
                        file_arrived = open("arrived_vehicle.txt", "a+")
                        print("[", vecID, "] esce perché non ci sono piu' strade fisicamente percorribili", file=file_arrived)
                        file_arrived.close()

                exit_cond = True
            else:
                print("     *** Aumento la superficie di ricerca perchè non ci sono strade disponibili in quest'area di ricerca ***")
                update_vecID_to_dynamicarea_counter_dictionary(vecID, vecID_to_dynamicarea_counter_dictionary.get(vecID)[0] * 2,vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
                update_vec_to_searchtime_started_dictionary(vecID, 0, True)

        # Controllo se sono uscito perché ho aumentato la superficie di ricerca al massimo
        if vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] >= 3 and exit_cond is False:
            dest_edge = get_destination_xml(vecID)
            edg = traci.lane.getEdgeID(curr_laneID)
            if edg != dest_edge:
                print("     Il veicolo non può aumentare ancora la superficie per trovare una strada, tornerà alla sua destinazione iniziale", dest_edge)
                send_to_destination_xml(vecID)
                reset_vecID_to_dynamicarea_counter_dictionary(vecID)
                reset_vec_to_searchtime_started_dictionary(vecID)
            else:
                depart_edge = get_depart_xml(vecID)
                print("     Il veicolo non può aumentare ancora la superficie per trovare una strada, tornerà alla sua destinazione iniziale", dest_edge)
                print("     Il veicolo non può tornare alla sua destinazione iniziale", dest_edge, "torneà alla suo indirizzo di partenza", depart_edge)
                send_to_depart_xml(vecID)
                reset_vecID_to_dynamicarea_counter_dictionary(vecID)
                reset_vec_to_searchtime_started_dictionary(vecID)
    else:
        # Non c'è nessuna strada collegata a quella corrente
        file = open("arrived_vehicle.txt", "a+")
        print("[", vecID, "] esce perché non ci sono piu' strade fisicamente percorribili", file=file)
        file.close()


""" * ********************************************************************************************************************************************************************* * """


def critical_routine(vecID, curr_edgeID, curr_laneID, curr_lane_index, last_edgeID, last_laneID_excpected, expected_index):
    print("    # [CRITICAL ROUTINE] >>> Il veicolo è arrivato a destinazione", curr_edgeID, " == (", last_edgeID, ") ***")

    print("@@@@ expcected index:", expected_index)
    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    set_coordinate_destination_xml(vecID, expected_index)

    # Controllo se il veicolo ha trovato parcheggio nella strada di destinazione XML e se è tornato al suo indirizzo di partenza XML
    if vecID in set_vec_parking_destinationXML and last_edgeID == get_depart_xml(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        send_to_destination_xml(vecID)

    else:
        # Il veicolo è alla ricerca di un parcheggio
        traci.vehicle.setColor(vecID, (255, 0, 0))

        # Controllo se nella lane di destinazione corrente c'è un parcheggio
        parkingID = get_parking(last_laneID_excpected)
        if parkingID is not None:
            print("     Ho trovato:" + str(parkingID))

            # Il veicolo ha trovato parcheggio
            traci.vehicle.setColor(vecID, (0, 255, 0))

            if check_parking_aviability(parkingID):
                try:
                    # Controllo se il veicolo ha trovato parcheggio PROPRIO nella sua destinazione XML
                    # laneDestinationXML != currLastLaneID poichè currLastLaneID cambia di percorso in percorso
                    destination_edgeXML = get_destination_xml(vecID)
                    lane_destinationXML = get_lane_xml_form_edge_and_index(destination_edgeXML, expected_index)
                    lane_parking = traci.parkingarea.getLaneID(parkingID)

                    if lane_parking == lane_destinationXML:
                        set_vec_parking_destinationXML.add(vecID)

                    if is_parking_already_setted(vecID, parkingID) is False:
                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                    reset_vec_to_searchtime_started_dictionary(vecID)
                except traci.TraCIException as e:
                    print("     Non è riuscito a parcheggiare a causa di un'eccezione", e)
                    search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected)
            else:
                print("     Non è riuscito a parcheggiare a causa della disponibilità")
                search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected)
        else:
            print("     Il veicolo non ha trovato parcheggio nella strada " + str(last_edgeID) + " , alla lane " + str(last_laneID_excpected))
            search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected)


""" * ********************************************************************************************************************************************************************* * """


def normal_routine(vecID, curr_edgeID, curr_laneID, curr_lane_index):
    print("    # [NORMAL ROUTINE] >>> Il veicolo è arrivato a destinazione (" + curr_edgeID + ") ***")

    print("@@@@ curr index:", curr_lane_index)

    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    set_coordinate_destination_xml(vecID, curr_lane_index)

    # Controllo se il veicolo ha trovato parcheggio nella strada di destinazione XML e se è tornato al suo indirizzo di partenza XML
    if vecID in set_vec_parking_destinationXML and curr_edgeID == get_depart_xml(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        send_to_destination_xml(vecID)
    else:

        # Il veicolo è alla ricerca di un parcheggio
        traci.vehicle.setColor(vecID, (255, 0, 0))

        # Controllo se nella lane di destinazione corrente c'è un parcheggio
        parkingID = get_parking(curr_laneID)
        if parkingID is not None:
            print("    Ho trovato:" + str(parkingID))
            # Il veicolo ha trovato parcheggio
            traci.vehicle.setColor(vecID, (0, 255, 0))

            if check_parking_aviability(parkingID):
                try:
                    # Controllo se il veicolo ha trovato parcheggio PROPRIO nella sua destinazione XML
                    # laneDestinationXML != currLastLaneID poichè currLastLaneID cambia di percorso in percorso
                    destination_edgeXML = get_destination_xml(vecID)
                    lane_destinationXML = get_lane_xml_form_edge_and_index(destination_edgeXML, curr_lane_index)
                    lane_parking = traci.parkingarea.getLaneID(parkingID)

                    if lane_parking == lane_destinationXML:
                        set_vec_parking_destinationXML.add(vecID)

                    if is_parking_already_setted(vecID, parkingID) is False:
                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                    reset_vec_to_searchtime_started_dictionary(vecID)

                except traci.TraCIException as e:
                    print("     Non è riuscito a parcheggiare a causa di un'eccezione", e)
                    search_random_edge_for_parking(vecID, curr_laneID, curr_lane_index, None)
            else:
                print("     Non è riuscito a parcheggiare a causa della disponibilità")
                search_random_edge_for_parking(vecID, curr_laneID, curr_lane_index, None)
        else:
            print("     Il veicolo non ha trovato parcheggio nella strada " + curr_edgeID + " , alla lane " + curr_laneID)
            search_random_edge_for_parking(vecID, curr_laneID, curr_lane_index, None)


""" * ********************************************************************************************************************************************************************* * """

def run():
    load_vecID_to_dynamicarea_counter_dictionary(AREA_INIT)
    set_lane_to_parking_dictionary()
    load_vec_to_searchtime_started_dictionary()

    step = traci.simulation.getTime()  # step = 0.0

    while traci.simulation.getMinExpectedNumber() != 0:

        check_exit_vec(step)
        curr_vehicles_List = traci.vehicle.getIDList()

        for vecID in curr_vehicles_List:
            print("\n # VEC_ID: [" + vecID + "]")
            print("    # (currArea, counter):", vecID_to_dynamicarea_counter_dictionary.get(vecID))
            print("    # (counter_step, started):", vec_to_searchtime_started_dictionary.get(vecID))

            # SE IL VEICOLO NON È ATTUALMENTE PARCHEGGIATO
            if traci.vehicle.isStoppedParking(vecID) is False:

                started_research = vec_to_searchtime_started_dictionary.get(vecID)[1]
                if started_research is True:
                    count_timeslice = vec_to_searchtime_started_dictionary.get(vecID)[0] + 1
                    update_vec_to_searchtime_started_dictionary(vecID, count_timeslice, True)
                    check_timeslice(vecID, count_timeslice)

                curr_route_list = traci.vehicle.getRoute(vecID)
                last_edgeID = curr_route_list[len(curr_route_list) - 1]

                curr_laneID = traci.vehicle.getLaneID(vecID)
                curr_position = traci.vehicle.getLanePosition(vecID)
                curr_speed = traci.vehicle.getSpeed(vecID)
                curr_acc = traci.vehicle.getAcceleration(vecID)
                curr_edgeID = traci.lane.getEdgeID(curr_laneID)
                curr_lane_index = traci.vehicle.getLaneIndex(vecID)

                distance_to_lastedge = get_distance_to_last(curr_edgeID, last_edgeID, curr_position)

                leader_speed = traci.vehicle.getAllowedSpeed(vecID)
                # min_gap = traci.vehicle.getMinGap(vecID)
                max_decel = traci.vehicle.getDecel(vecID)

                # Limite superiore della velocità nel prossimo step
                # space_on_next_step = (1 / 2 * abs(curr_acc) * 1) + (curr_speed * 1)
                space_on_next_step = traci.vehicle.getFollowSpeed(vecID, curr_speed, distance_to_lastedge, leader_speed, max_decel)

                print("    # curr_speed:", curr_speed, " , curr_acc:", curr_acc)
                print("    # currEdge:", curr_edgeID, ", lastEdge:", last_edgeID)
                print("    # currLane:", curr_laneID, ", LaneIndex:", curr_lane_index)
                print("    # currPosition:", curr_position)
                print("    # distance_to_last:", distance_to_lastedge)
                print("    # space_on_next_step:", space_on_next_step)

                # ___ CRITICAL ROUTINE ___ #
                if space_on_next_step >= distance_to_lastedge and curr_edgeID != last_edgeID:
                    next_expected_index = get_expected_index(last_edgeID, curr_lane_index)
                    last_laneID_excpected = get_lane_xml_form_edge_and_index(last_edgeID, next_expected_index)
                    critical_routine(vecID, curr_edgeID, curr_laneID, curr_lane_index, last_edgeID, last_laneID_excpected, next_expected_index)
                # ___ NORMAL ROUTINE ___ #
                elif space_on_next_step >= distance_to_lastedge and curr_edgeID == last_edgeID:
                    normal_routine(vecID, curr_edgeID, curr_laneID, curr_lane_index)

                # ___ TRIP ROUTINE ___ #
                else:
                    print("     Sto viaggindo...")
            else:
                # SE IL VEICOLO E' ATTUALMENTE PARCHEGGIATO
                print("     Il veicolo è attualmente parcheggiato!...")

                if vecID in set_vec_parking_destinationXML:
                    send_to_depart_xml(vecID)
                    print("     Il veicolo ritornerà alla sua partenza: " + get_depart_xml(vecID))
                else:
                    send_to_destination_xml(vecID)
                    print("     Il veicolo ritornerà alla sua destinazione iniziale: " + get_destination_xml(vecID))

                reset_vecID_to_dynamicarea_counter_dictionary(vecID)

        traci.simulation.step()
        step = traci.simulation.getTime()  # step ++  # traci.time.sleep(0.5)


""" * ********************************************************************************************************************************************************************* * """


def main():
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    # sumoBinary = checkBinary('sumo-gui')
    sumoBinary = checkBinary('sumo')
    sumoCmd = [sumoBinary, "-c", "san_francisco.sumocfg", "--start"]

    traci.start(sumoCmd)
    run()
    traci.close()


if __name__ == "__main__":
    main()
