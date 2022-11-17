#!/usr/bin/python
import os
import random
import sys
import xml.etree.ElementTree as ET

import traci
from sumolib import checkBinary

# E' il numero di veicoli totali della simulazione (che conosco già)
NUMBER = 150

# (vecID, routeIndex)
vehicle_Dictionary = {}

# (currLaneID, parkingID)
lane_Dictionary = {}

# (vecID, parked)
parkingVec_Dictionary = {}

# (edgeID, districtID)
edgeDistrict_Dictionary = {}

# (districtID, listEdgesDistrict)
districtListEdgesDictionary = {}

def check_exit_vec(step):
    if step == 0:
        traci.time.sleep(2)
    else:
        count = traci.vehicle.getIDCount()
        print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")
        # Controllo se qualche veicolo ha lasciato la simulazione
        if (len(traci.simulation.getArrivedIDList())) > 0:
            print(traci.simulation.getArrivedIDList())
            traci.time.sleep(5)



# Questa funzione si occupa di inizializzare il dizionario vehicle_Dictionary
# aggiungendo una coppia (key = i, space = 0)
def loadVehicleDictionary():
    for i in range(0, NUMBER):
        vehicle_Dictionary[str(i)] = 0


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


def getListDistrictID():
    listDistrictID = []
    tree = ET.parse('districts.taz.xml')
    root = tree.getroot()
    for dis in root.findall('taz'):
        districtID = dis.get('id')
        listDistrictID.append(districtID)
    return listDistrictID


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
    step = 0
    loadLaneDictionary()
    loadVehicleDictionary()
    loadParkingVecDictionary()
    loadEdgeDistrictDictionary()
    loadDistrictListEdgesDictionary()
    # listDistrictID = getListDistrictID()

    while traci.simulation.getMinExpectedNumber() != 0:
        traci.simulationStep()

        check_exit_vec(step)

        currVehiclesList = traci.vehicle.getIDList()


        for vecID in currVehiclesList:
            print(" - VEC_ID: " + vecID)
            currVecRouteIndex = traci.vehicle.getRouteIndex(vecID)
            currRouteList = traci.vehicle.getRoute(vecID)
            DictionaryRouteIndex = vehicle_Dictionary[vecID]
            lastEdgeID = currRouteList[len(currRouteList) - 1]

            print("     currIndex: " + str(currVecRouteIndex))
            print("     len: " + str(len(currRouteList)))
            # Controllo se dalla strada in cui sono partito, sono passato ad un'altra starda
            if currVecRouteIndex != DictionaryRouteIndex:
                # Aggiorno nel dizionario il valore associato alla coppia (vecID, indexRoute) in quanto il veicolo si è spostato su un nuovo nodo(strada) del percorsp
                vehicle_Dictionary[vecID] = currVecRouteIndex
                print("     currRouteList: " + str(currRouteList))

            # Controllo se sono arrivato alla strada di destinazione
            if currVecRouteIndex + 1 == len(currRouteList):
                print("     Il veicolo è arrivato a destinazione")
            else:
                print("     Il veicolo non ha ancora raggiungo ancora la sua destinazione")
        step = step + 1
        #traci.time.sleep(0.3)


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
