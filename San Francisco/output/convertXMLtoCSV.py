# Importing the required libraries
import csv
import xml.etree.ElementTree as ElementTree
import pandas
from matplotlib import pyplot


def get_vehicle_from_xml():
    tree = ElementTree.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml

def create_csv_stopinfo(list_vec_xml):
    cols = ["vehicleID", "parkingAreaID"]
    rows = []

    # Parsing the XML file
    tree = ElementTree.parse('stops.xml')
    root = tree.getroot()
    for vecID in list_vec_xml:
        for elem in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            vehicleID = elem.attrib["id"]
            parkingID = elem.attrib["parkingArea"]
            rows.append({"vehicleID": vehicleID, "parkingAreaID": parkingID})

        df = pandas.DataFrame(rows, columns=cols)
        df.to_csv("stop_info.csv", index=False)

def read_csv_stopinfo():
    with open("stop_info.csv", "r") as csv_file:
        next(csv_file)  # Skippo la prima linea
        csv_reader = csv.reader(csv_file, delimiter=",")

        # vecID, counter
        dizionario = {}
        for temp_list in csv_reader:
            if temp_list[0] not in dizionario:
                dizionario[temp_list[0]] = 1
            else:
                temp_count = dizionario.get(temp_list[0])
                dizionario[temp_list[0]] = temp_count + 1


        pyplot.figure(1, figsize=(20, 8), dpi=120)
        pyplot.title("Example Data")
        pyplot.xlabel("Veicolo ID")
        pyplot.ylabel("Conteggio")
        pyplot.plot(dizionario.keys(), dizionario.values(), label="A")
        # pyplot.show()
        pyplot.savefig('stop_info.png')


        # pyplot.figure(2, figsize=(20, 8), dpi=120)
        # pyplot.title("Example Data")
        # pyplot.xlabel("Veicolo ID")
        # pyplot.ylabel("Conteggio")
        # pyplot.bar(dizionario.keys(), dizionario.values())
        # pyplot.show()
        #
        # pyplot.figure(2, figsize=(20, 8), dpi=120)
        # pyplot.title("Example Data")
        # pyplot.xlabel("Veicolo ID")
        # pyplot.ylabel("Conteggio")
        # pyplot.scatter(dizionario.keys(), dizionario.values())
        # pyplot.show()






def main():
    list_vec = get_vehicle_from_xml()
    create_csv_stopinfo(list_vec)
    read_csv_stopinfo()

if __name__ == "__main__":
    main()
