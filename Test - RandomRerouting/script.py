#!/usr/bin/python
import random
import os, sys, traci
from sumolib import checkBinary

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

sumoBinary = checkBinary('sumo-gui')
sumoCmd = [sumoBinary, "-c", "main.sumocfg", "--start"]


"""
vehicle_Dict conterrà una coppia (vecID, vecRouteIndex) dove index è l'indice dell'edge in cui il veicolo si trova per quel route (sequenza di edges) in quell'ultimo tep
Ricordando che gli index partono da 0
"""
#(vecID, routeIndex)
vehicle_Dict = {}

#(laneID, parkingID)
lane_Dict = {}

#(vecID, parkingID)
parkingVec_Dict = {}

def loadLane_Dict():
    parkingListIDs = traci.parkingarea.getIDList()
    for parkingID in parkingListIDs:
        currLaneID = traci.parkingarea.getLaneID(parkingID)
        lane_Dict[currLaneID] = parkingID

#Questa funzione si occupa di inizializzare il dizionario vehicle_Dict aggiungendo una coppia (key = i, val = 0)
def loadVehicle_Dict():
    NUMBER = 2000 #E' il numero di veicoli totali della simulazione (che conosco già)
    for i in range(0,NUMBER):
        vehicle_Dict[str(i)] = 0


#Version 4.0
def run():
    step = 0.0
    loadLane_Dict() 
    loadVehicle_Dict()

    while (traci.simulation.getMinExpectedNumber() != 0 ):
        traci.simulationStep(0)
        sys.stdout.write("\n#STEP: "+str(step)+"\n")
        currVehiclesList = traci.vehicle.getIDList()

        for vecID in currVehiclesList:
            print(" - VEC_ID: "+vecID)
            currVecType = traci.vehicle.getTypeID(vecID)
            currVecRouteIndex = traci.vehicle.getRouteIndex(vecID)
            currRouteList = traci.vehicle.getRoute(vecID)
            dictRouteIndex = vehicle_Dict[vecID]


            if(currVecRouteIndex != dictRouteIndex):
                #Aggiorno nel dizionario il valore associato alla coppia (vecID, indexRoute) in quanto il veicolo si è spostato su un nuovo nodo(strada) del percorsp
                vehicle_Dict[vecID] = currVecRouteIndex

            if(currVecRouteIndex + 1 == len(currRouteList)):
                currLaneID = traci.vehicle.getLaneID(vecID)
                print("     E' arrivato a destinazione")

                if(traci.vehicle.isStoppedParking(vecID) == False): # type: ignore
                    currEdgeID = traci.lane.getEdgeID(currLaneID)
                    randomNumberEdge = random.randint(32,41)

                    parkingID = lane_Dict.get(currLaneID, False)
                    if(parkingID != False):
                        parkingCapacity = traci.simulation.getParameter(parkingID, "parkingArea.capacity")
                        parkingOccupancy = traci.simulation.getParameter(parkingID, "parkingArea.occupancy")
                        print("     Controlla parkingID: "+str(parkingID)+" , Capacità: "+parkingCapacity+" , Occupazione: "+parkingOccupancy)

                        if(parkingOccupancy < parkingCapacity and (vecID,parkingID) not in parkingVec_Dict.items()):
                                
                                try:
                                    traci.vehicle.setParkingAreaStop(vecID, parkingID, 10)  # type: ignore
                                    parkingVec_Dict[vecID] = parkingID
                                    print("     Ha settato il parkingID: "+str(parkingID))
                                except traci.TraCIException:
                        
                                    newRouteStage = traci.simulation.findRoute(currEdgeID,"E"+str(randomNumberEdge))

                                    while(len(newRouteStage.edges)==0):
                                        print("     Calcolo un nuovo percorso...")
                                        randomNumberEdge = random.randint(32,41)
                                        print("E"+str(randomNumberEdge)+" , "+str(currEdgeID))
                                        if("E"+str(randomNumberEdge) != str(currEdgeID)):
                                            newRouteStage = traci.simulation.findRoute(currEdgeID,"E"+str(randomNumberEdge))
                                        else:
                                            print("1111111111111111111111111111111111111")
                                            traci.vehicle.changeTarget(vecID,currEdgeID)
                                            break

                                    print("     Nuovo percorso calcolato: [ "+str(newRouteStage.edges)+" ] per arrivare a "+"E"+str(randomNumberEdge))
                                    try:
                                        traci.vehicle.setRoute(vecID,newRouteStage.edges)
                                    except traci.TraCIException:
                                        pass
                                   
                        else:
                           
                            print("     currEdgeId:"+str(currEdgeID))
                            newRouteStage = traci.simulation.findRoute(currEdgeID,"E"+str(randomNumberEdge))

                            while(len(newRouteStage.edges)==0):
                                    print("     Calcolo un nuovo percorso...")
                                    randomNumberEdge = random.randint(32,41)
                                    print("E"+str(randomNumberEdge)+" , "+str(currEdgeID))
                                    if("E"+str(randomNumberEdge) != str(currEdgeID)):
                                        newRouteStage = traci.simulation.findRoute(currEdgeID,"E"+str(randomNumberEdge))
                                    else:
                                        print("22222222222222222222222222222222222222")
                                        traci.vehicle.changeTarget(vecID,currEdgeID)
                                        break

                            print("     Nuovo percorso calcolato: [ "+str(newRouteStage.edges)+" ] per arrivare a "+"E"+str(randomNumberEdge))
                            try:
                                traci.vehicle.setRoute(vecID,newRouteStage.edges)
                            except traci.TraCIException:
                                pass
                            
                    else:
                        
                        newRouteStage = traci.simulation.findRoute(currEdgeID,"E"+str(randomNumberEdge))
                    
                        while(len(newRouteStage.edges)==0):
                            print("     Calcolo un nuovo percorso...")
                            randomNumberEdge = random.randint(32,41)
                            print("E"+str(randomNumberEdge)+" , "+str(currEdgeID))
                            if("E"+str(randomNumberEdge) != str(currEdgeID)):
                                newRouteStage = traci.simulation.findRoute(currEdgeID,"E"+str(randomNumberEdge))
                            else:
                                print("333333333333333333333333333333333333")
                                print("currEdgeID: "+str(currEdgeID))
                                traci.vehicle.changeTarget(vecID,currEdgeID)
                                break

                        print("     Nuovo percorso calcolato: [ "+str(newRouteStage.edges)+" ] per arrivare a "+"E"+str(randomNumberEdge))
                        try:
                            traci.vehicle.setRoute(vecID,newRouteStage.edges)
                        except traci.TraCIException:
                            pass
                else:
                    print("     E' già parcheggiato in attesa che scada il suo quanto di tempo")

        #traci.time.sleep(0.5)
        step+=0.1



traci.start(sumoCmd)
run()
traci.close()









"""currSpeed = traci.vehicle.getSpeed(vecID)
                            currAccel = traci.vehicle.getAcceleration(vecID)
                            currDecel = traci.vehicle.getDecel(vecID)

                            #Spazio attuale che occorre al veicolo per frenare in sicurezza
                            spaceCurrToBrake = ((currSpeed*currSpeed)/((2*9.8)*0.8))
                            print("Spazio corrente che serve per frenare: "+str(spaceCurrToBrake))
                            print(" con Speed: "+str(currSpeed)+" ed Acc: "+str(currAccel)+" ed MaxDecl: "+str(currDecel))

                            spaceAviableToBrake = traci.parkingarea.getStartPos(parkingID)
                            
                            print("Spazio disponibile per frenare: "+str(spaceAviableToBrake))

                            #if(spaceCurrToBrake > spaceAviableToBrake):
                                #print("     vecID: "+vecID+" deve fare una repentina per parcheggiarsi")

                                #La velocità che bisogna dare al veicolo per arrestarlo nel gap fornito
                                #val = traci.vehicle.getStopSpeed(vecID,currSpeed,spaceCurrToBrake)

                                #val2 = traci.vehicle.getStopSpeed(vecID,currSpeed,spaceAviableToBrake)
                                #print("Stop-speed: "+str(val))
                                #print("Stop-speed2: "+str(val2))

                                #traci.vehicle.setDecel(vecID,val2)
                                #traci.vehicle.setSpeed(vecID,val2)

                            #elif(traci.vehicle.getDecel(vecID) != maxDecel):
                             #   traci.vehicle.setDecel(vecID,maxDecel)"""


      
"""#Aggiungo al dizionario la coppia(vecID, parkinID)
                                parkingVec_Dict[vecID] = parkingID

print("     vecID: "+vecID+" ha settato il parcheggio")"""


"""
 #Sapendo che lo spazio di arresto = spazio di reazione + spazio di frenata
                            #supponiamo che lo spazio di reazione del conducente per frenare è instantaneo (cioè non lo terremo in considerazione)
                            #safeSpaceToBrake = ((currSpeed*currSpeed)/((2*9.8)*0.8))
                            #print("Spazio Frenata Sicura: "+str(safeSpaceToBrake))
                            #print(" con Speed: "+str(currSpeed)+" ed Acc: 9.8")"""

"""def loadLane_Dict():
    import re
    parkingListIDs = traci.parkingarea.getIDList()
    for parkingID in parkingListIDs:
        currLaneID = traci.parkingarea.getLaneID(parkingID)
        s1 = (str(currLaneID))
        s2 = re.search('^E[0-9]*', s1).group(0) # type: ignore
        lane_Dict[s2] = parkingID
    print("LaneDict: "+str(lane_Dict)) 
"""


#Version 3.0
"""step = 0.0
    loadLane_Dict() 
    loadVehicle_Dict()

    print(str(vehiclesSet))
    while (traci.simulation.getMinExpectedNumber() != 0 ):
        traci.simulationStep(0)
        sys.stdout.write("#STEP: "+str(step)+"\n")

        for vecID in vehicle_Dict.keys():
            currVehiclesList = traci.vehicle.getIDList()

            if(vecID in currVehiclesList):
                currVecRouteIndex = traci.vehicle.getRouteIndex(vecID)
                currRouteList = traci.vehicle.getRoute(vecID)
                dictRouteIndex = vehicle_Dict[vecID]
                traci.vehicle.highlight(vecID, (255,0,0))

                if(currVecRouteIndex != dictRouteIndex):
                    vehicle_Dict[vecID] = currVecRouteIndex
                    print(str(vehicle_Dict))
                    if(currVecRouteIndex + 1 == len(currRouteList)):
                        currLaneID = traci.vehicle.getLaneID(vecID)
                        parkingID = lane_Dict.get(currLaneID, False)
                        if(parkingID != False):
                            traci.vehicle.setParkingAreaStop(vecID, parkingID, 20)    # type: ignore
        traci.time.sleep(1)
        step+=0.1"""


""" parking_Dict = {}
    def loadParking_Dict():
    parkingListID = traci.parkingarea.getIDList()
    for parkingID in parkingListID:
        parking_Dict[parkingID] = traci.parkingarea.getLaneID(parkingID)
    print("parking_Dict: "+str(parking_Dict))"""

#Version 2.0
"""while (traci.simulation.getMinExpectedNumber() != 0 ):
        traci.simulationStep(0)
        sys.stdout.write("#STEP: "+str(step)+"\n")
        
        for vecID in vehicle_Dict.keys():

            currVehiclesList = traci.vehicle.getIDList()
            if(vecID in currVehiclesList):
                currVecRouteIndex = traci.vehicle.getRouteIndex(vecID)
                currRouteList = traci.vehicle.getRoute(vecID)
                dictRouteIndex = vehicle_Dict[vecID]
                traci.vehicle.highlight(vecID, (255,0,0))

                if(currVecRouteIndex != dictRouteIndex):
                    vehicle_Dict[vecID] = currVecRouteIndex

                    if(currVecRouteIndex + 1 == len(currRouteList)):
                        checkParking = False
                        currLaneID = traci.vehicle.getLaneID(vecID)
                        for laneID in parking_Dict.values():
                            if(laneID == currLaneID):
                                checkParking = True
                                break
                        if(checkParking == True):
                            for par,lan in parking_Dict.items():
                                if(lan == currLaneID):
                                    parking = par
                                    break
                            traci.vehicle.setParkingAreaStop(vecID, parking, 20)  # type: ignore
        traci.time.sleep(1)
        step+=0.1"""




#Version 1.0
"""while (traci.simulation.getMinExpectedNumber() != 0 ):
        traci.simulationStep(0)

        sys.stdout.write("#STEP: "+str(step)+"\n")
        vehicleListID = traci.vehicle.getIDList()
        for vecID in vehicleListID:

            #currVecRouteIndex = vehicle_Dict[vecID]

            currVecRouteIndex = traci.vehicle.getRouteIndex(vecID)
            currRouteList = traci.vehicle.getRoute(vecID)

            print("#vecID: "+vecID)
            print(" currRouteList"+str(currRouteList)+", len: "+str(len(currRouteList)))
            print(" current index: "+str(currVecRouteIndex))

            if(currVecRouteIndex + 1 == len(currRouteList)):
                print("Il veicolo vecID "+vecID+" sta percorrendo l'ultima strada per poi uscire dalla simulaizone")
                traci.vehicle.highlight(vecID, (255,0,0))
                checkParking = False
                currLaneID = traci.vehicle.getLaneID(vecID)
                for laneID in parking_Dict.values():
                    if(laneID == currLaneID):
                        checkParking = True
                        break
                if(checkParking == True):
                    for par,lan in parking_Dict.items():
                        if(lan == currLaneID):
                            parking = par
                            print(parking)
                            break
                    traci.vehicle.setParkingAreaStop(vecID, parking, 20)  # type: ignore
                    print("Ho settato la parkingArea per il veicoli vecID: "+vecID)
        traci.time.sleep(1)
        step+=0.1"""
