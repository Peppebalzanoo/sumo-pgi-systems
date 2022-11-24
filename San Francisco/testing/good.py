#!/usr/bin/python
import os
import random
import sys
import xml.etree.ElementTree as ElementTree

import traci
from sumolib import checkBinary

AREA_INIT = 500
TIME_SLICE = 600

# (vecID, coordinateXY_lane_dest)
dest_lane_to_position_dictionary = {}

""" * ********************************************************************************************************************************************************************* * """

# (currLaneID, parkingID)
lane_to_parking_dictionary = {}


def set_lane_to_parking_dictionary():
    # file = open("loadparking.txt", "w")
    parkingIDs_list = traci.parkingarea.getIDList()
    for parkingID in parkingIDs_list:
        curr_laneID = traci.parkingarea.getLaneID(parkingID)
        lane_to_parking_dictionary[curr_laneID] = parkingID
        # print("LANE:", curr_laneID, "   PARKING:", lane_to_parking_dictionary[curr_laneID], file=file)
    # file.close()


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


def get_start_coordinate_from_destination_lane(destEdgeID, index):
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
        distance_tolast_edge = traci.simulation.getDistanceRoad(curr_edgeID, curr_position, last_edgeID, 0.0, True)

    return distance_tolast_edge


""" * ********************************************************************************************************************************************************************* * """


# Attenzione all'uso di questo metodo, bisognerebbe controllare se il parkingID non è NONE
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
    for i in range(0, len(tuple_of_stop_data)):
        temp_stop_data = tuple_of_stop_data[i]
        if temp_stop_data.stoppingPlaceID == parkingID:
            return True
    return False


""" * ********************************************************************************************************************************************************************* * """


# def check_exit_vec(step):
#     count = traci.vehicle.getIDCount()
#     print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")
#     if step != 0:
#         # Controllo se qualche veicolo ha lasciato la simulazione
#         if (len(traci.simulation.getArrivedIDList())) > 0:
#             file = open("arrived_vehicle.txt", "a+")
#             print("" + str(traci.simulation.getArrivedIDList()), file=file)
#             file.close()


""" * ********************************************************************************************************************************************************************* * """


# def send_to_destination_xml(vecID):
#     currRouteList = traci.vehicle.getRoute(vecID)
#     currLastEdgeID = currRouteList[len(currRouteList) - 1]
#     destinationEdgeXML = get_destination_xml(vecID)
#     if currLastEdgeID != destinationEdgeXML:
#         traci.vehicle.changeTarget(vecID, destinationEdgeXML)
#         traci.vehicle.setColor(vecID, (255, 255, 0))
#         return True
#     return False


def send_to_depart_xml(vecID):
    curr_route_list = traci.vehicle.getRoute(vecID)
    curr_last_edgeID = curr_route_list[len(curr_route_list) - 1]
    depart_edge_xml = get_depart_xml(vecID)
    if curr_last_edgeID != depart_edge_xml:
        traci.vehicle.changeTarget(vecID, depart_edge_xml)
        traci.vehicle.setColor(vecID, (255, 255, 0))
        return True
    return False


def set_coordinate_lane_destination_xml(vecID, curr_lane_index):
    if dest_lane_to_position_dictionary.get(vecID) is None:
        coordinateXY = get_start_coordinate_from_destination_lane(get_destination_xml(vecID), curr_lane_index)
        dest_lane_to_position_dictionary[vecID] = coordinateXY


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
            # print("     *** Aumento la superficie perchè sono passati", TIME_SLICE, "steps ***")
            update_vecID_to_dynamicarea_counter_dictionary(vecID, vecID_to_dynamicarea_counter_dictionary.get(vecID)[0] * 2,vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
            update_vec_to_searchtime_started_dictionary(vecID, 0, True)
        else:
            # print("     Sono passati", TIME_SLICE, "steps")
            # print("     Il veicolo ritornerà alla sua partenza iniziale:", get_depart_xml(vecID), " perchè NON è possibile aumentare la superficie")
            send_to_depart_xml(vecID)
            reset_vecID_to_dynamicarea_counter_dictionary(vecID)
            reset_vec_to_searchtime_started_dictionary(vecID)


""" * ********************************************************************************************************************************************************************* * """


def get_available_edges(vecID, curr_laneID, expected_index, last_laneID_excpected, list_tuple_links):
    tupla_dynamicarea_counter = vecID_to_dynamicarea_counter_dictionary.get(vecID)
    curr_area = tupla_dynamicarea_counter[0]
    dest_lane_positionXY = dest_lane_to_position_dictionary.get(vecID)
    limit_infX = dest_lane_positionXY[0] - curr_area / 2
    limit_infY = dest_lane_positionXY[1] - curr_area / 2
    limit_supX = dest_lane_positionXY[0] + curr_area / 2
    limit_supY = dest_lane_positionXY[1] + curr_area / 2

    list_available = []
    for i in range(0, len(list_tuple_links)):
        temp_tuple = list_tuple_links[i]
        temp_lane = temp_tuple[0]

        if temp_lane != curr_laneID and temp_lane != last_laneID_excpected:
            temp_edge = traci.lane.getEdgeID(temp_lane)
            temp_index = get_expected_index(temp_edge, expected_index)
            curr_coordinateXY = get_start_coordinate_from_destination_lane(temp_edge, temp_index)

            currX = curr_coordinateXY[0]
            currY = curr_coordinateXY[1]
            if limit_infX <= currX <= limit_supX and limit_infY <= currY <= limit_supY:
                list_available.append(temp_edge)

    return list_available


def search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected, space_on_next_step, dist_to_last):
    # Veicolo alla ricerca di un parcheggio
    traci.vehicle.setColor(vecID, (255, 0, 0))

    # Notifico che da questo momento il veicolo sta cercando parcheggio
    update_vec_to_searchtime_started_dictionary(vecID, vec_to_searchtime_started_dictionary.get(vecID)[0], True)

    num_links = traci.lane.getLinkNumber(last_laneID_excpected)
    list_tuple_links = traci.lane.getLinks(last_laneID_excpected)  # Una lista di tuple

    if num_links >= 1:
        exit_cond = False
        while vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] < 3 and exit_cond is False:
            list_available_edgs = get_available_edges(vecID, curr_laneID, expected_index, last_laneID_excpected, list_tuple_links)

            if len(list_available_edgs) > 0:
                random_edgeID = random.choice(list_available_edgs)
                random_index = get_expected_index(random_edgeID, expected_index)
                random_laneID = get_lane_xml_form_edge_and_index(random_edgeID, random_index)
                traci.vehicle.changeTarget(vecID, random_edgeID)
                # print("     Il veicolo ha scelto casualmente " + random_edgeID)

                # curr_position_on_new_curr_edge = (space_on_next_step - dist_to_last)
                curr_position_on_new_curr_edge = 0.0

                # old_last_edge is new curr_edge
                old_last_edge = traci.lane.getEdgeID(last_laneID_excpected)
                distance_to_new_last_edge = get_distance_to_last(old_last_edge, random_edgeID, curr_position_on_new_curr_edge)

                # space_on_next_step is a new curr_speed
                space_on_next_next_step = traci.vehicle.getFollowSpeed(vecID, space_on_next_step, distance_to_new_last_edge, traci.lane.getMaxSpeed(last_laneID_excpected), traci.vehicle.getDecel(vecID))

                if space_on_next_next_step >= distance_to_new_last_edge:
                    num_links_next = traci.lane.getLinkNumber(random_laneID)
                    if num_links_next >= 1:
                        list_next = traci.lane.getLinks(random_laneID)
                        avbl_edg = get_available_edges(vecID, last_laneID_excpected, random_index, random_laneID, list_next)
                        if len(avbl_edg) >= 1:
                            new_next = random.choice(avbl_edg)
                            traci.vehicle.changeTarget(vecID, new_next)
                            # print("     ### Il veicolo ha scelto casualmente " + new_next)
                            exit_cond = True
                        else:
                            # print("     *** Aumento la superficie di ricerca perchè non ci sono strade disponibili in quest'area di ricerca ***")
                            update_vecID_to_dynamicarea_counter_dictionary(vecID, vecID_to_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
                            update_vec_to_searchtime_started_dictionary(vecID, 0, True)
                    else:
                        # Non c'è nessuna strada collegata a quella corrente
                        file = open("arrived_vehicle.txt", "a+")
                        print("[", vecID, "] non ci sono piu' strade fisicamente percorribili", file=file)
                        file.close()
                else:
                    exit_cond = True
            else:
                # print("     *** Aumento la superficie di ricerca perchè non ci sono strade disponibili in quest'area di ricerca ***")
                update_vecID_to_dynamicarea_counter_dictionary(vecID, vecID_to_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
                update_vec_to_searchtime_started_dictionary(vecID, 0, True)

        # Controllo se sono uscito perché ho aumentato la superficie di ricerca al massimo
        if vecID_to_dynamicarea_counter_dictionary.get(vecID)[1] >= 3 and exit_cond is False:
            # print(" Il veicolo non può aumentare ancora la superficie per trovare una strada, tornerà alla sua partenza iniziale", get_depart_xml(vecID))
            send_to_depart_xml(vecID)
            reset_vecID_to_dynamicarea_counter_dictionary(vecID)
            reset_vec_to_searchtime_started_dictionary(vecID)
    else:
        # Non c'è nessuna strada collegata a quella corrente
        file = open("arrived_vehicle.txt", "a+")
        print("[", vecID, "] esce perché non ci sono piu' strade fisicamente percorribili", file=file)
        file.close()


""" * ********************************************************************************************************************************************************************* * """


def critical_routine(vecID, curr_edgeID, curr_laneID, curr_lane_index, last_edgeID, last_laneID_excpected, expected_index, space_on_next_step, dist_to_last):
    # print("    # [CRITICAL ROUTINE] >>> Il veicolo è arrivato a destinazione", curr_edgeID, " == (", last_edgeID, ") ***")

    # Controllo se non sono arrivato al mio indirizzo di partenza
    # Controllo se sono arrivato alla mia destinazione ( destinazione xml oppure destinazione casuale )
    if last_edgeID != get_depart_xml(vecID):

        # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
        set_coordinate_lane_destination_xml(vecID, expected_index)

        # Il veicolo è alla ricerca di un parcheggio
        traci.vehicle.setColor(vecID, (255, 0, 0))

        # Controllo se nella lane di destinazione corrente c'è un parcheggio
        parkingID = get_parking(last_laneID_excpected)
        if parkingID is not None:
            # print("     Ho trovato:" + str(parkingID))

            # Il veicolo ha trovato parcheggio
            traci.vehicle.setColor(vecID, (0, 255, 0))

            if check_parking_aviability(parkingID):
                try:
                    if is_parking_already_setted(vecID, parkingID) is False:
                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                    reset_vec_to_searchtime_started_dictionary(vecID)
                except traci.TraCIException as e:
                    # print(" Non è riuscito a parcheggiare a causa di un'eccezione", e)
                    search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected, space_on_next_step, dist_to_last)
            else:
                # print(" Non è riuscito a parcheggiare a causa della disponibilità")
                search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected, space_on_next_step, dist_to_last)
        else:
            # print("     Il veicolo non ha trovato parcheggio nella strada " + str(last_edgeID) + " , alla lane " + str(last_laneID_excpected))
            search_random_edge_for_parking(vecID, curr_laneID, expected_index, last_laneID_excpected, space_on_next_step, dist_to_last)


""" * ********************************************************************************************************************************************************************* * """


# def normal_routine(vecID, curr_edgeID, curr_laneID, curr_lane_index):
#     print("    # [NORMAL ROUTINE] >>> Il veicolo è arrivato a destinazione (" + curr_edgeID + ") ***")
#
#     # Controllo se non sono arrivato al mio indirizzo di partenza
#     # Controllo se sono arrivato alla mia destinazione ( destinazione xml oppure destinazione casuale )
#     if curr_edgeID != get_depart_xml(vecID):
#         # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
#         set_coordinate_lane_destination_xml(vecID, curr_lane_index)
#
#         # Il veicolo è alla ricerca di un parcheggio
#         traci.vehicle.setColor(vecID, (255, 0, 0))
#
#         # Controllo se nella lane di destinazione corrente c'è un parcheggio
#         parkingID = get_parking(curr_laneID)
#         if parkingID is not None:
#             print("    Ho trovato:" + str(parkingID))
#             # Il veicolo ha trovato parcheggio
#             traci.vehicle.setColor(vecID, (0, 255, 0))
#
#             if check_parking_aviability(parkingID):
#                 try:
#                     if is_parking_already_setted(vecID, parkingID) is False:
#                         traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)
#
#                     reset_vec_to_searchtime_started_dictionary(vecID)
#                 except traci.TraCIException as e:
#                     print("     Non è riuscito a parcheggiare a causa di un'eccezione", e)
#                     search_random_edge_for_parking(vecID, curr_laneID, curr_lane_index, None)
#             else:
#                 print("     Non è riuscito a parcheggiare a causa della disponibilità")
#                 search_random_edge_for_parking(vecID, curr_laneID, curr_lane_index, None)
#         else:
#             print("     Il veicolo non ha trovato parcheggio nella strada " + curr_edgeID + " , alla lane " + curr_laneID)
#             search_random_edge_for_parking(vecID, curr_laneID, curr_lane_index, None)


""" * ********************************************************************************************************************************************************************* * """


def run():
    load_vecID_to_dynamicarea_counter_dictionary(AREA_INIT)
    set_lane_to_parking_dictionary()
    load_vec_to_searchtime_started_dictionary()

    step = traci.simulation.getTime()  # step = 0.0

    while traci.simulation.getMinExpectedNumber() != 0:
        # print("\n ###################### STEP: " + str(step) + " ######################")
        curr_vehicles_List = traci.vehicle.getIDList()

        for vecID in curr_vehicles_List:
            """print("\n # VEC_ID: [" + vecID + "]")
            print("    # (currArea, counter):", vecID_to_dynamicarea_counter_dictionary.get(vecID))
            print("    # (counter_step, started):", vec_to_searchtime_started_dictionary.get(vecID))"""

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

                """#print("    # curr_speed:", curr_speed, " , curr_acc:", curr_acc)
                # print("    # currEdge:", curr_edgeID, ", lastEdge:", last_edgeID)
                # print("    # currLane:", curr_laneID, ", LaneIndex:", curr_lane_index)
                # print("    # currPosition:", curr_position)
                # print("    # distance_to_last:", distance_to_lastedge)
                # print("    # space_on_next_step:", space_on_next_step)"""

                # ___ ROUTINE ___ #
                if space_on_next_step >= distance_to_lastedge:
                    next_expected_index = get_expected_index(last_edgeID, curr_lane_index)
                    last_laneID_excpected = get_lane_xml_form_edge_and_index(last_edgeID, next_expected_index)
                    critical_routine(vecID, curr_edgeID, curr_laneID, curr_lane_index, last_edgeID, last_laneID_excpected, next_expected_index, space_on_next_step, distance_to_lastedge)

                """# ___ TRIP ROUTINE ___ #
                # else:
                #     print("     Sto viaggindo...")"""
            else:
                # SE IL VEICOLO È ATTUALMENTE PARCHEGGIATO
                # print(" Il veicolo è attualmente parcheggiato!...")

                send_to_depart_xml(vecID)
                # print(" Il veicolo ritornerà alla sua partenza: " + get_depart_xml(vecID))

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
