#!/usr/bin/python
import os, sys, traci
from sumolib import checkBinary

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

sumoBinary = checkBinary('sumo-gui')
sumoCmd = [sumoBinary, "-c", "main.sumocfg", "--start"]
#sumoCmd = ["C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe", "-c", "main.sumocfg", "--start"]



def run():
    step = 0
    while (traci.simulation.getMinExpectedNumber() > 0):
        traci.simulationStep()
        sys.stdout.write("#NUM_Step: "+str(step)+"\n")
        
        """if step == 100:
            vehicleList = traci.vehicle.getIDList()
            traci.vehicle.changeTarget(vehicleList[1], "E9")
            traci.vehicle.changeTarget(vehicleList[3], "E9")"""

        #Interrogo il detector presente sulla lane E4_0
        #Recuperando gli IDs dei veicoli nell'ultimo step che hanno attraverato tale lane
        #E spostando questi veicoli recuperati sulla corsia 2 per 100 steps 
        if step==100:
            vehList = traci.inductionloop.getLastStepVehicleIDs("det0")
            for vehID in vehList:
                traci.vehicle.changeLane(vehID, 2, 100)
                traci.vehicle.setColor(vehID,(255,0,0))

        step+=1
    traci.close()



traci.start(sumoCmd)
run()



