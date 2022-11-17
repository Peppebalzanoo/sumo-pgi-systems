#!/usr/bin/python
import os, sys, traci
import random
from sumolib import checkBinary
import xml.etree.ElementTree as ET

# E' il numero di veicoli totali della simulazione (che conosco già)
NUMBER = 1
insieme = set()

# (edgeID, districtID)
edgeDistrict_Dictionary = {}


def loadEdgeDistrictDictionary():
    tree = ET.parse('districts.taz.xml')
    root = tree.getroot()
    for dis in root.findall('taz'):
        currdistrictID = dis.get("id")
        currStringEdgesID = dis.get("edges")
        if currStringEdgesID is not None:
            currListEdges = currStringEdgesID.split()
            for edgeID in currListEdges:
                edgeDistrict_Dictionary[str(edgeID)] = currdistrictID


# (districtID, listEdgeIDs)
districtListEdgesDictionary = {}


def loadDistrictListEdgesDictionary():
    tree = ET.parse('districts.taz.xml')
    root = tree.getroot()
    for dis in root.findall('taz'):
        currdistrictID = dis.get("id")
        currStringEdgesID = dis.get("edges")
        if currStringEdgesID is not None:
            currListEdges = currStringEdgesID.split()
            districtListEdgesDictionary[currdistrictID] = currListEdges
        else:
            districtListEdgesDictionary[currdistrictID] = []


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


def getListDistrictID():
    listDistrictID = []
    tree = ET.parse('districts.taz.xml')
    root = tree.getroot()
    for dis in root.findall('taz'):
        districtID = dis.get('id')
        listDistrictID.append(districtID)
    return listDistrictID


def getLaneFromEdgeIDAndIndex(edgeID, index):
    tree = ET.parse('network.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


def checkAviableEdgDstr(listLinks, districtID):
    i = 0
    while i < len(listLinks):
        currTupl = listLinks[i]
        currLan = currTupl[0]
        currEdg = traci.lane.getEdgeID(currLan)
        currDis = edgeDistrict_Dictionary.get(currEdg)
        if currDis == districtID:
            return True
        i = i + 1
    return False


def getAviabilityEdgDstr(listLinks, districtID, currEdgeID, lastEdgeID):
    i = 0
    listRet = []
    while i < len(listLinks):
        currTupl = listLinks[i]
        currLan = currTupl[0]
        currEdg = traci.lane.getEdgeID(currLan)
        currDis = edgeDistrict_Dictionary.get(currEdg)
        if currDis == districtID and currEdg != currEdgeID and currEdg != lastEdgeID:
            listRet.append(currEdg)
        i = i + 1
    return listRet


def getDestinationXML(vecID):
    tree = ET.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            listEdges = temp.split()
            return listEdges[len(listEdges) - 1]
    return None


"""def getEdgeXML(vecID):
    tree = ET.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            listEdges = temp.split()
            return listEdges[len(listEdges) - 2]
    return None"""


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
            #print("DistanceToLastEdge: " + str(distanceToLastEdge))

        except traci.TraCIException as e:
            print("********************** [EXCEPTION]: " + str(e) + " **********************")
            traci.time.sleep(10)
            distanceToLastEdge = 0.0

    return distanceToLastEdge


def getSpace(currAcc, currSpeed):
    return (0.5 * currAcc * 1) + (currSpeed * 1)


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
    tree = ET.parse('network.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        return name.attrib['length']


def searchOtherParking(desEdgeID, laneID, vecID, currEdgeID, lastEdgeID):
    traci.vehicle.setColor(vecID, (255, 0, 0))
    num = traci.lane.getLinkNumber(laneID)
    listLinks = traci.lane.getLinks(laneID)  # Una lista di tuple
    destinationDistrict = edgeDistrict_Dictionary.get(desEdgeID)

    if num >= 1:
        listAvibleEdge = getAviabilityEdgDstr(listLinks, destinationDistrict, currEdgeID, lastEdgeID)

        print("     Può scegliere:" + str(listAvibleEdge))

        if len(listAvibleEdge) == 0:
            depart = getDepartXML(vecID)
            print("     Non ci sono destinazioni valide, ritorno alla strada di partenza... " + str(depart))
            # print("Change Target 8")
            traci.vehicle.changeTarget(vecID, depart)
            traci.vehicle.setColor(vecID, (0, 0, 255))
            insieme.add(vecID)

        else:
            randomEdgeID = random.choice(listAvibleEdge)
            currDis = edgeDistrict_Dictionary[randomEdgeID]

            if currDis == destinationDistrict and currEdgeID != randomEdgeID and lastEdgeID != randomEdgeID:
                # print("Change Target 9")
                traci.vehicle.changeTarget(vecID, randomEdgeID)
            else:
                while currDis != destinationDistrict or currEdgeID == randomEdgeID or lastEdgeID == randomEdgeID:
                    randomEdgeID = random.choice(listAvibleEdge)
                    currDis = edgeDistrict_Dictionary[randomEdgeID]

                # print("Change Target 10")
                traci.vehicle.changeTarget(vecID, randomEdgeID)
    else:

        print("     Non ci sono più strade perccoribili")
        # print("Change Target 11")
        traci.vehicle.changeTarget(vecID, getDepartXML(vecID))


def getRifDistanceXML(vecID):
    return traci.simulation.getDistanceRoad(getDepartXML(vecID), 0.0, getDestinationXML(vecID), 0.0, True)

def run():
    loadLaneDictionary()
    loadParkingVecDictionary()
    loadEdgeDistrictDictionary()
    loadDistrictListEdgesDictionary()
    step = 0.0


    while traci.simulation.getMinExpectedNumber() != 0:
        count = traci.vehicle.getIDCount()

        print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")

        currVehiclesList = traci.vehicle.getIDList()

        for vecID in currVehiclesList:
            print("\n - VEC_ID: [" + vecID + "]")

            currRouteList = traci.vehicle.getRoute(vecID)
            lastEdgeID = currRouteList[len(currRouteList) - 1]

            # Controllo se il veicolo in questo step NON è già parcheggiato
            if not traci.vehicle.isStoppedParking(vecID):
                # print("[1]")
                currLaneID = traci.vehicle.getLaneID(vecID)
                currPosition = traci.vehicle.getLanePosition(vecID)
                currSpeed = traci.vehicle.getSpeed(vecID)
                currAcc = traci.vehicle.getAcceleration(vecID)
                currEdgeID = traci.lane.getEdgeID(currLaneID)
                currLength = traci.lane.getLength(currLaneID)
                currLaneIndex = traci.vehicle.getLaneIndex(vecID)

                lastLaneID = getLaneFromEdgeIDAndIndex(lastEdgeID, currLaneIndex)
                lengthLastLane = getLengthLastEdge(lastEdgeID)

                distanceToLastEdge = getDistanceToLast(currEdgeID, lastEdgeID, currPosition)

                spaceForSecond = currPosition + getSpace(currAcc, currSpeed)


                print("currEdge: "+str(currEdgeID)+" , currLane: "+str(currLaneID)+" , lastEdge: "+str(lastEdgeID))
                print("Distance To Last: "+str(distanceToLastEdge)+", spaceForSecond: " + str(spaceForSecond))

                # print("currRoute: "+str(traci.vehicle.getRoute(vecID)))

                # ____SITUAZIONE CRITICA____ #
                if spaceForSecond >= distanceToLastEdge and currEdgeID != lastEdgeID:

                    print("     [CRITICAL] Il veicolo è arrivato a destinazione " + currEdgeID + "<-->(" + lastEdgeID + ")")


                    if vecID in insieme and lastEdgeID == getDepartXML(vecID):
                        insieme.remove(vecID)
                        # print("Change Target 1")
                        traci.vehicle.changeTarget(vecID, getDestinationXML(vecID))
                        traci.vehicle.setColor(vecID, (255, 255, 0))
                    else:
                        traci.vehicle.setColor(vecID, (0, 255, 0))
                        # Controllo se il veicolo NON si è già parcheggiato almeno 1 volta
                        if not checkOneTimeParking(vecID):
                            parkingID = getParking(lastLaneID)
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
                                            # print("VEICOLO AGGIUNTO, PARCHEGGIO NELLA STRADA DI DESTINAZIONE")

                                        traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                                        if vecID in traci.simulation.getParkingStartingVehiclesIDList():
                                            parkingVec_Dictionary[vecID] = True

                                    except traci.TraCIException:
                                        print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                                        searchOtherParking(lastEdgeID, lastLaneID, vecID, currEdgeID, lastEdgeID)
                                else:
                                    print("     Non è riuscito a parcheggiare a causa della disponibilità")
                                    searchOtherParking(lastEdgeID, lastLaneID, vecID, currEdgeID, lastEdgeID)

                            else:
                                print("     Il veicolo non ha trovato parcheggio nella strada " + str(
                                    lastEdgeID) + " , alla lane " + str(lastLaneID))
                                print("     Cerco parcheggio su altre strade...")
                                searchOtherParking(lastEdgeID, lastLaneID, vecID, currEdgeID, lastEdgeID)

                        else:  # Il veicolo si è parcheggiato ALMENO 1 volta
                            des = getDestinationXML(vecID)

                            print("     Il veicolo già si è parcheggiato ALMENO 1 volta, ora ritornerà alla sua destinazione iniziale: " + str(des))
                            print("Change Target 2")
                            traci.vehicle.changeTarget(vecID, des)
                            traci.vehicle.setColor(vecID, (255, 255, 0))
                else:
                    # ____SITUAZIONI non CRITICHE____ #
                    if spaceForSecond >= distanceToLastEdge and currEdgeID == lastEdgeID:
                        print("     [NOT CRITICAL] Il veicolo è arrivato a destinazione (" + lastEdgeID + ")")

                        traci.vehicle.setColor(vecID, (0, 255, 0))

                        if vecID in insieme and currEdgeID == getDepartXML(vecID):
                            insieme.remove(vecID)

                            # print("     Veicolo RIMOSSO 2")
                            # print("Change Target 3")
                            traci.vehicle.changeTarget(vecID, getDestinationXML(vecID))
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

                                                # print("VEICOLO AGGIUNTO, PARCHEGGIO NELLA STRADA DI DESTINAZIONE")

                                            traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)

                                            if vecID in traci.simulation.getParkingStartingVehiclesIDList():
                                                parkingVec_Dictionary[vecID] = True

                                        except traci.TraCIException:
                                            print("     Non è riuscito a parcheggiare a causa di un'eccezione")

                                            searchOtherParking(currEdgeID, lastLaneID, vecID, currEdgeID, lastEdgeID)
                                    else:
                                        print("     Non è riuscito a parcheggiare a causa della disponibilità")

                                        searchOtherParking(currEdgeID, lastLaneID, vecID, currEdgeID, lastEdgeID)
                                else:
                                    print( "     Il veicolo non ha trovato parcheggio nella strada " + lastEdgeID + " , alla lane " + lastLaneID)
                                    print("     Cerco parcheggio su altre strade...")

                                    searchOtherParking(currEdgeID, lastLaneID, vecID, currEdgeID, lastEdgeID)

                            else:  # Il veicolo si è parcheggiato ALMENO 1 volta
                                des = getDestinationXML(vecID)

                                print("     Il veicolo già si è parcheggiato ALMENO 1 volta, ora ritornerà alla sua destinazione iniziale: " + str(des))
                                # print("Change Target 4")
                                traci.vehicle.changeTarget(vecID, des)
                                traci.vehicle.setColor(vecID, (255, 255, 0))
                    else:
                        print("     Sto viaggindo...")
            else:
                if vecID in insieme:
                    # print("Change Target 5")
                    traci.vehicle.changeTarget(vecID, getDepartXML(vecID))
                    traci.vehicle.setColor(vecID, (255, 255, 0))
                else:
                    des = getDestinationXML(vecID)
                    # print("Change Target 6")
                    traci.vehicle.changeTarget(vecID, des)
                    traci.vehicle.setColor(vecID, (255, 255, 0))
                    parkingVec_Dictionary[vecID] = False

        step = step + 1
        traci.simulation.step()
        #traci.time.sleep(0.2)
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
