#!/usr/bin/python
import os
import random
import sys
import xml.etree.ElementTree as ElementTree

import traci
from sumolib import checkBinary

AREA_INIT = 1000
TIME_SLICE = 10

# (destEdgeID, tuplaXY)
destedges_tupleposXY_dictionary = {}

""" * ********************************************************************************************************************************************************************* * """

# (currLaneID, parkingID)
lane_parking_dictionary = {}


def load_lane_parking_dictionary():
    parkingIDs_list = traci.parkingarea.getIDList()
    for parkingID in parkingIDs_list:
        curr_laneID = traci.parkingarea.getLaneID(parkingID)
        lane_parking_dictionary[curr_laneID] = parkingID


""" * ********************************************************************************************************************************************************************* * """

# (vecID, (lato, count_espansione) )
vecID_dynamicarea_counter_dictionary = {}


def load_dynamicarea_counter_dictionary(val):
    for vecID in getvehicleXML():
        vecID_dynamicarea_counter_dictionary[vecID] = (val, 0)


def update_dynamicarea_counter(vecID, area, counter):
    if vecID_dynamicarea_counter_dictionary.get(vecID)[0] != area or vecID_dynamicarea_counter_dictionary.get(vecID)[1] != counter:
        vecID_dynamicarea_counter_dictionary[vecID] = (area, counter)


def reset_dynamicarea_counter(vecID):
    if vecID_dynamicarea_counter_dictionary.get(vecID)[0] != AREA_INIT or vecID_dynamicarea_counter_dictionary.get(vecID)[1] != 0:
        vecID_dynamicarea_counter_dictionary[vecID] = (AREA_INIT, 0)


""" * ********************************************************************************************************************************************************************* * """


def getCoordinateCartesianeEdges(destEdgeID, curr_lane_index):
    index_calculated = get_index_calculated(destEdgeID, curr_lane_index)
    tuplaXY = traci.simulation.convert2D(destEdgeID, 0.0, index_calculated, False)
    return tuplaXY


""" * ********************************************************************************************************************************************************************* * """


def getvehicleXML():
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    listvec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        listvec_xml.append(vec_xml)
    return listvec_xml


""" * ********************************************************************************************************************************************************************* * """


def get_laneXML_form_edgeID_index(edgeID, index):
    tree = ElementTree.parse('san_francisco.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


def get_indexesXML_form_edgeID(edgeID):
    tree = ElementTree.parse('san_francisco.net.xml')
    root = tree.getroot()
    list_indexes = []
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        list_indexes.append(int(name.attrib['index']))
    return list_indexes


def get_index_calculated(edgeID, curr_lane_index):
    list_indexes = get_indexesXML_form_edgeID(edgeID)
    if curr_lane_index != 0 and curr_lane_index in list_indexes:
        return curr_lane_index
    else:
        return 0


""" * ********************************************************************************************************************************************************************* * """


def get_destinationXML(vecID):
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[len(list_edges) - 1]
    return None


""" * ********************************************************************************************************************************************************************* * """


def get_departXML(vecID):
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[0]
    return None


""" * ********************************************************************************************************************************************************************* * """


def get_distance_tolast(curr_edgeID, last_edgeID, curr_position):
    if curr_edgeID == last_edgeID:
        distance_tolast_edge = 0.0
    else:
        distance_tolast_edge = traci.simulation.getDistanceRoad(curr_edgeID, curr_position, last_edgeID, 0.0, True)

    return distance_tolast_edge


""" * ********************************************************************************************************************************************************************* * """


def get_parkingID(laneID):
    return lane_parking_dictionary.get(laneID)


""" * ********************************************************************************************************************************************************************* * """


def check_parkingaviability(parkingID):
    parking_capacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
    parking_occupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
    if parking_occupancy < parking_capacity:
        return True
    return False

def check_parking_already_setted(vecID, parkingID):
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
            print(traci.simulation.getArrivedIDList(), file=file)
            file.close()


""" * ********************************************************************************************************************************************************************* * """


def send_to_destinationXML(vecID):
    currRouteList = traci.vehicle.getRoute(vecID)
    currLastEdgeID = currRouteList[len(currRouteList) - 1]
    destinationEdgeXML = get_destinationXML(vecID)
    if currLastEdgeID != destinationEdgeXML:
        traci.vehicle.changeTarget(vecID, destinationEdgeXML)
        traci.vehicle.setColor(vecID, (255, 255, 0))


def send_to_departXML(vecID):
    currRouteList = traci.vehicle.getRoute(vecID)
    currLastEdgeID = currRouteList[len(currRouteList) - 1]
    departEdgeXML = get_departXML(vecID)
    if currLastEdgeID != departEdgeXML:
        traci.vehicle.changeTarget(vecID, departEdgeXML)
        traci.vehicle.setColor(vecID, (255, 255, 0))


def assign_coordinate_todestinationXML(vecID, curr_lane_index):
    if destedges_tupleposXY_dictionary.get(vecID) is None:
        tuplaXY = getCoordinateCartesianeEdges(get_destinationXML(vecID), curr_lane_index)
        destedges_tupleposXY_dictionary[vecID] = tuplaXY


""" * ********************************************************************************************************************************************************************* * """


# (vecID, (counter_step, started))
vec_searchtime_dictionary = {}


def load_vec_searchtime_dictionary():
    tree = ElementTree.parse('san_francisco.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle"):
        vecID = elem.attrib['id']
        vec_searchtime_dictionary[vecID] = (0, False)


def update_vec_searchtime_dictionary(vecID, counter, started):
    vec_searchtime_dictionary[vecID] = (counter, started)


def reset_vec_searchtime_dictionary(vecID):
    if vec_searchtime_dictionary.get(vecID)[0] != 0 or vec_searchtime_dictionary.get(vecID)[1] is not False:
        vec_searchtime_dictionary[vecID] = (0, False)


def check_timeslice(vecID, count):
    if count == TIME_SLICE:
        if vecID_dynamicarea_counter_dictionary.get(vecID)[1] < 3:
            print("     *** Aumento la superficie perchè sono passati", TIME_SLICE, "steps ***")
            update_dynamicarea_counter(vecID, vecID_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
            update_vec_searchtime_dictionary(vecID, 0, True)
        else:
            destination_edgeXML = get_destinationXML(vecID)
            print("     Sono passati", TIME_SLICE, "steps")
            print("     Il veicolo ritornerà alla sua destinazione iniziale: " + str(destination_edgeXML) + " perchè NON è possibile aumentare la superficie")
            send_to_destinationXML(vecID)
            reset_dynamicarea_counter(vecID)
            reset_vec_searchtime_dictionary(vecID)


""" * ********************************************************************************************************************************************************************* * """


def get_available_edges(list_tuple_links, vecID, currLaneIndex, laneID):
    tupla_vec = vecID_dynamicarea_counter_dictionary.get(vecID)
    curr_area = tupla_vec[0]

    destedges_posXY = destedges_tupleposXY_dictionary.get(vecID)
    limitInfX = destedges_posXY[0] - curr_area / 2
    limitInfY = destedges_posXY[1] - curr_area / 2
    limitSupX = destedges_posXY[0] + curr_area / 2
    limitSupY = destedges_posXY[1] + curr_area / 2

    list_available = []
    for i in range(0, len(list_tuple_links)):
        temp_tuple = list_tuple_links[i]
        temp_lane = temp_tuple[0]

        if temp_lane != laneID:
            temp_edge = traci.lane.getEdgeID(temp_lane)

            # Recupero le coordinate di currEdg che sto esaminando
            curr_tupleXY = getCoordinateCartesianeEdges(temp_edge, currLaneIndex)
            currX = curr_tupleXY[0]
            currY = curr_tupleXY[1]

            if limitInfX <= currX <= limitSupX and limitInfY <= currY <= limitSupY:
                list_available.append(temp_edge)
        else:
            continue

    return list_available


def search_random_edge_for_parking(laneID, vecID, curr_lane_index, curr_laneID):
    # Veicolo alla ricerca di un parcheggio
    traci.vehicle.setColor(vecID, (255, 0, 0))

    # Notifico che da questo momento il veicolo sta cercando parcheggio
    update_vec_searchtime_dictionary(vecID, vec_searchtime_dictionary.get(vecID)[0], True)

    num_links = traci.lane.getLinkNumber(laneID)
    list_tuple_links = traci.lane.getLinks(laneID)  # Una lista di tuple

    if num_links >= 1:
        list_available_edgs = get_available_edges(list_tuple_links, vecID, curr_lane_index, curr_laneID)

        if len(list_available_edgs) > 0:
            random_edgID = random.choice(list_available_edgs)
            traci.vehicle.changeTarget(vecID, random_edgID)
            print("     Il veicolo ha scelto casualemente " + random_edgID)
        else:

            exit_while = False
            while vecID_dynamicarea_counter_dictionary.get(vecID)[1] < 3 and exit_while is False:
                print("     *** Aumento la superficie di ricerca perchè non ci sono strade disponibili in quest'area di ricerca ***")
                update_dynamicarea_counter(vecID, vecID_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
                update_vec_searchtime_dictionary(vecID, 0, True)

                list_available_edgs = get_available_edges(list_tuple_links, vecID, curr_lane_index, curr_laneID)

                if len(list_available_edgs) > 0:
                    random_edgID = random.choice(list_available_edgs)
                    traci.vehicle.changeTarget(vecID, random_edgID)
                    print("     Il veicolo ha scelto casualemente " + random_edgID)
                    exit_while = True

            if vecID_dynamicarea_counter_dictionary.get(vecID)[1] >= 3 and exit_while is False:
                dest_edgeID = get_destinationXML(vecID)
                if laneID != get_laneXML_form_edgeID_index(dest_edgeID, curr_lane_index):
                    print("     Il veicolo non può aumentare ancora la superficie per trovare una strada, tornerà alla sua destinazione iniziale", dest_edgeID)
                    send_to_destinationXML(vecID)
                    reset_dynamicarea_counter(vecID)
                    reset_vec_searchtime_dictionary(vecID)
    else:
        # Non c'è nessuna strada collegata a quella corrente
        print("######### NON CI SONO PIU' STRADE FISICAMENTE PERCORRIBILI, USCIERO' DALLA SIMULAZIONE ######### ")


""" * ********************************************************************************************************************************************************************* * """


def critical_routine(vecID, set_vec_parking_destinationXML, curr_edgeID, curr_last_edgeID, curr_last_laneID, curr_lane_index, curr_laneID):
    print("    # [CRITICAL ROUTINE] >>> Il veicolo è arrivato a destinazione", curr_edgeID, " == (", curr_last_edgeID, ") ***")

    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    assign_coordinate_todestinationXML(vecID, curr_lane_index)

    # Controllo se il veicolo ha trovato parcheggio nella strada di destinazione XML e se è tornato al suo indirizzo di partenza XML
    if vecID in set_vec_parking_destinationXML and curr_last_edgeID == get_departXML(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        send_to_destinationXML(vecID)

    else:
        # Il veicolo è alla ricerca di un parcheggio
        traci.vehicle.setColor(vecID, (255, 0, 0))

        # Controllo se nella lane di destinazione corrente c'è un parcheggio
        parkingID = get_parkingID(curr_last_laneID)
        if parkingID is not None:
            print("     Ho trovato:" + str(parkingID))

            # Il veicolo ha trovato parcheggio
            traci.vehicle.setColor(vecID, (0, 255, 0))

            if check_parkingaviability(parkingID):
                try:
                    # Controllo se il veicolo ha trovato parcheggio PROPRIO nella sua destinazione XML
                    # laneDestinationXML != currLastLaneID poichè currLastLaneID cambia di percorso in percorso
                    destination_edgeXML = get_destinationXML(vecID)
                    lane_destinationXML = get_laneXML_form_edgeID_index(destination_edgeXML, curr_lane_index)
                    lane_parking = traci.parkingarea.getLaneID(parkingID)

                    if lane_parking == lane_destinationXML:
                        set_vec_parking_destinationXML.add(vecID)

                    if check_parking_already_setted(vecID, parkingID) is False:
                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                    reset_vec_searchtime_dictionary(vecID)
                except traci.TraCIException as e:
                    print("     Non è riuscito a parcheggiare a causa di un'eccezione", e)
                    search_random_edge_for_parking(curr_last_laneID, vecID, curr_lane_index, curr_laneID)
            else:
                print("     Non è riuscito a parcheggiare a causa della disponibilità")
                search_random_edge_for_parking(curr_last_laneID, vecID, curr_lane_index, curr_laneID)
        else:
            print("     Il veicolo non ha trovato parcheggio nella strada " + str(curr_last_edgeID) + " , alla lane " + str(curr_last_laneID))
            search_random_edge_for_parking(curr_last_laneID, vecID, curr_lane_index, curr_laneID)


""" * ********************************************************************************************************************************************************************* * """


def normal_routine(vecID, set_vec_parking_destinationXML, curr_edgeID, curr_laneID, curr_lane_index):
    print("    # [NORMAL ROUTINE] >>> Il veicolo è arrivato a destinazione (" + curr_edgeID + ") ***")

    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    assign_coordinate_todestinationXML(vecID, curr_lane_index)

    # Controllo se il veicolo ha trovato parcheggio nella strada di destinazione XML e se è tornato al suo indirizzo di partenza XML
    if vecID in set_vec_parking_destinationXML and curr_edgeID == get_departXML(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        send_to_destinationXML(vecID)
    else:

        # Il veicolo è alla ricerca di un parcheggio
        traci.vehicle.setColor(vecID, (255, 0, 0))

        # Controllo se nella lane di destinazione corrente c'è un parcheggio
        parkingID = get_parkingID(curr_laneID)
        if parkingID is not None:
            print("    Ho trovato:" + str(parkingID))
            # Il veicolo ha trovato parcheggio
            traci.vehicle.setColor(vecID, (0, 255, 0))

            if check_parkingaviability(parkingID):
                try:
                    # Controllo se il veicolo ha trovato parcheggio PROPRIO nella sua destinazione XML
                    # laneDestinationXML != currLastLaneID poichè currLastLaneID cambia di percorso in percorso
                    destination_edgeXML = get_destinationXML(vecID)
                    lane_destinationXML = get_laneXML_form_edgeID_index(destination_edgeXML, curr_lane_index)
                    lane_parking = traci.parkingarea.getLaneID(parkingID)

                    if lane_parking == lane_destinationXML:
                        set_vec_parking_destinationXML.add(vecID)

                    if check_parking_already_setted(vecID, parkingID) is False:
                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                    reset_vec_searchtime_dictionary(vecID)

                except traci.TraCIException as e:
                    print("     Non è riuscito a parcheggiare a causa di un'eccezione", e)
                    search_random_edge_for_parking(curr_laneID, vecID, curr_lane_index, curr_laneID)
            else:
                print("     Non è riuscito a parcheggiare a causa della disponibilità")
                search_random_edge_for_parking(curr_laneID, vecID, curr_lane_index, curr_laneID)
        else:
            print("     Il veicolo non ha trovato parcheggio nella strada " + curr_edgeID + " , alla lane " + curr_laneID)
            search_random_edge_for_parking(curr_laneID, vecID, curr_lane_index, curr_laneID)


""" * ********************************************************************************************************************************************************************* * """


def run():
    load_dynamicarea_counter_dictionary(AREA_INIT)
    load_lane_parking_dictionary()
    load_vec_searchtime_dictionary()
    set_vec_park_destinationXML = set()

    step = traci.simulation.getTime()  # step = 0.0

    while traci.simulation.getMinExpectedNumber() != 0 and step <= 500:

        check_exit_vec(step)
        curr_vehicles_List = traci.vehicle.getIDList()

        for vecID in curr_vehicles_List:
            print("\n # VEC_ID: [" + vecID + "]")
            print("    # (currArea, counter):", vecID_dynamicarea_counter_dictionary.get(vecID))
            print("    # (counter_step, started):", vec_searchtime_dictionary.get(vecID))

            # SE IL VEICOLO NON È ATTUALMENTE PARCHEGGIATO
            if traci.vehicle.isStoppedParking(vecID) is False:

                started_research = vec_searchtime_dictionary.get(vecID)[1]
                if started_research is True:
                    count_timeslice = vec_searchtime_dictionary.get(vecID)[0] + 1
                    update_vec_searchtime_dictionary(vecID, count_timeslice, True)
                    check_timeslice(vecID, count_timeslice)

                curr_route_list = traci.vehicle.getRoute(vecID)
                curr_last_edgeID = curr_route_list[len(curr_route_list) - 1]

                curr_laneID = traci.vehicle.getLaneID(vecID)
                curr_position = traci.vehicle.getLanePosition(vecID)
                curr_speed = traci.vehicle.getSpeed(vecID)
                curr_acc = traci.vehicle.getAcceleration(vecID)
                curr_edgeID = traci.lane.getEdgeID(curr_laneID)
                curr_lane_index = traci.vehicle.getLaneIndex(vecID)

                distanceToLastEdge = get_distance_tolast(curr_edgeID, curr_last_edgeID, curr_position)

                leader_speed = traci.vehicle.getAllowedSpeed(vecID)
                min_gap = traci.vehicle.getMinGap(vecID)
                max_decel = traci.vehicle.getDecel(vecID)

                # Limite superiore della velocità nel prossimo step
                # space_on_next_step = (1 / 2 * abs(curr_acc) * 1) + (curr_speed * 1)
                space_on_next_step = traci.vehicle.getFollowSpeed(vecID, curr_speed, min_gap, leader_speed, max_decel)

                print("    # curr_speed:", curr_speed, " , curr_acc:", curr_acc)
                print("    # currEdge:", curr_edgeID, ", lastEdge:", curr_last_edgeID)
                print("    # currLane:", curr_laneID, ", LaneIndex:", curr_lane_index)
                print("    # distance_to_last:", distanceToLastEdge)
                print("    # space_on_next_step:", space_on_next_step)

                # ___ CRITICAL ROUTINE ___ #
                if space_on_next_step >= distanceToLastEdge and curr_edgeID != curr_last_edgeID:
                    index_calculated = get_index_calculated(curr_last_edgeID, curr_lane_index)
                    curr_last_laneID = get_laneXML_form_edgeID_index(curr_last_edgeID, index_calculated)
                    critical_routine(vecID, set_vec_park_destinationXML, curr_edgeID, curr_last_edgeID, curr_last_laneID, curr_lane_index, curr_laneID)

                # ___ NORMAL ROUTINE ___ #
                elif space_on_next_step >= distanceToLastEdge and curr_edgeID == curr_last_edgeID:
                    normal_routine(vecID, set_vec_park_destinationXML, curr_edgeID, curr_laneID, curr_lane_index)

                # ___ TRIP ROUTINE ___ #
                else:
                    print("     Sto viaggindo...")
            else:
                # SE IL VEICOLO E' ATTUALMENTE PARCHEGGIATO
                print("     Il veicolo è attualmente parcheggiato!...")

                if vecID in set_vec_park_destinationXML:
                    send_to_departXML(vecID)
                    print("     Il veicolo ritornerà alla sua partenza: " + get_departXML(vecID))
                else:
                    send_to_destinationXML(vecID)
                    print("     Il veicolo ritornerà alla sua destinazione iniziale: " + get_destinationXML(vecID))

                reset_dynamicarea_counter(vecID)

        traci.simulation.step()
        step = traci.simulation.getTime()  # step ++  # traci.time.sleep(0.5)


""" * ********************************************************************************************************************************************************************* * """


def main():
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumoBinary = checkBinary('sumo-gui')
    sumoCmd = [sumoBinary, "-c", "san_francisco.sumocfg", "--start"]

    traci.start(sumoCmd)
    run()
    traci.close()


if __name__ == "__main__":
    main()
