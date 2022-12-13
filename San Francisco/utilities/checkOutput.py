import xml.etree.ElementTree as ET

def get_vehicle_from_xml():
    tree = ET.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml

def check_stops(vecID):
    tree = ET.parse('../output/strategia2/100%/stops.xml')
    root = tree.getroot()
    count = 0
    for stop in root.findall(".//stopinfo/[@id='"+vecID+"'"):
        count += 1
    if count != 1:
        file = open("file.txt", "a")
        print("VecID:", vecID, "ha effettuato più di una fermata (" + str(count) + ")", file=file)
        file.close()


def check_route(vecID):
    tree = ET.parse('../output/strategia2/100%/vehroute.xml')
    root = tree.getroot()
    count = 0
    last_edge = ""
    for route in root.findall(".//vehicle/[@id='"+vecID+"']//routeDistribution//route"):
        temp_list = list(route.attrib["edges"].split(" "))
        if count == 0:
            last_edge = temp_list[len(temp_list)-1]
            count += 1
        else:
            if last_edge not in temp_list:
                file = open("file.txt", "a")
                print("VecID:", vecID, "non un percorso inconsistente", file=file)
                file.close()
                break

def create_file(filaname):
    file = open(filaname, "w")
    file.close()

def main():
    create_file("file.txt")
    for vecID in get_vehicle_from_xml():
        check_route(vecID)
        # check_stops(vecID)

if __name__ == "__main__":
    main()
