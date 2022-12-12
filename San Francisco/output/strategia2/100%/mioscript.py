import xml.etree.ElementTree as ET

def get_vehicle_from_xml():
    tree = ET.parse('../../../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


def check(vecID):
    tree = ET.parse('vehroute.xml')
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
                print("VecID:", vecID, file=file)
                break

def main():
    file = open("file.txt", "w")
    file.close()
    for vecID in get_vehicle_from_xml():
        check(vecID)

if __name__ == "__main__":
    main()
