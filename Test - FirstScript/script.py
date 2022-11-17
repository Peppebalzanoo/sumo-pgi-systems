#!/usr/bin/python
import os, sys, traci

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


#sumoCmd = ["sumo", "-c", "main.sumocfg"]
#sumoCmd = ["sumo-gui", "-c", "main.sumocfg", "--start"]
sumoCmd = ["C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe", "-c", "main.sumocfg", "--start"]

traci.start(sumoCmd)

step = 0
while (traci.simulation.getMinExpectedNumber() != 0):
    traci.simulationStep()

    countID = traci.vehicle.getIDCount()
    sys.stdout.write("#NUM_Vehicle: "+str(countID)+" #NUM_Step: "+str(step))

    listiID = traci.vehicle.getIDList()
    sys.stdout.write("\nCurrents Types: \n")

    for i in range(0, len(listiID)):
        var = listiID[i]
        sys.stdout.write("  -"+traci.vehicle.getTypeID(var)+"\n")

    print("\n")

    #print(f'current step: {step}')
    step+=1

traci.close()
