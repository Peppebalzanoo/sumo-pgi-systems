import pandas
import xml.etree.ElementTree as ElementTree


def get_vehicle_from_xml():
    tree = ElementTree.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


def create_csv_stopinfo(list_vec_xml, strategia, scenario):
    cols = ["vecID", "parkingID", "duration"]
    rows = []
    tree = ElementTree.parse("../output/"+strategia+"/"+scenario+"/stops.xml")
    root = tree.getroot()
    for vecID in list_vec_xml:
        for elem in root.findall(".//stopinfo/[@id='" + vecID + "']"):
            vehicleID = elem.attrib["id"]
            parkingID = elem.attrib["parkingArea"]
            start = float(elem.attrib["started"])
            end = float(elem.attrib["ended"])
            rows.append({"vecID": vehicleID, "parkingID": parkingID, "duration": (end - start)})
    df = pandas.DataFrame(rows, columns=cols)
    df.to_csv("../output/"+strategia+"/"+scenario+"/csv/stopinfo.csv", index=False)


def create_csv_statistics(strategia, scenario):
    cols = ["routeLengthAVG", "speedAVG", "durationAVG"]
    rows = []
    tree = ElementTree.parse("../output/"+strategia+"/"+scenario+"/statistic.xml")
    root = tree.getroot()
    avg_route_length = float(root.find("vehicleTripStatistics").attrib["routeLength"])
    avg_speed = float(root.find("vehicleTripStatistics").attrib["speed"])
    avg_duration = float(root.find("vehicleTripStatistics").attrib["duration"])
    rows.append({"routeLengthAVG": avg_route_length, "speedAVG": avg_speed, "durationAVG": avg_duration})
    df = pandas.DataFrame(rows, columns=cols)
    df.to_csv("../output/"+strategia+"/"+scenario+"/csv/statistics.csv", index=False)


def create_csv_emmissions(strategia, scenario):
    cols = ["CO", "CO2", "HC", "FUEL"]
    rows = []
    tree = ElementTree.parse("../output/"+strategia+"/"+scenario+"/tripinfo.xml")
    root = tree.getroot()
    for elem in root.findall(".//tripinfo/emissions"):
        temp_CO = float(elem.attrib["CO_abs"])
        temp_CO2 = float(elem.attrib["CO2_abs"])
        temp_HC = float(elem.attrib["HC_abs"])
        temp_FUEL = float(elem.attrib["fuel_abs"])
        rows.append({"CO": temp_CO, "CO2": temp_CO2, "HC": temp_HC, "FUEL": temp_FUEL})
    df = pandas.DataFrame(rows, columns=cols)
    df.to_csv("../output/"+strategia+"/"+scenario+"/csv/emissions.csv", index=False)


def main():
    list_vec = get_vehicle_from_xml()

    # STRATEGIA: dynamic_area, SCENARIO: 100%
    create_csv_stopinfo(list_vec, "dynamic_area", "100%")
    create_csv_statistics("dynamic_area", "100%")
    create_csv_emmissions("dynamic_area", "100%")


if __name__ == "__main__":
    main()
