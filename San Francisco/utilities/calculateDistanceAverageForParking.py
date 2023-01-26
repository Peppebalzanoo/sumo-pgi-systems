import re
import xml.etree.ElementTree as ElementTree
from matplotlib import pyplot
colors_palette = ["#364F6B", "#3FC1C9", "#C9D6DF", "#FC5185", "#52616B"]

def get_vehicle_from_xml():
    tree = ElementTree.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


def get_not_parking_vehicle(strategia, scenario):
    tree = ElementTree.parse("../output/"+strategia+"/"+scenario+"/stops.xml")
    root = tree.getroot()
    list_parked = []
    for vecID in get_vehicle_from_xml():
        for stop in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            list_parked.append(vecID)
    not_parked = set(get_vehicle_from_xml()).difference(set(list_parked))
    return not_parked


def get_edge_form_parkinglane(parking_laneID):
    return re.sub("_.*", "", parking_laneID)

# * ********************************************************************************************************************************************************************* * #

park_to_startpos_dict = {}

def calculate_startpos_parking_dict():
    tree = ElementTree.parse('../parking_capacity_100%/on_parking_100%.add.xml')
    root = tree.getroot()
    for park in root.findall(".//parkingArea"):
        parkID = park.attrib["id"]
        startpos = park.attrib["startPos"]
        park_to_startpos_dict[parkID] = startpos

    tree = ElementTree.parse('../parking_capacity_100%/off_parking_100%.add.xml')
    root = tree.getroot()
    for park in root.findall(".//parkingArea"):
        parkID = park.attrib["id"]
        startpos = park.attrib["startPos"]
        park_to_startpos_dict[parkID] = startpos

# * ********************************************************************************************************************************************************************* * #

# edge to lenght
edge_to_length_dict = {}

def calculate_edge_to_length_dict():
    tree = ElementTree.parse('../san_francisco.net.xml')
    root = tree.getroot()
    for edg in root.findall(".//edge"):
        edgeID = edg.attrib["id"]
        for lane in root.findall(".//edge/[@id='" + edgeID + "']/lane"):
            edge_to_length_dict[edgeID] = lane.attrib["length"]
            break

# * ********************************************************************************************************************************************************************* * #

# vecID: (parkID, laneID)
vecparked_to_parkingID_dict = {}

def calculate_vecparked_dict(strategia, scenario, list_vec_xml):
    tree = ElementTree.parse("../output/"+strategia+"/"+scenario+"/stops.xml")
    root = tree.getroot()
    for vecID in list_vec_xml:
        for elem in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            laneID_parking = elem.attrib["lane"]
            curr_parkingID = elem.attrib["parkingArea"]
            vecparked_to_parkingID_dict[vecID] = curr_parkingID, laneID_parking

# * ********************************************************************************************************************************************************************* * #

# vecID: destID
vec_to_dest_dict = {}

def calculate_vec_destination(list_vec_xml):
    for vecID in list_vec_xml:
        tree = ElementTree.parse('../san_francisco.rou.xml')
        root = tree.getroot()
        for elem in root.findall(".//vehicle/[@id='" + vecID + "']/route"):
            temp = elem.get("edges")
            if temp is not None:
                list_edges = temp.split()
                vec_to_dest_dict[vecID] = list_edges[len(list_edges) - 1]

# * ********************************************************************************************************************************************************************* * #


# vecID: lista_nodi_percorso
vec_to_listedges_dict = {}

def calculate_vec_route(strategia, scenario, list_vec_xml):

    tree = ElementTree.parse("../output/" + strategia + "/" + scenario + "/vehroute.xml")
    root = tree.getroot()
    for vecID in list_vec_xml:
        # I veicoli che non hanno mai calcolato un nuovo percorso
        for route in root.findall(".//vehicle/[@id='" + vecID + "']/route"):
            vec_to_listedges_dict[vecID] = list(route.attrib["edges"].split())

        # I veicoli che hanno almeno una volta calcolato un nuovo percorso
        for route in root.findall(".//vehicle/[@id='" + vecID + "']/routeDistribution/route"):
            if "replacedOnEdge" not in route.attrib:
                vec_to_listedges_dict[vecID] = list(route.attrib["edges"].split())

# * ********************************************************************************************************************************************************************* * #

def calculate(strategia, scenario, list_vec_xml):
    totale = 0.0
    list_vec_parked = list(vecparked_to_parkingID_dict.keys())
    for vecID in list_vec_parked:
        dest_edgeID = vec_to_dest_dict.get(vecID)
        vec_route_list = list(vec_to_listedges_dict.get(vecID))
        start = False
        for idx in range(0, len(vec_route_list)):
            curr_edgeID = vec_route_list[idx]
            parkingID = vecparked_to_parkingID_dict.get(vecID)[0]
            laneID_park = vecparked_to_parkingID_dict.get(vecID)[1]
            edgeID_park = get_edge_form_parkinglane(laneID_park)

            # Se sto sommando
            if start is True:
                # Se sono arrivato al nodo del parcheggio sommo solo la distanza al parcheggio (non sommo tutta la lunghezza della strada)
                if curr_edgeID == edgeID_park:
                    startpos = park_to_startpos_dict.get(parkingID)
                    totale += float(startpos)
                    break
                else:
                    totale += float(edge_to_length_dict.get(curr_edgeID))
            else:
                # Se non sto sommano e mi rendo conto che sono arrivato a destinazione
                if curr_edgeID == dest_edgeID and start is False:
                    start = True
                    # Se ho parcheggiato a destinazione sommo solo la distanza al parcheggio (non sommo tutta la lunghezza della strada)
                    if curr_edgeID == edgeID_park:
                        startpos = park_to_startpos_dict.get(parkingID)
                        totale += float(startpos)
                        break
                    else:
                        totale += float(edge_to_length_dict.get(curr_edgeID))

    not_parked_list = get_not_parking_vehicle(strategia, scenario)
    for vecID in not_parked_list:
        dest_edgeID = vec_to_dest_dict.get(vecID)
        vec_route_list = list(vec_to_listedges_dict.get(vecID))
        start = False
        for idx in range(0, len(vec_route_list)):
            curr_edgeID = vec_route_list[idx]
            # Se sto sommando
            if start is True:
                totale += float(edge_to_length_dict.get(curr_edgeID))
            else:
                # Se non sto sommano e mi rendo conto che sono arrivato a destinazione
                if curr_edgeID == dest_edgeID and start is False:
                    start = True
                    totale += float(edge_to_length_dict.get(curr_edgeID))

    return totale




def generate_bar(data, data_labels, name_out, lista_strategie, scenario):
    pyplot.figure(figsize=(6, 7), dpi=120)
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.grid(color='#95a5a6', linestyle='--', linewidth=1.5, axis='y', alpha=0.7)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    for strategia in lista_strategie:
        pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_grid")
    pyplot.close()

def generate_pie(data, data_labels, name_out, lista_strategie, scenario):
    pyplot.figure(figsize=(10, 7), dpi=120)
    myexplode = []
    for i in range(0, len(data)):
        myexplode.append(0.1)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=colors_palette, explode=myexplode)
    pyplot.legend()
    pyplot.axis("equal")
    for strategia in lista_strategie:
        pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", ""))
    pyplot.close()

def main():
    list_vec_xml = get_vehicle_from_xml()
    calculate_edge_to_length_dict()
    calculate_startpos_parking_dict()
    calculate_vec_destination(list_vec_xml)

    print("-------------- 100% -------------- ")
    calculate_vec_route("strategia1", "100%", list_vec_xml)
    calculate_vecparked_dict("strategia1", "100%", list_vec_xml)
    t1 = calculate("strategia1", "100%", list_vec_xml)
    t1 = t1/len(list_vec_xml)
    print(t1)

    calculate_vec_route("strategia2", "100%", list_vec_xml)
    calculate_vecparked_dict("strategia2", "100%", list_vec_xml)
    t2 = calculate("strategia2", "100%", list_vec_xml)
    t2 = t2/len(list_vec_xml)
    print(t2)

    calculate_vec_route("strategia3", "100%", list_vec_xml)
    calculate_vecparked_dict("strategia3", "100%", list_vec_xml)
    t3 = calculate("strategia3", "100%", list_vec_xml)
    t3 = t3/len(list_vec_xml)
    print(t3)

    data = [t1, t2, t3]
    lables_data_bar = ["strategia1", "strategia2", "strategia3"]
    generate_bar(data, lables_data_bar, "distance", ["strategia1", "strategia2", "strategia3"], "100%")
    generate_pie(data, lables_data_bar, "distance", ["strategia1", "strategia2", "strategia3"], "100%")

    print("-------------- 75% -------------- ")
    calculate_vec_route("strategia1", "75%", list_vec_xml)
    calculate_vecparked_dict("strategia1", "75%", list_vec_xml)
    t4 = calculate("strategia1", "75%", list_vec_xml)
    t4 = t4/len(list_vec_xml)
    print(t4)

    calculate_vec_route("strategia2", "75%", list_vec_xml)
    calculate_vecparked_dict("strategia2", "75%", list_vec_xml)
    t5 = calculate("strategia2", "75%", list_vec_xml)
    t5 = t5/len(list_vec_xml)
    print(t5)


    calculate_vec_route("strategia3", "75%", list_vec_xml)
    calculate_vecparked_dict("strategia3", "75%", list_vec_xml)
    t6 = calculate("strategia3", "75%", list_vec_xml)
    t6 = t6/len(list_vec_xml)
    print(t6)


    data = [t4, t5, t6]
    generate_bar(data, lables_data_bar, "distance", ["strategia1", "strategia2", "strategia3"], "75%")
    generate_pie(data, lables_data_bar, "distance", ["strategia1", "strategia2", "strategia3"], "75%")

    print("--------------  50% -------------- ")
    calculate_vec_route("strategia1", "50%", list_vec_xml)
    calculate_vecparked_dict("strategia1", "50%", list_vec_xml)
    t7 = calculate("strategia1", "50%", list_vec_xml)
    t7 = t7/len(list_vec_xml)
    print(t7)


    calculate_vec_route("strategia2", "50%", list_vec_xml)
    calculate_vecparked_dict("strategia2", "50%", list_vec_xml)
    t8 = calculate("strategia2", "50%", list_vec_xml)
    t8 = t8/len(list_vec_xml)
    print(t8)


    calculate_vec_route("strategia3", "50%", list_vec_xml)
    calculate_vecparked_dict("strategia3", "50%", list_vec_xml)
    t9 = calculate("strategia3", "50%", list_vec_xml)
    t9 = t9/len(list_vec_xml)
    print(t9)


    data = [t7, t8, t9]
    generate_bar(data, lables_data_bar, "distance", ["strategia1", "strategia2", "strategia3"], "50%")
    generate_pie(data, lables_data_bar, "distance", ["strategia1", "strategia2", "strategia3"], "50%")

# * ********************************************************************************************************************************************************************* * #


if __name__ == "__main__":
    main()
