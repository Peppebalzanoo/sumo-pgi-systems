#!/usr/bin/python
import os
import random
import sys
import xml.etree.ElementTree as ElementTree

import traci
from sumolib import checkBinary

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

# (vecID, parked)
vec_isparked_dictionary = {}


def load_vec_isparked_dictionary():
    for vecID in getvehicleXML():
        vec_isparked_dictionary[vecID] = False


""" * ********************************************************************************************************************************************************************* * """

# (vecID, (lato, count_espansione) )
vecID_dynamicarea_counter_dictionary = {}


def load_dynamicarea_counter(val):
    for vecID in getvehicleXML():
        vecID_dynamicarea_counter_dictionary[vecID] = (val, 0)


""" * ********************************************************************************************************************************************************************* * """


def getCoordinateCartesianeEdges(destEdgeID, curr_lane_index):
    tuplaXY = traci.simulation.convert2D(destEdgeID, 0.0, curr_lane_index, False)
    return tuplaXY


""" * ********************************************************************************************************************************************************************* * """


def getvehicleXML():
    tree = ElementTree.parse('elem.rou.xml')
    root = tree.getroot()
    listvec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        listvec_xml.append(vec_xml)
    return listvec_xml


""" * ********************************************************************************************************************************************************************* * """


def get_laneXML_form_edgeID_index(edgeID, index):
    tree = ElementTree.parse('network1_3.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


""" * ********************************************************************************************************************************************************************* * """


def get_destinationXML(vecID):
    tree = ElementTree.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            list_edges = temp.split()
            return list_edges[len(list_edges) - 1]
    return None


""" * ********************************************************************************************************************************************************************* * """


def get_departXML(vecID):
    tree = ElementTree.parse('elem.rou.xml')
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


def check_parked(vecID):
    if not vec_isparked_dictionary.get(vecID):
        return False
    return True


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


""" * ********************************************************************************************************************************************************************* * """


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

def search_parking(laneID, vecID, curr_lane_index):
    # Veicolo alla ricerca di un parcheggio
    traci.vehicle.setColor(vecID, (255, 0, 0))

    num_links = traci.lane.getLinkNumber(laneID)
    list_tuple_links = traci.lane.getLinks(laneID)  # Una lista di tuple

    if num_links >= 1:
        # C'è almeno una strada percorribile
        list_available_edgs = get_available_edges(list_tuple_links, vecID, curr_lane_index)
        if len(list_available_edgs) > 0:
            random_edgID = random.choice(list_available_edgs)
            traci.vehicle.changeTarget(vecID, random_edgID)
            print("     Il veicolo ha scelto casualemente " + random_edgID)
        else:
            print("     *** Aumento la superficie, non ci sono strade perccorribili per tale superficie ***")
            # Raddoppio la superficie corrente in cui cercare
            while vecID_dynamicarea_counter_dictionary.get(vecID)[1] < 3:
                vecID_dynamicarea_counter_dictionary[vecID] = (vecID_dynamicarea_counter_dictionary.get(vecID)[0] * 2, vecID_dynamicarea_counter_dictionary.get(vecID)[1] + 1)
                print("     currLato:", vecID_dynamicarea_counter_dictionary.get(vecID)[0])
                list_available_edgs = get_available_edges(list_tuple_links, vecID, curr_lane_index)
                if len(list_available_edgs) > 0:
                    random_edgID = random.choice(list_available_edgs)
                    traci.vehicle.changeTarget(vecID, random_edgID)
                    print("     Il veicolo ha scelto casualemente " + random_edgID)
                    break


            if vecID_dynamicarea_counter_dictionary.get(vecID)[1] >= 3:
                print("     Non posso aumentare ancora la superficie, ritorno alla destinazione iniziale ", get_destinationXML(vecID))
                traci.vehicle.changeTarget(vecID, get_destinationXML(vecID))
                traci.vehicle.setColor(vecID, (255, 255, 0))
    else:
        print("###### NON CI SONO PIU' STRADE FISICAMENTE PERCORRIBILI, USCIERO' DALLA SIMULAZIONE ###")


""" * ********************************************************************************************************************************************************************* * """


def reset_dynamicarea_counter(vecID):
    vecID_dynamicarea_counter_dictionary[vecID] = (50, 0)


""" * ********************************************************************************************************************************************************************* * """


def critical_routine(vecID, set_vec_parking_destinationXML, curr_edgeID, curr_last_edgeID, curr_last_laneID, curr_lane_Index):
    print("     *** CRITICAL ROUTINE *** >>> Il veicolo è arrivato a destinazione", curr_edgeID, " == (", curr_last_edgeID, ")")
    traci.vehicle.setColor(vecID, (0, 255, 0))

    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    if destedges_tupleposXY_dictionary.get(vecID) is None:
        tuplaXY = getCoordinateCartesianeEdges(get_destinationXML(vecID), curr_lane_Index)
        destedges_tupleposXY_dictionary[vecID] = tuplaXY
    print("    ", curr_edgeID, " == (", curr_last_edgeID, ")", " coordinate (X,Y) : ", destedges_tupleposXY_dictionary[vecID])

    # Controllo se il veicolo corrente è uno di quei veicolo che ha trovato parcheggio (si è parcheggiato) nella strada di destinazione XML
    # E se è tornato al suo indirizzo di partenza XML
    if vecID in set_vec_parking_destinationXML and curr_last_edgeID == get_departXML(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        traci.vehicle.changeTarget(vecID, get_destinationXML(vecID))
        traci.vehicle.setColor(vecID, (255, 255, 0))

    else:
        # Controllo se il veicolo NON si è già parcheggiato almeno 1 volta, se non ha aumentato più di 3 volte la superficie e se non sono passati 10 secondi
        if not check_parked(vecID) and vecID_dynamicarea_counter_dictionary.get(vecID)[1] < 3:

            # Il veicolo è alla ricerca di un parcheggio
            traci.vehicle.setColor(vecID, (255, 0, 0))

            parkingID = get_parkingID(curr_last_laneID)

            # Controllo se nella lane di destinazione corrente c'è un parcheggio
            if parkingID is not None:
                print("     Ho trovato:" + str(parkingID))

                # Il veicolo ha trovato parcheggio
                traci.vehicle.setColor(vecID, (0, 255, 0))

                if check_parkingaviability(parkingID):
                    try:
                        # Controllo se il veicolo ha trovato parcheggio PROPRIO nella sua destinazione XML
                        # laneDestinationXML != currLastLaneID poichè currLastLaneID cambia di percorso in percorso
                        destination_edgeXML = get_destinationXML(vecID)
                        lane_destinationXML = get_laneXML_form_edgeID_index(destination_edgeXML, curr_lane_Index)
                        lane_parking = traci.parkingarea.getLaneID(parkingID)

                        if lane_parking == lane_destinationXML:
                            set_vec_parking_destinationXML.add(vecID)

                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)


                        vec_isparked_dictionary[vecID] = True

                    except traci.TraCIException:
                        print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                        search_parking(curr_last_laneID, vecID, curr_lane_Index)
                else:
                    print("     Non è riuscito a parcheggiare a causa della disponibilità")
                    search_parking(curr_last_laneID, vecID, curr_lane_Index)

            else:
                print("     Il veicolo non ha trovato parcheggio nella strada " + str(curr_last_edgeID) + " , alla lane " + str(curr_last_laneID))
                search_parking(curr_last_laneID, vecID, curr_lane_Index)

        else:
            # Il veicolo si è parcheggiato ALMENO 1 volta (aumentando o meno la superficie)

            # Controllo se il veicolo ha aumentato almeno una volta la dimensione della superficie in cui cercare
            if vecID_dynamicarea_counter_dictionary.get(vecID)[1] > 0:
                reset_dynamicarea_counter(vecID)
                print("     Il veicolo ha resettato i suoi valori")

            destination_edgeXML = get_destinationXML(vecID)

            print("     Il veicolo ritornerà alla sua destinazione iniziale: " + str(destination_edgeXML))
            traci.vehicle.changeTarget(vecID, destination_edgeXML)
            traci.vehicle.setColor(vecID, (255, 255, 0))


""" * ********************************************************************************************************************************************************************* * """


def normal_routine(vecID, set_vec_parking_destinationXML, curr_edgeID, curr_laneID, curr_lane_Index):
    print("     *** NORMAL ROUTINE *** >>> Il veicolo è arrivato a destinazione (" + curr_edgeID + ")")
    traci.vehicle.setColor(vecID, (0, 255, 0))

    # Assegno al veicolo le coordinate (X,Y) del suo indirizzo di destinazione XML
    if destedges_tupleposXY_dictionary.get(vecID) is None:
        tuplaXY = getCoordinateCartesianeEdges(get_destinationXML(vecID), curr_lane_Index)
        destedges_tupleposXY_dictionary[vecID] = tuplaXY
    print("    ", curr_edgeID, " coordinate (X,Y) : ", destedges_tupleposXY_dictionary[vecID])

    # Controllo se il veicolo corrente è uno di quei veicolo che ha trovato parcheggio (si è parcheggiato) nella strada di destinazione XML
    # E se è tornato al suo indirizzo di partenza XML
    if vecID in set_vec_parking_destinationXML and curr_edgeID == get_departXML(vecID):
        set_vec_parking_destinationXML.remove(vecID)
        traci.vehicle.changeTarget(vecID, get_destinationXML(vecID))
        traci.vehicle.setColor(vecID, (255, 255, 0))

    else:

        # Controllo se il veicolo NON si è già parcheggiato ALMENO 1 volta, se non ha aumentato più di 3 volte la superficie e se non sono passati 10 secondi
        if not check_parked(vecID) and vecID_dynamicarea_counter_dictionary.get(vecID)[1] < 3:

            # Il veicolo è alla ricerca di un parcheggio
            traci.vehicle.setColor(vecID, (255, 0, 0))

            parkingID = get_parkingID(curr_laneID)

            # Controllo se nella lane di destinazione corrente c'è un parcheggio
            if parkingID is not None:
                print("     Cerco parcheggio su questa strada... ho trovato:" + str(parkingID))

                # Il veicolo ha trovato parcheggio
                traci.vehicle.setColor(vecID, (0, 255, 0))

                if check_parkingaviability(parkingID):
                    try:
                        # Controllo se il veicolo ha trovato parcheggio PROPRIO nella sua destinazione XML
                        # laneDestinationXML != currLastLaneID poichè currLastLaneID cambia di percorso in percorso
                        destination_edgeXML = get_destinationXML(vecID)
                        lane_destinationXML = get_laneXML_form_edgeID_index(destination_edgeXML, curr_lane_Index)
                        lane_parking = traci.parkingarea.getLaneID(parkingID)

                        if lane_parking == lane_destinationXML:
                            set_vec_parking_destinationXML.add(vecID)

                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)


                        vec_isparked_dictionary[vecID] = True

                    except traci.TraCIException:
                        print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                        search_parking(curr_laneID, vecID, curr_lane_Index)
                else:
                    print("     Non è riuscito a parcheggiare a causa della disponibilità")
                    search_parking(curr_laneID, vecID, curr_lane_Index)
            else:
                print("     Il veicolo non ha trovato parcheggio nella strada " + curr_edgeID + " , alla lane " + curr_laneID)
                search_parking(curr_laneID, vecID, curr_lane_Index)

        else:
            # Il veicolo si è parcheggiato ALMENO 1 volta (aumentando o meno la superficie)

            # Controllo se il veicolo ha aumentato almeno una volta la dimensione della superficie in cui cercare

            if vecID_dynamicarea_counter_dictionary.get(vecID)[1] > 0:
                reset_dynamicarea_counter(vecID)
                print("     Il veicolo ha resettato i suoi valori")

            destination_edgeXML = get_destinationXML(vecID)

            print("     Il veicolo ritornerà alla sua destinazione iniziale: " + str(destination_edgeXML))
            traci.vehicle.changeTarget(vecID, destination_edgeXML)
            traci.vehicle.setColor(vecID, (255, 255, 0))


""" * ********************************************************************************************************************************************************************* * """


def check_exit_vec(step):
    count = traci.vehicle.getIDCount()
    print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")
    # Controllo se qualche veicolo ha lasciato la simulazione
    if (len(traci.simulation.getArrivedIDList())) > 0:
        print(traci.simulation.getArrivedIDList())
        traci.time.sleep(5)


""" * ********************************************************************************************************************************************************************* * """


def run():
    load_dynamicarea_counter(50)
    load_lane_parking_dictionary()
    load_vec_isparked_dictionary()


    step = 0.0
    set_vec_parking_destinationXML = set()

    while traci.simulation.getMinExpectedNumber() != 0:

        check_exit_vec(step)

        currVehiclesList = traci.vehicle.getIDList()

        for vecID in currVehiclesList:
            print("\n - VEC_ID: [" + vecID + "]")
            print("     currLato:", (vecID_dynamicarea_counter_dictionary.get(vecID)[0]), " currCountIncrement:", (vecID_dynamicarea_counter_dictionary.get(vecID)[1]))

            currRouteList = traci.vehicle.getRoute(vecID)
            currLastEdgeID = currRouteList[len(currRouteList) - 1]

            # Controllo se il veicolo in questo step NON è già parcheggiato
            if not traci.vehicle.isStoppedParking(vecID):

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
                print("     currPosition:", currPosition, ", currLaneIndex:", currLaneIndex)
                print("     currAcc: ", currAcc, " , currSpeed:", currSpeed)
                print("     Distance To Last:", distanceToLastEdge, " spaceForSecond:", spaceForSecond)

                # CRITICAL ROUTINE #
                if spaceForSecond >= distanceToLastEdge and currEdgeID != currLastEdgeID:
                    currLastLaneID = get_laneXML_form_edgeID_index(currLastEdgeID, currLaneIndex)
                    critical_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLastEdgeID, currLastLaneID, currLaneIndex)



                # NORMAL ROUTINE #
                elif spaceForSecond >= distanceToLastEdge and currEdgeID == currLastEdgeID:
                    normal_routine(vecID, set_vec_parking_destinationXML, currEdgeID, currLaneID, currLaneIndex)



                # TRIP ROUTINE #
                else:
                    print("     Sto viaggindo...")

            # Se il veicolo in questo step è GIA' parcheggiato
            else:

                # - Controllo se è uno di quei veicoli che ha parcheggiato nella strada di destinazione XML
                #   In tal caso il veicolo deve tornare al suo inidirzzo di paretenza XML (non è possibile farlo tornare al suo indirizzo di destinazione XML, poichè già vi è)
                if vecID in set_vec_parking_destinationXML:
                    traci.vehicle.changeTarget(vecID, get_departXML(vecID))
                else:
                    # - Altrimenti, il veicolo è parcheggiato in questo step
                    #   In tal caso il veicolo deve tornare al suo indirizzo di destinazione XML
                    destinationEdgeXML = get_destinationXML(vecID)
                    traci.vehicle.changeTarget(vecID, destinationEdgeXML)

                traci.vehicle.setColor(vecID, (255, 255, 0))
                vec_isparked_dictionary[vecID] = False
                reset_dynamicarea_counter(vecID)


        step = step + 1
        traci.simulation.step()
        # traci.time.sleep(0.5)
        print("\n #### #### ####")


""" * ********************************************************************************************************************************************************************* * """


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