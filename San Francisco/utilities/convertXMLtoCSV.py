# Importing the required libraries
import csv
import xml.etree.ElementTree as ElementTree
import pandas
from matplotlib import pyplot

palette = ["#364F6B", "#3FC1C9", "#F5F5F5", "#FC5185"]

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
    tree = ElementTree.parse('../output/stops.xml')
    root = tree.getroot()
    for vecID in list_vec_xml:
        for elem in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            vehicleID = elem.attrib["id"]
            parkingID = elem.attrib["parkingArea"]
            rows.append({"vehicleID": vehicleID, "parkingAreaID": parkingID})
    df = pandas.DataFrame(rows, columns=cols)
    df.to_csv("../output/stop_info.csv", index=False)


def read_csv_stopinfo():
    with open("../output/stop_info.csv", "r") as csv_file:
        next(csv_file)  # Skippo la prima linea
        csv_reader = csv.reader(csv_file, delimiter=",")

        counter_parked = 0
        counter_not_parked = 0
        for temp_list in csv_reader:
            counter_parked += 1

        number_vec = len(get_vehicle_from_xml())
        counter_not_parked = number_vec - counter_parked
        print("Veicoli totali:", number_vec)
        # val : number_vec = X : 100 ---> (val * 100)/number_vec
        print("Si sono parcheggiati:", counter_parked, (counter_parked * 100) / number_vec)
        print("Non si sono parcheggiati:", counter_not_parked, (counter_not_parked * 100) / number_vec)

        pyplot.figure(figsize=(4, 5), dpi=120)
        data = [counter_parked, counter_not_parked]
        labels = ["Trovato", "Non Trovato"]
        pyplot.xticks(range(len(data)), labels)
        pyplot.ylabel('Conteggio')
        pyplot.grid(color='#95a5a6', linestyle='--', linewidth=1.5, axis='y', alpha=0.7)
        pyplot.bar(range(len(data)), height=data, width=0.5, color=palette[1])
        pyplot.savefig('../output/stop_info_bar_count.png')

        pyplot.figure(figsize=(4, 5), dpi=120)
        data = [((counter_parked * 100) / number_vec), ((counter_not_parked * 100) / number_vec)]
        labels = ["Trovato %", "Non Trovato %"]
        pyplot.xticks(range(0, len(data)), labels)
        pyplot.ylabel('Percentuale')
        pyplot.grid(color='#95a5a6', linestyle='--', linewidth=1.5, axis='y', alpha=0.7)
        pyplot.bar(range(0, len(data)), height=data, width=0.5, color=palette[1])
        pyplot.savefig('../output/stop_info_bar_percentage.png')


        pyplot.figure(figsize=(10, 7), dpi=120)
        data = [((counter_parked * 100) / number_vec),((counter_not_parked * 100) / number_vec)]
        labels = ["Trovato %", "Non Trovato %"]
        pyplot.pie(data, labels=labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=palette)
        pyplot.legend()
        # pyplot.axis("equal")
        pyplot.savefig('../output/stop_info_circle_percentage_noexplode.png')

        pyplot.figure(figsize=(10, 7), dpi=120)
        data = [((counter_parked * 100) / number_vec),((counter_not_parked * 100) / number_vec)]
        labels = ["Trovato %", "Non Trovato %"]
        myexplode = [0.2, 0]
        pyplot.pie(data, labels=labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=palette, explode=myexplode)
        pyplot.legend()
        # pyplot.axis("equal")
        pyplot.savefig('../output/stop_info_circle_percentage_noshadow.png')

        pyplot.figure(figsize=(10, 7), dpi=120)
        data = [((counter_parked * 100) / number_vec),((counter_not_parked * 100) / number_vec)]
        labels = ["Trovato %", "Non Trovato %"]
        myexplode = [0.2, 0]
        pyplot.pie(data, labels=labels, autopct='%1.1f%%', startangle=0, shadow=True, colors=palette, explode=myexplode)
        pyplot.legend()
        # pyplot.axis("equal")
        pyplot.savefig('../output/stop_info_circle_percentage_shadow.png')


def main():
    list_vec = get_vehicle_from_xml()
    create_csv_stopinfo(list_vec)
    read_csv_stopinfo()


if __name__ == "__main__":
    main()
