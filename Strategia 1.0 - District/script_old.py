#!/usr/bin/python
import os, sys, traci
import random
from sumolib import checkBinary
import xml.etree.ElementTree as ET

# E' il numero di veicoli totali della simulazione (che conosco già)
NUMBER = 150

# (vecID, routeIndex)
""" vehicle_Dictionary = {}  """

# (currLaneID, parkingID)
lane_Dictionary = {}

# (vecID, parked)
parkingVec_Dictionary = {}

# (edgeID, districtID)
edgeDistrict_Dictionary = {}

# (districtID, listEdgesDistrict)
districtListEdgesDictionary = {}

# Questa funzione si occupa di inizializzare il dizionario vehicle_Dictionary
# aggiungendo una coppia (key = i, space = 0)
"""def loadVehicleDictionary():
    for i in range(0,NUMBER):
        vehicle_Dictionary[str(i)] = 0"""


def loadLaneDictionary():
    parkingListIDs = traci.parkingarea.getIDList()
    for parkingID in parkingListIDs:
        currLaneID = traci.parkingarea.getLaneID(parkingID)
        lane_Dictionary[currLaneID] = parkingID


def loadParkingVecDictionary():
    for i in range(0, NUMBER):
        parkingVec_Dictionary[str(i)] = False


def loadEdgeDistrictDictionary():
    tree = ET.parse('districts.taz.xml')
    root = tree.getroot()
    for dis in root.findall('taz'):
        currdistrictID = dis.get("id")
        currStringEdgesID = dis.get("edges")
        if currStringEdgesID is not None:
            currListEdgesDistrict = currStringEdgesID.split()
            for edgeID in currListEdgesDistrict:
                edgeDistrict_Dictionary[str(edgeID)] = currdistrictID


def loadDistrictListEdgesDictionary():
    tree = ET.parse('districts.taz.xml')
    root = tree.getroot()
    for dis in root.findall('taz'):
        currdistrictID = dis.get("id")
        currStringEdgesID = dis.get("edges")
        if currStringEdgesID is not None:
            currListEdgesDistrict = currStringEdgesID.split()
            districtListEdgesDictionary[currdistrictID] = currListEdgesDistrict
        else:
            districtListEdgesDictionary[currdistrictID] = []


"""def getListPolyID():
    listPolyID = []
    tree = ET.parse('poly.xml')
    root = tree.getroot()
    for pol in root.findall('poly'):
            polID = pol.get('id')
            listPolyID.append(polID)
    return listPolyID"""


def getListDistrictID():
    listDistrictID = []
    tree = ET.parse('districts.taz.xml')
    root = tree.getroot()
    for dis in root.findall('taz'):
        districtID = dis.get('id')
        listDistrictID.append(districtID)
    return listDistrictID


""""
#(lane,EdgeID)
def getLaneEdge():
    tree = ET.parse('copynet.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge//lane/[@id='E27.38_0']"):
        print(str(name.attrib))
        print(name.tag)
"""


def getLengthLastEdge(edgeID):
    tree = ET.parse('copynet.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane"):
        return name.attrib['length']


def getLaneFromEdgeIDAndIndex(edgeID, index):
    tree = ET.parse('copynet.net.xml')
    root = tree.getroot()
    for name in root.findall(".//edge/[@id='" + edgeID + "']//lane/[@index='" + str(index) + "']"):
        return name.attrib['id']


def getDestination(vecID):
    tree = ET.parse('elem.rou.xml')
    root = tree.getroot()
    for elem in root.findall(".//vehicle/[@id='" + vecID + "']//route"):
        temp = elem.get("edges")
        if temp is not None:
            listEdges = temp.split()
            return listEdges[len(listEdges) - 1]
    return None


def checkAviableEdgDstr(listLinks, districtID):
    i = 0
    while i < len(listLinks):
        currTupl = listLinks[i]
        currLan = currTupl[0]
        currEdg = traci.lane.getEdgeID(currLan)
        print("************" + currEdg)
        currDis = edgeDistrict_Dictionary.get(currEdg)
        if currDis == districtID:
            return True
        i = i + 1
    return False


def run():
    loadLaneDictionary()
    loadParkingVecDictionary()
    loadEdgeDistrictDictionary()
    loadDistrictListEdgesDictionary()
    step = 0.0

    tempMap = {}

    while traci.simulation.getMinExpectedNumber() != 0:
        traci.simulationStep()
        sys.stdout.write("\n#STEP: " + str(step) + "\n")

        currVehiclesList = traci.vehicle.getIDList()

        for vecID in currVehiclesList:
            print(" - VEC_ID: [" + vecID + "]")

            currRouteList = traci.vehicle.getRoute(vecID)
            # firstEdgeID = currRouteList[0]
            lastEdgeID = currRouteList[len(currRouteList) - 1]

            # Controllo se il veicolo corrente NON si è fermato per parcheggiare
            if not traci.vehicle.isStoppedParking(vecID):
                currLaneID = traci.vehicle.getLaneID(vecID)
                currPosition = traci.vehicle.getLanePosition(vecID)
                currSpeed = traci.vehicle.getSpeed(vecID)
                currAcc = traci.vehicle.getAcceleration(vecID)
                currEdgeID = traci.lane.getEdgeID(currLaneID)
                currLength = traci.lane.getLength(currLaneID)

                lung = getLengthLastEdge(lastEdgeID)
                index = traci.vehicle.getLaneIndex(vecID)
                lastLaneID = getLaneFromEdgeIDAndIndex(lastEdgeID, index)

                if currEdgeID == lastEdgeID:
                    distanceToLastEdge = 0.0
                else:
                    distanceToLastEdge = traci.simulation.getDistanceRoad(currEdgeID, currPosition, lastEdgeID, 0.0, True)

                space = (0.5 * currAcc * 1) + (currSpeed * 1)

                print("     currEdgeID: " + currEdgeID + " | currPosition: " + str(currPosition) + " | currLength: " + str(currLength))
                print("     space: " + str(space) + " | distance from lastEdge: " + str(distanceToLastEdge))
                print("     lastEdgeID: " + str(lastEdgeID) + " | lastEdgeLength: " + str(lung))

                """"
                1. currEdgeID == lastEdgeID (and space >=(distance = 0.0)) --> ARRIVATO
                2. currEdgeID != lastEdgeID and space >= distanceToLastEdge ---> CRITICA
                3. currEdgeID != lastEdgeID and space <= distanceToLastEdge --> NULL

                #Se nella lane di destinazione c'è il parcheggio
                """

                # SITUAZIONE CRITICA
                if space >= distanceToLastEdge and currEdgeID != lastEdgeID:  # type: ignore
                    print("***** SITUAZIONE CRITICA ****")
                    print("     Il veicolo è arrivato a destinazione " + currEdgeID + "<-->(" + lastEdgeID + ")")
                    traci.vehicle.setColor(vecID, (0, 255, 0))
                    tempMap[int(vecID)] = 0

                    if not parkingVec_Dictionary.get(vecID):
                        parkingID = lane_Dictionary.get(lastLaneID)
                        print("     Cerco parcheggio..." + str(parkingID))
                        if parkingID is not None:
                            parkingCapacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
                            parkingOccupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
                            if parkingOccupancy <= parkingCapacity:
                                try:
                                    traci.vehicle.setParkingAreaStop(vecID, parkingID, 10)
                                    parkingVec_Dictionary[vecID] = True

                                except traci.TraCIException:
                                    print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                                    traci.time.sleep(10)
                                    print("###########################################################")

                            else:
                                print("     Non è riuscito a parcheggiare perchè non c'erano posti liberi")
                                traci.time.sleep(10)
                                print("###########################################################")

                        else:
                            print("     Il veicolo non ha trovato parcheggio nella strada " + lastEdgeID+" , "+lastLaneID)
                            print("     Il veicolo cercherà parcheggio in un'altra strada")
                            index = traci.vehicle.getLaneIndex(vecID)
                            lastLaneID = getLaneFromEdgeIDAndIndex(lastEdgeID, index)
                            num = traci.lane.getLinkNumber(lastLaneID)
                            listLinks = traci.lane.getLinks(lastLaneID)  # Una lista di tuple
                            destinationDistrict = edgeDistrict_Dictionary.get(lastEdgeID)

                            if num >= 1:
                                # print(" CRITICA > 1")

                                if not checkAviableEdgDstr(listLinks, destinationDistrict):
                                    des = getDestination(vecID)
                                    print("Non ci sono destinazioni valide, ritorno all'inidirizzo di destinazione... " + str(des))
                                    traci.vehicle.changeTarget(vecID, des)
                                    traci.vehicle.setColor(vecID, (255, 0, 0))
                                else:
                                    randomTuple = random.choice(listLinks)  # E' una tupla (string, bool bool, ....,)
                                    randomLane = randomTuple[0]
                                    randomEdgeID = traci.lane.getEdgeID(randomLane)
                                    currDis = edgeDistrict_Dictionary[randomEdgeID]
                                    distance = traci.simulation.getDistanceRoad(currEdgeID, currPosition, randomEdgeID, 0.0, True)

                                    if currDis == destinationDistrict and currEdgeID != randomEdgeID and lastEdgeID != randomEdgeID:
                                        print("     La strada trovata scelta fa parte del distretto " + str(destinationDistrict))
                                        traci.vehicle.changeTarget(vecID, randomEdgeID)
                                        print("     [1] Il veicolo ha scelto casualmente la prossima strada da percorrere (" + str( randomEdgeID) + ")")
                                        print("     distance: " + str(distance))
                                    else:
                                        while currDis != destinationDistrict or currEdgeID == randomEdgeID or lastEdgeID == randomEdgeID:
                                            print("-----------------while")
                                            print("     num: " + str(num))
                                            randomTuple = random.choice(listLinks)  # E' una tupla (string, bool bool, ....,)
                                            randomLane = randomTuple[0]
                                            randomEdgeID = traci.lane.getEdgeID(randomLane)
                                            currDis = edgeDistrict_Dictionary[randomEdgeID]

                                            """
                                            print("     - currEdgeID: "+currEdgeID+" , currLaneID: "+currLaneID)
                                            print("     - destEdgeID: "+str(lastEdgeID))
                                            print("     - randomEdgeID: "+randomEdgeID+" , randomLaneID: "+randomLane)
                                            print("     - distance: "+str(distance)+" , space: "+str(space))
                                            print("     - currDis: "+str(currDis)+" , destinationDistrict "+str(destinationDistrict))"""

                                        print("     - La strada trovata scelta fa parte del distretto " + str(destinationDistrict))
                                        traci.vehicle.changeTarget(vecID, randomEdgeID)
                                        print("     [2] Il veicolo ha scelto casualmente la prossima strada da percorrere (" + str(randomEdgeID) + ")")
                            else:
                                print("     - Non ci sono più strade perccoribili")
                                traci.time.sleep(10)
                                print("###########################################################")
                    else:
                        des = getDestination(vecID)
                        print("     Il veicolo già si è parcheggiato 1 volta, ora lo faccio ritornare alla sua destinazione iniziale" + str(des))
                        traci.vehicle.changeTarget(vecID, des)
                        traci.vehicle.setColor(vecID, (255, 0, 0))
                        parkingVec_Dictionary[vecID] = False

                # SITUAZIONE NON CRITICA
                elif space >= distanceToLastEdge and currEdgeID == lastEdgeID:
                    print("--- SITUAZIONE non CRITICA ---")
                    print("     Il veicolo è arrivato a destinazione (" + lastEdgeID + ")")
                    traci.vehicle.setColor(vecID, (0, 255, 0))
                    tempMap[int(vecID)] = 0

                    if not parkingVec_Dictionary.get(vecID):
                        parkingID = lane_Dictionary.get(currLaneID)
                        print("     Cerco parcheggio..." + str(parkingID))
                        if parkingID is not None:
                            parkingCapacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
                            parkingOccupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
                            if parkingOccupancy <= parkingCapacity:
                                try:
                                    traci.vehicle.setParkingAreaStop(vecID, parkingID, 10)  # type: ignore
                                    parkingVec_Dictionary[vecID] = True

                                except traci.TraCIException:
                                    print("     Non è riuscito a parcheggiare a causa di un'eccezione")
                                    traci.time.sleep(10)
                                    print("###########################################################")
                            else:
                                print("     Non è riuscito a parcheggiare perchè non c'erano posti liberi")
                                traci.time.sleep(10)
                                print("###########################################################")

                        else:
                            print("     Il veicolo non ha trovato parcheggio nella strada " + lastEdgeID+" , "+lastLaneID)
                            print("     Il veicolo cercherà parcheggio in un'altra strada")

                            index = traci.vehicle.getLaneIndex(vecID)
                            lastEdgeID = getLaneFromEdgeIDAndIndex(currEdgeID, index)
                            num = traci.lane.getLinkNumber(currLaneID)
                            listLinks = traci.lane.getLinks(currLaneID)  # Una lista di tuple
                            destinationDistrict = edgeDistrict_Dictionary.get(currEdgeID)

                            if num >= 1:
                                print(" non CRITICA > 1")

                                if not checkAviableEdgDstr(listLinks, destinationDistrict):
                                    des = getDestination(vecID)
                                    print("Non ci sono destinazioni valide, ritorno all'inidirizzo di destinazione... " + str(des))
                                    traci.vehicle.changeTarget(vecID, des)
                                    traci.vehicle.setColor(vecID, (255, 0, 0))
                                else:
                                    randomTuple = random.choice(listLinks)  # E' una tupla (string, bool bool, ....,)
                                    randomLane = randomTuple[0]
                                    randomEdgeID = traci.lane.getEdgeID(randomLane)
                                    currDis = edgeDistrict_Dictionary[randomEdgeID]
                                    distance = traci.simulation.getDistanceRoad(currEdgeID, currPosition, randomEdgeID,0.0, True)

                                    if currDis == destinationDistrict and currEdgeID != randomEdgeID and lastEdgeID != randomEdgeID:
                                        print("     La strada trovata scelta fa parte del distretto " + str(destinationDistrict))
                                        traci.vehicle.changeTarget(vecID, randomEdgeID)
                                        print("     [4] Il veicolo ha scelto casualmente la prossima strada da percorrere (" + str(randomEdgeID) + ")")
                                        print("     distance: " + str(distance))
                                    else:
                                        while currDis != destinationDistrict or currEdgeID == randomEdgeID or lastEdgeID == randomEdgeID:
                                            # print("-----------------while")
                                            # print("     num: " + str(num))
                                            randomTuple = random.choice(listLinks)  # E' una tupla (string, bool bool, ....,)
                                            randomLane = randomTuple[0]
                                            randomEdgeID = traci.lane.getEdgeID(randomLane)
                                            currDis = edgeDistrict_Dictionary[randomEdgeID]

                                            """     
                                            print("     ^ currEdgeID: "+currEdgeID+" , currLaneID: "+currLaneID)
                                            print("     ^ destEdgeID: "+str(lastEdgeID))
                                            print("     ^ randomEdgeID: "+randomEdgeID+" , randomLaneID: "+randomLane)
                                            print("     ^ distance: "+str(distance)+" , space: "+str(space))
                                            print("     ^ currDis: "+str(currDis)+" , destinationDistrict "+str(destinationDistrict))"""

                                        print("     ^ La strada trovata scelta fa parte del distretto " + str(destinationDistrict))
                                        traci.vehicle.changeTarget(vecID, randomEdgeID)
                                        print("     [5] Il veicolo ha scelto casualmente la prossima strada da percorrere (" + str(randomEdgeID) + ")")
                            else:
                                print("     ^ Non ci sono più strade perccoribili")
                                traci.time.sleep(10)
                                print("###########################################################")
                    else:
                        des = getDestination(vecID)
                        print("     Il veicolo già si è parcheggiato 1 volta, ora lo faccio ritornare alla sua destinazione iniziale" + str(des))
                        traci.vehicle.changeTarget(vecID, des)
                        traci.vehicle.setColor(vecID, (255, 0, 0))
                        parkingVec_Dictionary[vecID] = False

                elif currEdgeID != lastEdgeID and space <= distanceToLastEdge:  # space <= distanceToLastEdge and currEdgeID != lastEdgeID
                    print("     Sto viaggindo...")
            else:
                des = getDestination(vecID)
                print("     Il veicolo è già parcheggiato e deve ritornare alla sua destinazione iniziale " + str(des))
                traci.vehicle.changeTarget(vecID, des)
                traci.vehicle.setColor(vecID, (255, 0, 0))
                parkingVec_Dictionary[vecID] = False

        step += 1
        traci.time.sleep(0.5)

    for i in sorted(tempMap):
        print((i, tempMap[i]), end=" ")
        print("")
    print(len(tempMap))


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

"""def run():
    step = 0.0
    loadLaneDictionary() 
    loadVehicleDictionary()
    loadParkingVecDictionary()
    loadEdgeDistrictDictionary()
    loadDistrictListEdgesDictionary()
    #listDistrictID = getListDistrictID()
    
    

    while (traci.simulation.getMinExpectedNumber() != 0):
        traci.simulationStep()
        
        sys.stdout.write("\n#STEP: "+str(step)+"\n")

        currVehiclesList = traci.vehicle.getIDList() 
       
        print("[1]")

        for vecID in currVehiclesList:
            print(" - VEC_ID: "+vecID)
            currVecRouteIndex = traci.vehicle.getRouteIndex(vecID)
            currRouteList = traci.vehicle.getRoute(vecID)
            DictionaryRouteIndex = vehicle_Dictionary[vecID]
            lastEdgeID = currRouteList[len(currRouteList)-1]
            
            print("     currIndex: "+str(currVecRouteIndex))
            print("     len: "+str(len(currRouteList)))
            #Controllo se dalla strada in cui sono partito, sono passato ad un'altra starda
            if(currVecRouteIndex != DictionaryRouteIndex):
                #Aggiorno nel dizionario il valore associato alla coppia (vecID, indexRoute) in quanto il veicolo si è spostato su un nuovo nodo(strada) del percorsp
                vehicle_Dictionary[vecID] = currVecRouteIndex
                print("     currRouteList: "+str(currRouteList))

            #Controllo se sono arrivato alla strada di destinazione
            if(currVecRouteIndex + 1 == len(currRouteList)):
                    
                print("     Il veicolo è arrivato a destinazione")
                #Controllo se il veicolo corrente NON si è fermato per parcheggiare
                if(traci.vehicle.isStoppedParking(vecID) == False): # type: ignore
                    currLaneID = traci.vehicle.getLaneID(vecID)
                    currEdgeID traci.lane.getEdgeID(currLaneID)
                    currDistrictID = edgeDistrict_Dictionary.get(currEdgeID
                    #Controllo se nella strada di destinazione c'è già un parcheggio
                    parkingID = lane_Dictionary.get(currLaneID, False)
                    if(parkingID != False and parkingVec_Dictionary.get(vecID) == False ): #Ho trovato il parcheggio
                        parkingCapacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
                        parkingOccupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
                        print("     Controlla parkingID: "+str(parkingID)+" , Capacità: "+parkingCapacity+" , Occupazione: "+parkingOccupancy)

                        #Controllo se il parcheggio che ho trovato ha la capacità e l'occupazione per farmi parcheggiare
                        if(parkingOccupancy < parkingCapacity):
                                try:
                                    traci.vehicle.setParkingAreaStop(vecID, parkingID, 10)  # type: ignore
                                    parkingVec_Dictionary[vecID] = True
                                except traci.TraCIException:    
                                    print("     Non è riuscito a parcheggiare")
                                    stop = False
                                    listEdgesDistrict = districtListEdgesDictionary.get(currDistrictID)
                                    if(listEdgesDistrict != None):
                                        randomEdgeID = random.choice(listEdgesDistrict)
                                        while(stop == False):
                                            if(randomEdgeID != currEdgeID
                                                newRouteStage = traci.simulation.findRoute(edgeIDLastStepandomEdgeID)
                                                print("     Nuovo percorso calcolato: [ "+str(newRouteStage.edges)+" ] per arrivare a "+randomEdgeID)
                                                print("TravelTime: "+str(newRouteStage.travelTime)+" , cost: "+str(newRouteStage.cost)+" , length: "+str(newRouteStage.length))
                                                if(newRouteStage.cost <= 5):
                                                    try:
                                                        traci.vehicle.setRoute(vecID,newRouteStage.edges)
                                                        stop = True
                                                    except traci.TraCIException:
                                                        pass
                                                else:
                                                    randomEdgeID = random.choice(listEdgesDistrict)
                                            else:
                                                randomEdgeID = random.choice(listEdgesDistrict)

                                    else:
                                        print("     Non ci sono altre strade per questo distretto")
                    elif(parkingVec_Dictionary.get(vecID) == True):
                            print("     Il veicolo ha già parcheggiato")
                    else: #parkingID == False
                        print("     Non ci sono parcheggi nella sua strada di destinazione")
                        stop = False
                        listEdgesDistrict = districtListEdgesDictionary.get(currDistrictID)
                        if(listEdgesDistrict != None):
                            randomEdgeID = random.choice(listEdgesDistrict)
                            while(stop == False):
                                if(randomEdgeID != currEdgeID
                                    newRouteStage = traci.simulation.findRoute(edgeIDLastStepandomEdgeID)
                                    print("     Nuovo percorso calcolato: [ "+str(newRouteStage.edges)+" ] per arrivare a "+randomEdgeID)
                                    print("TravelTime: "+str(newRouteStage.travelTime)+" , cost: "+str(newRouteStage.cost)+" , length: "+str(newRouteStage.length))
                                    if(newRouteStage.cost <= 5):
                                        try:
                                            traci.vehicle.setRoute(vecID,newRouteStage.edges)
                                            stop = True
                                        except traci.TraCIException:
                                            pass
                                    else:
                                        randomEdgeID = random.choice(listEdgesDistrict)
                                else:
                                    randomEdgeID = random.choice(listEdgesDistrict)
                else:
                    print("     Il veicolo è già fermo")
            else:
                print("     Il veicolo non ha ancora raggiungo ancora la sua destinazione")
        print("[2]")
        step = step + 1                                
        traci.time.sleep(0.3)


traci.start(sumoCmd)
run()
print("-----MAP"+str(parkingVec_Dictionary))
traci.close()
sys.stdout.flush()
"""
