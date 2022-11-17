#!/usr/bin/python
import os, sys, traci

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

sumoCmd = ["C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe", "-c", "main.sumocfg", "--start"]

traci.start(sumoCmd)

step = 0
while (traci.simulation.getMinExpectedNumber() != 0):
    traci.simulationStep()
    countID = traci.vehicle.getIDCount()
    sys.stdout.write("#NUM_Vehicle: "+str(countID)+" #NUM_Step: "+str(step)+"\n")
    
    parkingListID = traci.parkingarea.getIDList()
    objListID = traci.vehicle.getIDList()
    
    for i in range(0, len(objListID)):
        currentType = traci.vehicle.getTypeID(objListID[i])
        if(currentType == "passenger"):
            vehicleID = objListID[i]
            if(int(vehicleID) %2 == 0):
             traci.vehicle.highlight(vehicleID,(255,0,0))
            else:
                traci.vehicle.highlight(vehicleID,(0,255,0))

    sys.stdout.write("\n")
    step+=1


traci.close()
