#!/usr/bin/python
import os
import random
import sys
import xml.etree.ElementTree as ET

import traci
from ordered_set import OrderedSet
from sumolib import checkBinary

# E' il numero di veicoli totali della simulazione (che conosco già)
NUMBER = 1
VAL = 50
insieme = set()


# (currLaneID, parkingID)
lane_Dictionary = {}


def loadLaneDictionary():
    parkingListIDs = traci.parkingarea.getIDList()
    for parkingID in parkingListIDs:
        currLaneID = traci.parkingarea.getLaneID(parkingID)
        lane_Dictionary[currLaneID] = parkingID


# (vecID, parked)
parkingVec_Dictionary = {}


def loadParkingVecDictionary():
    for i in range(0, NUMBER):
        parkingVec_Dictionary[str(i)] = False


# (parkingID, tuplaXY)
parking_Position_Dict = {}


def coordinateCartesianeParking():
    parkingListIDs = traci.parkingarea.getIDList()
    for parkingID in parkingListIDs:
        startPosition = traci.parkingarea.getStartPos(parkingID)
        currLaneID = traci.parkingarea.getLaneID(parkingID)
        edgeID = traci.lane.getEdgeID(currLaneID)
        currIndex = getIndexFromNetXML(edgeID, currLaneID)
        tuplaParkingXY = traci.simulation.convert2D(edgeID, startPosition, int(currIndex), False)
        parking_Position_Dict[parkingID] = tuplaParkingXY



def getLaneFromEdgeIDAndIndex(edgeID, index):
    tree = ET.parse('network1_2.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


def getDestinationXML(vecID):
    tree = ET.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            listEdges = temp.split()
            return listEdges[len(listEdges) - 1]
    return None


def getDepartXML(vecID):
    tree = ET.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            listEdges = temp.split()
            return listEdges[0]
    return None


def getRouteXML(vecID):
    tree = ET.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            listEdges = temp.split()
            return listEdges
    return None


def getDistanceToLast(currEdgeID, lastEdgeID, currPosition):
    if currEdgeID == lastEdgeID:
        distanceToLastEdge = 0.0
    else:
        try:
            distanceToLastEdge = traci.simulation.getDistanceRoad(currEdgeID, currPosition, lastEdgeID, 0.0, True)
            # print("DistanceToLastEdge: " + str(distanceToLastEdge))

        except traci.TraCIException as e:
            print("********************** [EXCEPTION]: " + str(e) + " **********************")
            traci.time.sleep(5)
            distanceToLastEdge = 0.0

    return distanceToLastEdge


# (vecID, tuplaX = (startX, endX))
dizionario = {}

def loadDizionario():
    startX = 0.0
    for i in range(0, NUMBER):
        lengthLastEdge = getLengthLastEdge(getDestinationXML(str(i)))
        if lengthLastEdge is not None:
            endX = traci.simulation.getDistanceRoad(getDepartXML(str(i)), 0.0, getDestinationXML(str(i)), float(lengthLastEdge), True)
            tuplaXstartXend = (startX, endX)
            print("TuplaXstartXend: \n" + str(tuplaXstartXend))
            dizionario[str(i)] = tuplaXstartXend
        else:
            print("*********************** Errore ***********************")


"""def getSpaceForSecond(currPosition, currAcc, currSpeed, currEdgeID, lastEdgeID, vecID):
    spaceForSecond = (0.5 * (currAcc) * 1) + currSpeed
    return spaceForSecond"""


def checkOneTimeParking(vecID):
    if not parkingVec_Dictionary.get(vecID):
        return False
    return True


def getParking(laneID):
    return lane_Dictionary.get(laneID)


def getLaneIDFormParking(parkingID):
    tree = ET.parse('parking.xml')
    root = tree.getroot()
    for elem in root.findall(".//parkingArea/[@id='" + parkingID + "']"):
        temp = elem.get("lane")
        if temp is not None:
            return temp
    return None


def checkParkingAviability(parkingID):
    parkingCapacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
    parkingOccupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
    if parkingOccupancy < parkingCapacity:
        return True
    return False


def getLengthLastEdge(edgeID):
    tree = ET.parse('network1_2.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        return name.attrib['length']


def getNearestParking(setCandidati, currEdgeID):
    firstParking = setCandidati[0]
    laneFirst = traci.parkingarea.getLaneID(firstParking)
    edgFirst = traci.lane.getEdgeID(laneFirst)
    newRouteStage = traci.simulation.findRoute(currEdgeID, edgFirst)
    minCost = newRouteStage.cost
    nearestParking = firstParking
    print("     cost: " + str(newRouteStage.cost) + " , travelTime: " + str(newRouteStage.travelTime))
    for i in range(1, len(setCandidati)):
        lan = traci.parkingarea.getLaneID(setCandidati[i])
        edg = traci.lane.getEdgeID(lan)
        newRouteStage = traci.simulation.findRoute(currEdgeID, edg)
        currCost = newRouteStage.cost
        if currCost < minCost:
            minCost = newRouteStage.cost
            nearestParking = setCandidati[i]
        print("     cost: " + str(newRouteStage.cost) + " , travelTime: " + str(newRouteStage.travelTime))
    return nearestParking


def getAviabilityEdg(listLinks, currEdgeID, lastEdgeID):
    i = 0
    listRet = []
    while i < len(listLinks):
        currTupl = listLinks[i]
        currLan = currTupl[0]
        currEdg = traci.lane.getEdgeID(currLan)
        if currEdg != currEdgeID and currEdg != lastEdgeID:
            listRet.append(currEdg)
        i = i + 1
    return listRet


def searchOtherParking(laneID, vecID, currEdgeID, lastEdgeID, setCandidati, spaceForSecond, distanceToLast, isCritical):
    # Veicolo alla ricerca di un parcheggio (Red)
    traci.vehicle.setColor(vecID, (255, 0, 0))

    currPosition = traci.vehicle.getLanePosition(vecID)
    currLaneIndex = traci.vehicle.getLaneIndex(vecID)

    vec_tuplaPosXY = traci.simulation.convert2D(currEdgeID, currPosition, currLaneIndex, False)

    """LaneID, Position of vec e Index of Lane
    vec_tuplaRoad = traci.simulation.convertRoad(vec_tuplaPosXY[0], vec_tuplaPosXY[1], False, "ignoring")"""

    limitInfX = vec_tuplaPosXY[0] - VAL/2
    limitInfY = vec_tuplaPosXY[1] - VAL/2

    limitSupX = vec_tuplaPosXY[0] + VAL/2
    limitSupY = vec_tuplaPosXY[1] + VAL/2

    for parkID, tupl in parking_Position_Dict.items():
        currX = tupl[0]
        currY = tupl[1]
        if limitInfX <= currX <= limitSupX and limitInfY <= currY <= limitSupY:
            setCandidati.add(parkID)

    print("Candidati: "+str(setCandidati))
    if len(setCandidati) > 0:
        print("     I parcheggi candidati sono: " + str(setCandidati))
        # Controllo se al prossimo step esco dalla simulazione
        if spaceForSecond >= distanceToLast and isCritical is False:
            lastParking = getNearestParking(setCandidati, currEdgeID)
            # lastParking = setCandidati.pop()
            lan = traci.parkingarea.getLaneID(lastParking)
            edg = traci.lane.getEdgeID(lan)
            traci.vehicle.changeTarget(vecID, edg)
            print("     Ho cambiato destinazione! Vado a " + edg + " per parcheggiare a " + lastParking)
            setCandidati.clear()

        elif spaceForSecond >= distanceToLast and isCritical is True:
            lastParking = getNearestParking(setCandidati, lastEdgeID)
            lan = traci.parkingarea.getLaneID(lastParking)
            edg = traci.lane.getEdgeID(lan)
            traci.vehicle.changeTarget(vecID, edg)
            print("     Ho cambiato destinazione! Vado a " + edg + " per parcheggiare a " + lastParking)
            setCandidati.clear()
    else:
        print("     Non ci sono candiati...")

        num = traci.lane.getLinkNumber(laneID)
        listLinks = traci.lane.getLinks(laneID)  # Una lista di tuple

        if num >= 1:
            print("     num: "+str(num))
            listAviabileEdg = getAviabilityEdg(listLinks, currEdgeID, lastEdgeID)
            randomEdgeID = random.choice(listAviabileEdg)
            traci.vehicle.changeTarget(vecID, randomEdgeID)
            print("     Il veicolo ha scelto casualemente " + randomEdgeID)
        else:
            print("     Non ci sono più strade perccoribili")
            traci.vehicle.changeTarget(vecID, getDepartXML(vecID))


def getIndexFromNetXML(edgeID, laneID):
    tree = ET.parse('network1_2.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@id='" + laneID + "']"):
        return name.attrib['index']


def run():
    loadDizionario()
    loadLaneDictionary()
    loadParkingVecDictionary()
    step = 0.0

    coordinateCartesianeParking()

    while traci.simulation.getMinExpectedNumber() != 0:
        count = traci.vehicle.getIDCount()

        print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")

        currVehiclesList = traci.vehicle.getIDList()
        if (len(traci.simulation.getArrivedIDList())) > 0:
            print(traci.simulation.getArrivedIDList())
            traci.time.sleep(5)

        for vecID in currVehiclesList:
            print("\n - VEC_ID: [" + vecID + "]")

            currRouteList = traci.vehicle.getRoute(vecID)
            lastEdgeID = currRouteList[len(currRouteList) - 1]
            setCandidati = OrderedSet()

            # Controllo se il veicolo in questo step NON è già parcheggiato
            if not traci.vehicle.isStoppedParking(vecID):
                currLaneID = traci.vehicle.getLaneID(vecID)
                currPosition = traci.vehicle.getLanePosition(vecID)
                currSpeed = traci.vehicle.getSpeed(vecID)
                currAcc = traci.vehicle.getAcceleration(vecID)
                currEdgeID = traci.lane.getEdgeID(currLaneID)
                currLaneIndex = traci.vehicle.getLaneIndex(vecID)

                lastLaneID = getLaneFromEdgeIDAndIndex(lastEdgeID, currLaneIndex)

                distanceToLastEdge = getDistanceToLast(currEdgeID, lastEdgeID, currPosition)



                # Supponendo costante l'accelerazione, calcolo quanto spostamento potrei fare in 1 secondo
                # Se tale spostamente è >= della distanza dall'ultimo nodo del percorso, allora sono in una situazione critica
                # spaceForSecond è quindi una stima che suppone che l'accelerazione currAcc resti costante tra lo step corrente e il prossimo
                spaceForSecond = (1/2 * abs(currAcc) * 1) + (currSpeed * 1)



                print("     currEdge: " + str(currEdgeID) + " , currLane: " + str(currLaneID) + ", lastEdge: " + str(lastEdgeID))
                print("     currPosition: " + str(currPosition) + " , currLaneIndex: " + str(currLaneIndex))
                print("     currAcc: " + str(currAcc) + " , currSpeed: " + str(currSpeed))
                print("     Distance To Last: " + str(distanceToLastEdge))
                print("     spaceForSecond: " + str(spaceForSecond))


                # ____SITUAZIONE CRITICA____ #
                if spaceForSecond >= distanceToLastEdge and currEdgeID != lastEdgeID and currEdgeID != getDestinationXML(vecID):
                    print("     [CRITICAL] Il veicolo è arrivato a destinazione " + currEdgeID + "<-->(" + lastEdgeID + ")")

                    if vecID in insieme and lastEdgeID == getDepartXML(vecID):
                        insieme.remove(vecID)
                        traci.vehicle.changeTarget(vecID, getDestinationXML(vecID))
                        traci.vehicle.setColor(vecID, (255, 255, 0))

                    else:
                        # Controllo se il veicolo NON si è già parcheggiato almeno 1 volta
                        if not checkOneTimeParking(vecID):
                            parkingID = getParking(lastLaneID)
                            print("     Cerco parcheggio su questa strada...")

                            # Il veicolo è alla ricerca di un parcheggio (Red)
                            traci.vehicle.setColor(vecID, (255, 0, 0))

                            # Controllo se nella lane di destinazione corrente c'è un parcheggio
                            if parkingID is not None:
                                print("     Ho trovato:" + str(parkingID))

                                # Il veicolo ha trovato parcheggio (Green)
                                traci.vehicle.setColor(vecID, (0, 255, 0))

                                if checkParkingAviability(parkingID):
                                    try:
                                        # Controllo se il veicolo ha trovato parcheggio nella sua destinazione XML
                                        destinationEdge = getDestinationXML(vecID)
                                        laneDestination = getLaneFromEdgeIDAndIndex(destinationEdge, currLaneIndex)
                                        if getLaneIDFormParking(parkingID) == laneDestination:
                                            insieme.add(vecID)

                                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                                        if vecID in traci.simulation.getParkingStartingVehiclesIDList():
                                            parkingVec_Dictionary[vecID] = True

                                    except traci.TraCIException:
                                        print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                                        searchOtherParking(lastLaneID, vecID, currEdgeID, lastEdgeID, setCandidati, spaceForSecond, distanceToLastEdge, True)
                                else:
                                    print("     Non è riuscito a parcheggiare a causa della disponibilità")
                                    searchOtherParking(lastLaneID, vecID, currEdgeID, lastEdgeID, setCandidati, spaceForSecond, distanceToLastEdge, True)

                            else:
                                print("     Il veicolo non ha trovato parcheggio nella strada " + str(lastEdgeID) + " , alla lane " + str(lastLaneID))
                                print("     Cerco parcheggio su altre strade...")
                                searchOtherParking(lastLaneID, vecID, currEdgeID, lastEdgeID, setCandidati, spaceForSecond, distanceToLastEdge, True)

                        else:  # Il veicolo si è parcheggiato ALMENO 1 volta
                            des = getDestinationXML(vecID)

                            print("     Il veicolo già si è parcheggiato ALMENO 1 volta, ora ritornerà alla sua destinazione iniziale: " + str(des))
                            traci.vehicle.changeTarget(vecID, des)
                            traci.vehicle.setColor(vecID, (255, 255, 0))
                else:
                    # ____SITUAZIONI non CRITICHE____ #
                    if spaceForSecond >= distanceToLastEdge and currEdgeID == lastEdgeID:
                        print("     [NOT CRITICAL] Il veicolo è arrivato a destinazione (" + lastEdgeID + ")")
                        traci.vehicle.setColor(vecID, (0, 255, 0))

                        if vecID in insieme and currEdgeID == getDepartXML(vecID):
                            insieme.remove(vecID)
                            traci.vehicle.changeTarget(vecID, getDestinationXML(vecID))
                            traci.vehicle.setColor(vecID, (255, 255, 0))

                        else:
                            traci.vehicle.setColor(vecID, (0, 255, 0))
                            # Controllo se il veicolo NON si è già parcheggiato ALMENO 1 volta
                            if not checkOneTimeParking(vecID):
                                parkingID = getParking(currLaneID)
                                # Controllo se in questa lane c'è un parcheggio
                                if parkingID is not None:
                                    print("     Cerco parcheggio su questa strada... ho trovato:" + str(parkingID))

                                    if checkParkingAviability(parkingID):
                                        try:

                                            # Controllo se il veicolo ha trovato parcheggio nella sua destinazione XML
                                            destinationEdge = getDestinationXML(vecID)
                                            laneDestination = getLaneFromEdgeIDAndIndex(destinationEdge, currLaneIndex)
                                            if getLaneIDFormParking(parkingID) == laneDestination:
                                                insieme.add(vecID)

                                            traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                                            if vecID in traci.simulation.getParkingStartingVehiclesIDList():
                                                parkingVec_Dictionary[vecID] = True

                                        except traci.TraCIException:
                                            print("     Non è riuscito a parcheggiare a causa di un'eccezione")

                                            searchOtherParking(lastLaneID, vecID, currEdgeID, lastEdgeID, setCandidati, spaceForSecond, distanceToLastEdge, False)
                                    else:
                                        print("     Non è riuscito a parcheggiare a causa della disponibilità")

                                        searchOtherParking(lastLaneID, vecID, currEdgeID, lastEdgeID, setCandidati, spaceForSecond, distanceToLastEdge, False)
                                else:
                                    print(
                                        "     Il veicolo non ha trovato parcheggio nella strada " + lastEdgeID + " , alla lane " + lastLaneID,
                                        False)
                                    print("     Cerco parcheggio su altre strade...")

                                    searchOtherParking(lastLaneID, vecID, currEdgeID, lastEdgeID, setCandidati, spaceForSecond, distanceToLastEdge, False)

                            else:  # Il veicolo si è parcheggiato ALMENO 1 volta
                                des = getDestinationXML(vecID)

                                print("     Il veicolo già si è parcheggiato ALMENO 1 volta, ora ritornerà alla sua destinazione iniziale: " + str(des))
                                traci.vehicle.changeTarget(vecID, des)
                                traci.vehicle.setColor(vecID, (255, 255, 0))
                    else:
                        print("     Sto viaggindo...")
            else:
                if vecID in insieme:
                    traci.vehicle.changeTarget(vecID, getDepartXML(vecID))
                    traci.vehicle.setColor(vecID, (255, 255, 0))
                else:
                    des = getDestinationXML(vecID)
                    traci.vehicle.changeTarget(vecID, des)
                    traci.vehicle.setColor(vecID, (255, 255, 0))
                    parkingVec_Dictionary[vecID] = False

        step = step + 1
        traci.simulation.step()
        # traci.time.sleep(0.5)
        print("\n #### #### ####")


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
