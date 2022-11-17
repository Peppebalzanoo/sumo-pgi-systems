#!/usr/bin/python
import os
import sys

import traci
from sumolib import checkBinary


def get_distance_tolast(curr_edgeID, last_edgeID, curr_position):
    if curr_edgeID == last_edgeID:
        distance_tolast_edge = 0.0
    else:
        distance_tolast_edge = traci.simulation.getDistanceRoad(curr_edgeID, curr_position, last_edgeID, 0.0, True)

    return distance_tolast_edge


def check_exit_vec(step):
    count = traci.vehicle.getIDCount()
    print("\n ###################### STEP: " + str(step) + " COUNT: " + str(count) + " ######################")
    if step != 0:
        # Controllo se qualche veicolo ha lasciato la simulazione
        if (len(traci.simulation.getArrivedIDList())) > 0:
            print(traci.simulation.getArrivedIDList())
            traci.time.sleep(5)


def run():
    step = 0
    file = open("gap_length_0.txt", "w")
    print("################ length ################", file=file)

    while traci.simulation.getMinExpectedNumber() != 0:

        traci.simulation.step()
        step = step + 1



        check_exit_vec(step)
        currVehiclesList = traci.vehicle.getIDList()

        for vecID in currVehiclesList:
            print("\n # VEC_ID: [" + vecID + "]")
            print("    # (currSpeed, currAcc):", str(traci.vehicle.getSpeed(vecID)), str(traci.vehicle.getAcceleration(vecID)))

            departed_vec = traci.simulation.getDepartedIDList()
            if vecID not in departed_vec:


                currRouteList = traci.vehicle.getRoute(vecID)
                currLastEdgeID = currRouteList[len(currRouteList) - 1]

                currLaneID = traci.vehicle.getLaneID(vecID)
                currPosition = traci.vehicle.getLanePosition(vecID)
                currSpeed = traci.vehicle.getSpeed(vecID)
                currAcc = traci.vehicle.getAcceleration(vecID)
                currEdgeID = traci.lane.getEdgeID(currLaneID)
                currLaneIndex = traci.vehicle.getLaneIndex(vecID)


                leaderSpeed = traci.vehicle.getAllowedSpeed(vecID)
                # minGap = 2.5
                # minGap = 1.0
                # minGap = 0.1
                # minGap = 5.0
                minGap = traci.lane.getLength(currLaneID)
                nextSpeed = traci.vehicle.getFollowSpeed(vecID, currSpeed, minGap, leaderSpeed, 4.5)




                distanceToLastEdge = get_distance_tolast(currEdgeID, currLastEdgeID, currPosition)

                # space_for_second è una stima che suppone che l'accelerazione resti costante tra lo step corrente e il prossimo
                # space_for_second = (1 / 2 * abs(currAcc) * 1) + (currSpeed * 1)
                space_for_second = (1 / 2 * currAcc * 1) + (currSpeed * 1)

                print("currEdge:", currEdgeID, " , currLane:", currLaneID, ", lastEdge:", currLastEdgeID, "Distance To Last:", distanceToLastEdge)
                print("currAcc:", currAcc, "currSpeed:", currSpeed)
                print("space_for_second:", space_for_second)


                print("currSpeed:", currSpeed, file=file)
                print("spaceForSecond:", space_for_second, file=file)
                print("nextSpeed:", nextSpeed, file=file)
                print("\n", file=file)



                # ___ CRITICAL ROUTINE ___ #
                if space_for_second >= distanceToLastEdge and currEdgeID != currLastEdgeID:
                    print("     CRITICAL = E' arrivato a destinazione!")

                # ___ NORMAL ROUTINE ___ #
                elif space_for_second >= distanceToLastEdge and currEdgeID == currLastEdgeID:
                    print("     NORMAL = E' arrivato a destinazione!")

                # ___ TRIP ROUTINE ___ #
                else:
                    print("     Sto viaggindo...")
    file.close()

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


if __name__ == "__main__":
    main()
