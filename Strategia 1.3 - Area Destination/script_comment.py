
"""#!/usr/bin/python

import os
import random
import sys
import xml.etree.ElementTree as ElementTree

import traci
from sumolib import checkBinary

AREA_INIT = 50
TIME_SLICE = 10

# (vecID, lastparkingID)
vec_lastparkingID = {}

# (destEdgeID, tuplaXY)
destedges_tupleposXY_dictionary = {}

# * ********************************************************************************************************************************************************************* *

# (currLaneID, parkingID)
lane_parking_dictionary = {}


def load_lane_parking_dictionary():
    parkingIDs_list = traci.parkingarea.getIDList()
    for parkingID in parkingIDs_list:
        curr_laneID = traci.parkingarea.getLaneID(parkingID)
        lane_parking_dictionary[curr_laneID] = parkingID


# * ********************************************************************************************************************************************************************* *

# (vecID, (isparked, parkingID)
vec_isparked_dictionary = {}


def load_vec_isparked_dictionary():
    for vecID in getvehicleXML():
        vec_isparked_dictionary[vecID] = False


# * ********************************************************************************************************************************************************************* *

# (vecID, (lato, count_espansione) )
vecID_dynamicarea_counter_dictionary = {}


def load_dynamicarea_counter(val):
    for vecID in getvehicleXML():
        vecID_dynamicarea_counter_dictionary[vecID] = (val, 0)


def update_dynamicarea_counter(vecID, area, counter):
    if vecID_dynamicarea_counter_dictionary.get(vecID)[0] != area or vecID_dynamicarea_counter_dictionary.get(vecID)[1] != counter:
        print("[UPDATE] currArea(currArea, counter):", vecID_dynamicarea_counter_dictionary.get(vecID))
        vecID_dynamicarea_counter_dictionary[vecID] = (area, counter)


def reset_dynamicarea_counter(vecID):
    if vecID_dynamicarea_counter_dictionary.get(vecID)[0] != AREA_INIT or vecID_dynamicarea_counter_dictionary.get(vecID)[1] != 0:
        print("[INFO]: called reset_dynamicarea_counter")
        vecID_dynamicarea_counter_dictionary[vecID] = (AREA_INIT, 0)


# * ********************************************************************************************************************************************************************* *


def getCoordinateCartesianeEdges(destEdgeID, curr_lane_index):
    tuplaXY = traci.simulation.convert2D(destEdgeID, 0.0, curr_lane_index, False)
    return tuplaXY


# * ********************************************************************************************************************************************************************* *


def getvehicleXML():
    tree = ElementTree.parse('elem.rou.xml')
    root = tree.getroot()
    listvec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        listvec_xml.append(vec_xml)
    return listvec_xml


# * ********************************************************************************************************************************************************************* *


def get_laneXML_form_edgeID_index(edgeID, index):
    tree = ElementTree.parse('network1_3.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


# * ********************************************************************************************************************************************************************* *


def get_destinationXML(vecID):
    tree = ElementTree.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[len(list_edges) - 1]
    return None


# * ********************************************************************************************************************************************************************* *


def get_departXML(vecID):
    tree = ElementTree.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[0]
    return None


def get_one_node_vehicle():
    vec_xml = getvehicleXML()
    tree = ElementTree.parse('elem.rou.xml')
    root = tree.getroot()
    list_ret = []
    for vec in vec_xml:
        for elem in root.findall(".//vehicle/[@id='" + vec + "']//route"):
            temp = elem.get("edges")
            if temp is not None:
                list_edges = temp.split()
                if len(list_edges) == 1:
                    list_ret.append(vec)
    return list_ret


def select_random_node(vecID):
    parkingID = vec_lastparkingID.get(vecID)
    laneID = traci.parkingarea.getLaneID(parkingID)
    num_links = traci.lane.getLinkNumber(laneID)
    list_tuple_links = traci.lane.getLinks(laneID)  # Una lista di tuple
    if num_links >= 1:
        list_available_edgs = []
        for i in range(0, len(list_tuple_links)):
            temp_tuple = list_tuple_links[i]
            temp_lane = temp_tuple[0]
            temp_edge = traci.lane.getEdgeID(temp_lane)
            list_available_edgs.append(temp_edge)
        print("     list_available_edgs:", list_available_edgs)
        if len(list_available_edgs) > 0:
            random_edgID = random.choice(list_available_edgs)
            traci.vehicle.changeTarget(vecID, random_edgID)
            print("     Il veicolo ha scelto casualemente " + random_edgID)


# * ********************************************************************************************************************************************************************* *


def get_distance_tolast(curr_edgeID, last_edgeID, curr_position):
    if curr_edgeID == last_edgeID:
        distance_tolast_edge = 0.0
    else:
        distance_tolast_edge = traci.simulation.getDistanceRoad(curr_edgeID, curr_position, last_edgeID, 0.0, True)

    return distance_tolast_edge


# * ********************************************************************************************************************************************************************* *


def check_parked(vecID):
    if not vec_isparked_dictionary.get(vecID):
        return False
    return True


# * ********************************************************************************************************************************************************************* *


def get_parkingID(laneID):
    return lane_parking_dictionary.get(laneID)


# * ********************************************************************************************************************************************************************* *


def check_parkingaviability(parkingID):
    parking_capacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
    parking_occupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
    if parking_occupancy < parking_capacity:
        return True
    return False


# * ********************************************************************************************************************************************************************* *


def check_exit_vec(step):
    if step == 0.0:
        count = traci.vehicle.getIDCount()
        print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")
        traci.time.sleep(2)
    else:
        count = traci.vehicle.getIDCount()
        print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")
        # Controllo se qualche veicolo ha lasciato la simulazione
        if (len(traci.simulation.getArrivedIDList())) > 0:
            print(traci.simulation.getArrivedIDList())
            traci.time.sleep(5)


# * ********************************************************************************************************************************************************************* *


def send_to_destinationXML(vecID):
    currRouteList = traci.vehicle.getRoute(vecID)
    currLastEdgeID = currRouteList[len(currRouteList) - 1]
    destinationEdgeXML = get_destinationXML(vecID)
    if currLastEdgeID != destinationEdgeXML:
        traci.vehicle.changeTarget(vecID, destinationEdgeXML)
        traci.vehicle.setColor(vecID, (255, 255, 0))
        print("[INFO]: called send_to_destinationXML")


def send_to_departXML(vecID):
    currRouteList = traci.vehicle.getRoute(vecID)
    currLastEdgeID = currRouteList[len(currRouteList) - 1]
    departEdgeXML = get_departXML(vecID)
    if currLastEdgeID != departEdgeXML:
        traci.vehicle.changeTarget(vecID, departEdgeXML)
        traci.vehicle.setColor(vecID, (255, 255, 0))
        print("[INFO]: called send_to_departXML")


def assign_coordinate_todestinationXML(vecID, curr_lane_index, curr_edgeID):
    if destedges_tupleposXY_dictionary.get(vecID) is None:
        tuplaXY = getCoordinateCartesianeEdges(get_destinationXML(vecID), curr_lane_index)
        destedges_tupleposXY_dictionary[vecID] = tuplaXY


# * ********************************************************************************************************************************************************************* *


def get_available_edges(list_tuple_links, vecID, currLaneIndex):
    tupla_vec = vecID_dynamicarea_counter_dictionary.get(vecID)
    lato = tupla_vec[0]

    destedges_posXY = destedges_tupleposXY_dictionary.get(vecID)
    limitInfX = destedges_posXY[0] - lato / 2
    limitInfY = destedges_posXY[1] - lato / 2
    limitSupX = destedges_posXY[0] + lato / 2
    limitSupY = destedges_posXY[1] + lato / 2

    list_available = []
    for i in range(0, len(list_tuple_links)):
        temp_tuple = list_tuple_links[i]
        temp_lane = temp_tuple[0]
        temp_edge = traci.lane.getEdgeID(temp_lane)

        # Recupero le coordinate di currEdg che sto esaminando
        curr_tupleXY = getCoordinateCartesianeEdges(temp_edge, currLaneIndex)
        currX = curr_tupleXY[0]
        currY = curr_tupleXY[1]

        # Devo assicurarmi che tempEdge non sia il mio indirizzo di partenza XML perchè non voglio che il veicolo si possa parcheggiare in esso
        # if temp_edge != getDepartXML(vecID) and limitInfX <= currX <= limitSupX and limitInfY <= currY <= limitSupY:
        if limitInfX <= currX <= limitSupX and limitInfY <= currY <= limitSupY:
            list_available.append(temp_edge)

    return list_available


# Devo forzare il veicolo a girovagare casualemente solo per la superficie corrente
# Girovagando deve trovare parcheggio per le strade che perccorre
# Se per un quanto di tempo non trova parcheggio, ne incremento la superficie in cui cercare

def search_random_edge_for_parking(laneID, vecID, curr_lane_index, step):
    # Veicolo alla ricerca di un parcheggio
    traci.vehicle.setColor(vecID, (255, 0, 0))

    # Notifico che da questo momento il veicolo sta cercando parcheggio
    update_vec_searchtime_dictionary(vecID, vec_searchtime_dictionary.get(vecID)[0], True)

    num_links = traci.lane.getLinkNumber(laneID)
    list_tuple_links = traci.lane.getLinks(laneID)  # Una lista di tuple

    if num_links >= 1:
        # C'è almeno una strada collegata a quella corrente
        list_available_edgs = get_available_edges(list_tuple_links, vecID, curr_lane_index)
        print("     list_available_edgs:", list_available_edgs)
        if len(list_available_edgs) > 0:
            random_edgID = random.choice(list_available_edgs)
            traci.vehicle.changeTarget(vecID, random_edgID)
            print("     Il veicolo ha scelto casualemente " + random_edgID)
        else:
            exit_while = False
            while vecID_dynamicarea_counter_dictionary.get(vecID)[1] < 3 and exit_while is False:
                print("     *** Aumento la superficie di ricerca ***")
                update_dynamicarea_counter(vecID, vecID_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
                update_vec_searchtime_dictionary(vecID, 0, True)

                list_available_edgs = get_available_edges(list_tuple_links, vecID, curr_lane_index)
                print("     list_available_edgs:", list_available_edgs)
                if len(list_available_edgs) > 0:
                    random_edgID = random.choice(list_available_edgs)
                    traci.vehicle.changeTarget(vecID, random_edgID)
                    print("     Il veicolo ha scelto casualemente " + random_edgID)
                    exit_while = True

            if vecID_dynamicarea_counter_dictionary.get(vecID)[1] >= 3 and exit_while is False:
                print("     Il veicolo non può aumentare ancora la superficie per trovare una strada, ritornerà alla destinazione iniziale ", get_destinationXML(vecID))
                send_to_destinationXML(vecID)
                reset_dynamicarea_counter(vecID)
                reset_vec_searchtime_dictionary(vecID)
    else:
        # Non c'è nessuna strada collegata a quella corrente
        print("######### NON CI SONO PIU' STRADE FISICAMENTE PERCORRIBILI, USCIERO' DALLA SIMULAZIONE ######### ")


# * ********************************************************************************************************************************************************************* *

# (vecID, (counter_step, started))
vec_searchtime_dictionary = {}


def load_vec_searchtime_dictionary():
    tree = ElementTree.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle"):
        vecID = elem.attrib['id']
        vec_searchtime_dictionary[vecID] = (0, False)


def update_vec_searchtime_dictionary(vecID, counter, started):
    vec_searchtime_dictionary[vecID] = (counter, started)
    print("[UPDATE] currTime(counter_step, is_started):", vec_searchtime_dictionary[vecID])


def reset_vec_searchtime_dictionary(vecID):
    if vec_searchtime_dictionary.get(vecID)[0] != 0 or vec_searchtime_dictionary.get(vecID)[1] is not False:
        print("[INFO]: called reset_vec_searchtime_dictionary")
        vec_searchtime_dictionary[vecID] = (0, False)


def check_timeslice(vecID, count):
    if count == TIME_SLICE:
        if vecID_dynamicarea_counter_dictionary.get(vecID)[1] < 3:
            print("     *** Aumento la superficie perchè sono passati", TIME_SLICE, "steps ***")
            update_dynamicarea_counter(vecID, vecID_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
            update_vec_searchtime_dictionary(vecID, 0, True)
        else:
            destination_edgeXML = get_destinationXML(vecID)
            print("     Il veicolo ritornerà alla sua destinazione iniziale: " + str(destination_edgeXML) + " perchè NON è possibile aumentare la superficie")
            send_to_destinationXML(vecID)
            reset_dynamicarea_counter(vecID)
            reset_vec_searchtime_dictionary(vecID)


# * ********************************************************************************************************************************************************************* *


def critical_routine(vecID, set_vec_parking_destinationXML, curr_edgeID, curr_last_edgeID, curr_last_laneID, curr_lane_index, step):
    print("     *** [CRITICAL ROUTINE] *** >>> Il veicolo è arrivato a destinazione", curr_edgeID, " == (", curr_last_edgeID, ")")

    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    assign_coordinate_todestinationXML(vecID, curr_lane_index, curr_edgeID)

    # Controllo se il veicolo corrente è uno di quei veicolo che ha trovato parcheggio nella strada di destinazione XML
    # E se è tornato al suo indirizzo di partenza XML
    if vecID in set_vec_parking_destinationXML and curr_last_edgeID == get_departXML(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        send_to_destinationXML(vecID)

    else:
        # Se il veicolo NON si è parcheggiato MAI
        if check_parked(vecID) is False:

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

                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)
                        vec_lastparkingID[vecID] = parkingID

                        reset_vec_searchtime_dictionary(vecID)

                    except traci.TraCIException:
                        print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                        search_random_edge_for_parking(curr_last_laneID, vecID, curr_lane_index, step)
                else:
                    print("     Non è riuscito a parcheggiare a causa della disponibilità")
                    search_random_edge_for_parking(curr_last_laneID, vecID, curr_lane_index, step)

            else:
                print("     Il veicolo non ha trovato parcheggio nella strada " + str(curr_last_edgeID) + " , alla lane " + str(curr_last_laneID))
                search_random_edge_for_parking(curr_last_laneID, vecID, curr_lane_index, step)

        # Se il veicolo si è parcheggiato già 1 volta ed è arrivato alla sua corrente destinazione
        else:
            print("     Il veicolo si è parcheggiato già 1 volta ed è arrivato alla sua nuova destinazione")
            vec_isparked_dictionary[vecID] = False


# * ********************************************************************************************************************************************************************* *


def normal_routine(vecID, set_vec_parking_destinationXML, curr_edgeID, curr_laneID, curr_lane_index, step):
    print("     *** [NORMAL ROUTINE] *** >>> Il veicolo è arrivato a destinazione (" + curr_edgeID + ")")

    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    assign_coordinate_todestinationXML(vecID, curr_lane_index, curr_edgeID)

    # CONTROLLO SE IL VEICOLO CORRENTE È UNO DI QUEI VEICOLO CHE HA TROVATO PARCHEGGIO
    # NELLA STRADA DI DESTINAZIONE XML E CHE È ARRIVATO AL SUO INDIRIZZO DI PARTENZA XML
    if vecID in set_vec_parking_destinationXML and curr_edgeID == get_departXML(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        send_to_destinationXML(vecID)
    else:

        # Se il veicolo NON si è parcheggiato MAI
        if check_parked(vecID) is False:

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

                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)
                        vec_lastparkingID[vecID] = parkingID

                        reset_vec_searchtime_dictionary(vecID)

                    except traci.TraCIException:
                        print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                        search_random_edge_for_parking(curr_laneID, vecID, curr_lane_index, step)
                else:
                    print("     Non è riuscito a parcheggiare a causa della disponibilità")
                    search_random_edge_for_parking(curr_laneID, vecID, curr_lane_index, step)
            else:
                print("     Il veicolo non ha trovato parcheggio nella strada " + curr_edgeID + " , alla lane " + curr_laneID)
                search_random_edge_for_parking(curr_laneID, vecID, curr_lane_index, step)

        # Se il veicolo si è parcheggiato già 1 volta ed è arrivato alla sua corrente destinazione
        else:
            print("     Il veicolo si è parcheggiato già 1 volta ed è arrivato alla sua nuova destinazione")
            vec_isparked_dictionary[vecID] = False
            traci.time.sleep(10)


# * ********************************************************************************************************************************************************************* *


def run():
    load_dynamicarea_counter(AREA_INIT)
    load_lane_parking_dictionary()
    load_vec_isparked_dictionary()

    load_vec_searchtime_dictionary()

    step = 0.0
    set_vec_parking_destinationXML = set()
    list_one_node_vec = get_one_node_vehicle()
    print("list_one_node_vec:", list_one_node_vec)

    while traci.simulation.getMinExpectedNumber() != 0:

        check_exit_vec(step)
        currVehiclesList = traci.vehicle.getIDList()

        print(vec_isparked_dictionary)

        for vecID in currVehiclesList:
            print("\n - VEC_ID: [" + vecID + "]")
            print("     currArea(currArea, counter):", vecID_dynamicarea_counter_dictionary.get(vecID))
            print("     currTime(counter_step, is_started):", vec_searchtime_dictionary.get(vecID))

            currRouteList = traci.vehicle.getRoute(vecID)
            currLastEdgeID = currRouteList[len(currRouteList) - 1]

            # SE IL VEICOLO NON È ATTUALMENTE PARCHEGGIATO
            if traci.vehicle.isStoppedParking(vecID) is False:

                started_research = vec_searchtime_dictionary.get(vecID)[1]
                if started_research is True:
                    count = vec_searchtime_dictionary.get(vecID)[0] + 1
                    update_vec_searchtime_dictionary(vecID, count, True)
                    check_timeslice(vecID, count)
                    currRouteList = traci.vehicle.getRoute(vecID)
                    currLastEdgeID = currRouteList[len(currRouteList) - 1]

                currLaneID = traci.vehicle.getLaneID(vecID)
                currPosition = traci.vehicle.getLanePosition(vecID)
                currSpeed = traci.vehicle.getSpeed(vecID)
                currAcc = traci.vehicle.getAcceleration(vecID)
                currEdgeID = traci.lane.getEdgeID(currLaneID)
                currLaneIndex = traci.vehicle.getLaneIndex(vecID)

                distanceToLastEdge = get_distance_tolast(currEdgeID, currLastEdgeID, currPosition)

                # spaceForSecond è una stima che suppone che l'accelerazione currAcc resti costante tra lo step corrente e il prossimo
                spaceForSecond = (1 / 2 * abs(currAcc) * 1) + (currSpeed * 1)

                print("     currEdge:", currEdgeID, " , currLane:", currLaneID, ", lastEdge:", currLastEdgeID)
                print("     Distance To Last:", distanceToLastEdge, " spaceForSecond:", spaceForSecond)

                # ___ CRITICAL ROUTINE ___ #
                if spaceForSecond >= distanceToLastEdge and currEdgeID != currLastEdgeID:
                    if vecID not in list_one_node_vec:
                        currLastLaneID = get_laneXML_form_edgeID_index(currLastEdgeID, currLaneIndex)
                        critical_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLastEdgeID, currLastLaneID, currLaneIndex, step)
                    else:
                        # E' arrivato a destinazione iniziale
                        if currLastEdgeID == get_departXML(vecID):
                            currLastLaneID = get_laneXML_form_edgeID_index(currLastEdgeID, currLaneIndex)
                            critical_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLastEdgeID, currLastLaneID, currLaneIndex, step)
                        else:
                            # E' arrivato a destinazione NON iniziale e si è già parcheggiato 1 volta
                            if check_parked(vecID) is True:
                                traci.vehicle.changeTarget(vecID, get_departXML(vecID))
                            else:
                                currLastLaneID = get_laneXML_form_edgeID_index(currLastEdgeID, currLaneIndex)
                                critical_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLastEdgeID, currLastLaneID, currLaneIndex, step)




                # ___ NORMAL ROUTINE ___ #
                elif spaceForSecond >= distanceToLastEdge and currEdgeID == currLastEdgeID:
                    if vecID not in list_one_node_vec:
                        normal_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLaneID, currLaneIndex, step)
                    else:
                        # E' arrivato a destinazione iniziale
                        if currEdgeID == get_departXML(vecID):
                            normal_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLaneID, currLaneIndex, step)
                        else:
                            # E' arrivato a destinazione NON iniziale e si è già parcheggiato 1 volta
                            if check_parked(vecID) is True:
                                traci.vehicle.changeTarget(vecID, get_departXML(vecID))
                            else:
                                normal_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLaneID, currLaneIndex, step)


                # ___ TRIP ROUTINE ___ #
                else:
                    print("     Sto viaggindo...")

            else:

                # SE IL VEICOLO E' ATTUALMENTE PARCHEGGIATO
                print("     Il veicolo è attualmente parcheggiato!")
                vec_isparked_dictionary[vecID] = True

                if vecID not in list_one_node_vec:
                    if vecID in set_vec_parking_destinationXML:
                        send_to_departXML(vecID)
                        print("     Il veicolo ritornerà alla sua partenza: " + get_departXML(vecID))
                    else:
                        send_to_destinationXML(vecID)
                        print("     Il veicolo ritornerà alla sua destinazione iniziale: " + get_destinationXML(vecID))
                else:
                    if currRouteList[len(currRouteList) - 1] == get_departXML(vecID):
                        print("[INFO]: CALLED select_random_node")
                        select_random_node(vecID)

                reset_dynamicarea_counter(vecID)

        step = step + 1
        # traci.time.sleep(0.5)
        traci.simulation.step()


# * ********************************************************************************************************************************************************************* *


def main():
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumoBinary = checkBinary('sumo-gui')
    sumoCmd = [sumoBinary, "-c", "main.sumocfg", "--start"]

    traci.start(sumoCmd)
    run()
    traci.close()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
    """