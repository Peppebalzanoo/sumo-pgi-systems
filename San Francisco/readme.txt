@ISTRUZIONI:

#0: LO SCRIPT EFFETTEURA' UN CONTROLLO SULLA VARIABILE D'AMBIENTE "SUMO_HOME"
    - PER SETTARLA: "https://sumo.dlr.de/docs/Basics/Basic_Computer_Skills.html"
    - SE NON TI INTERESSA SETTARLA:
        1. @COMMENTARE la riga 385 del file strategiaX.py
                "sumoBinary = checkBinary('sumo')"
        2. @SCOMMENTARE la riga 386 del file strategiaX.py
                "sumoBinary = ('sumo')"

#1: PER AVVIARE SENZA GUI USARE IL COMANDO "python strategiaX.py"

#2: PER AVVIARE CON GUI
        @SOSTITUIRE la riga 385 del file strategiaX.py
            "sumoBinary = checkBinary('sumo')" >>> "sumoBinary = checkBinary('sumo-gui')"

##########################################################################################
@COMANDI UTILI:
sumo -c san_francisco.sumocfg --vehroute-output yourRoutes.rou.xml
"./utilities/clearTripFile.py" -trp "trip.trips.xml" -o "clear.trips.xml"
"./utilities/generateVehicleFromTrips.py" -net "san_francisco.net.xml" -trp "clear.trips.xml" -vtp passenger -o "san_francisco.rou.xml"
