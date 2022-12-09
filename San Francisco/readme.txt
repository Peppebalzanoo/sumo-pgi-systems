@ISTRUZIONI

#1: PER AVVIARE la simulazione usare il comando "python dynamicarea.py"

#2: UNA VOLTA AVVIATO, lo script verrà fatto un controllo sulla variabile d'ambiente SUMO_HOME
    - SE VUOI SETTARLA, seguire la procedura al link:
        "https://sumo.dlr.de/docs/Basics/Basic_Computer_Skills.html"

    - SE NON VUOI SETTARLA:
        @ COMMENTARE la riga #385 del file dynamicarea.py
            "sumoBinary = checkBinary('sumo')"
        @ SCOMMENTARE la riga #386 del file dynamicarea.py
            "sumoBinary = ('sumo')"

#3: PER AVVIARE la simulazione con GUI
        @ SOSTITUIRE la riga #385 del file dynamicarea.py
            "sumoBinary = checkBinary('sumo')" con "sumoBinary = checkBinary('sumo-gui')"

##########################################################################################

@COMANDI UTILI:

"./utilities/clearTripFile.py" -trp "trip.trips.xml" -o "clear.trips.xml"

"./utilities/generateVehicleFromTrips.py" -net "san_francisco.net.xml" -trp "clear.trips.xml" -vtp passenger -o "san_francisco.rou.xml"
