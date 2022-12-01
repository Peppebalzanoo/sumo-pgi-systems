import csv
from matplotlib import pyplot
import xml.etree.ElementTree as ElementTree

colors_palette = ["#364F6B", "#3FC1C9", "#C9D6DF", "#FC5185", "#52616B"]


def get_vehicle_from_xml():
    tree = ElementTree.parse('../san_francisco.rou.xml')
    root = tree.getroot()
    list_vec_xml = []
    for elem in root.findall(".//vehicle"):
        vec_xml = elem.attrib['id']
        list_vec_xml.append(vec_xml)
    return list_vec_xml


def get_average_emmissions(list_vec_xml):
    tree = ElementTree.parse('../output/dynamic_area/100%/tripinfo.xml')
    root = tree.getroot()

    temp_emissions_CO = 0.0
    temp_emissions_CO2 = 0.0
    temp_emissions_HC = 0.0
    temp_emissions_PM = 0.0
    temp_emissions_NO = 0.0
    temp_fuel_consumed = 0.0
    for elem in root.findall(".//tripinfo/emissions"):
        temp_emissions_CO += float(elem.attrib["CO_abs"])
        temp_emissions_CO2 += float(elem.attrib["CO2_abs"])
        temp_emissions_HC += float(elem.attrib["HC_abs"])
        temp_emissions_PM += float(elem.attrib["PMx_abs"])
        temp_emissions_NO += float(elem.attrib["NOx_abs"])
        temp_fuel_consumed += float(elem.attrib["fuel_abs"])

    average_emissions_CO = temp_emissions_CO/len(list_vec_xml)
    average_emissions_CO2 = temp_emissions_CO2/len(list_vec_xml)
    average_emissions_HC = temp_emissions_HC/len(list_vec_xml)
    average_emissions_PM = temp_emissions_PM/len(list_vec_xml)
    average_emissions_NO = temp_emissions_NO/len(list_vec_xml)
    average_fuel_consumed = temp_fuel_consumed/len(list_vec_xml)

    data_emissions = [average_emissions_CO, average_emissions_CO2, average_fuel_consumed]
    labels_data_emissions = ["CO", "CO2", "Fuel"]

    generate_bar_yscale(data_emissions, labels_data_emissions, "emissions", "dynamic_area", "100%", None)
    generate_pie(data_emissions, labels_data_emissions, "emissions", "dynamic_area", "100%")


def read_csv_statistics(strategia, scenario):
    with open("../output/"+strategia+"/"+scenario+"/csv/statistics.csv", "r") as csv_file:
        next(csv_file)  # Skippo la prima riga
        csv_reader = csv.reader(csv_file, delimiter=",")

        for temp_list in csv_reader:
            avg_route_length = temp_list[0]
            avg_speed = temp_list[1]
            avg_duration = temp_list[2]

        data_statistic = [avg_route_length, avg_duration]
        lables_data_statistic = ["Lunghezza Media", "Durata Media"]
        generate_bar(data_statistic, lables_data_statistic, "statistics", "dynamic_area", "100%", None)



def read_csv_stopinfo(strategia, scenario):
    with open("../output/"+strategia+"/"+scenario+"/csv/stopinfo.csv", "r") as csv_file:
        next(csv_file)  # Skippo la prima riga
        csv_reader = csv.reader(csv_file, delimiter=",")

        number_vec = len(get_vehicle_from_xml())
        counter_parked = 0
        for temp_list in csv_reader:
            counter_parked += 1

        counter_not_parked = number_vec - counter_parked

        # num: number_vec = X : 100 ---> (num * 100)/number_vec
        percentuale_parked = (counter_parked * 100) / number_vec
        percentuale_notparked = (counter_not_parked * 100) / number_vec

        data_percentage = [percentuale_parked, percentuale_notparked]
        labels_percentage = ["Trovato %", "Non Trovato %"]

        data_count = [counter_parked, counter_not_parked]
        data_labels_count = ["Trovato", "Non trovato"]

        # generate_bar(data_count, data_labels_count, "stopinfo", "dynamic_area", "100%", None)
        # generate_bar(data_percentage, labels_percentage, "stopinfo_%_", "dynamic_area", "100%", None)
        # generate_pie(data_percentage, labels_percentage, "stopinfo_%_", strategia, scenario)


def generate_bar(data, data_labels, name_out, strategia, scenario, xy_lables):
    pyplot.figure(figsize=(5, 6), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia+"/"+scenario+"/"+"plots/" + name_out + "_bar_" + "_nogrid")

    pyplot.figure(figsize=(5, 6), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.grid(color='#95a5a6', linestyle='--', linewidth=1.5, axis='y', alpha=0.7)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_grid")


def generate_bar_yscale(data, data_labels, name_out, strategia, scenario, xy_lables):
    pyplot.figure(figsize=(6, 7), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.yscale("symlog")
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia+"/"+scenario+"/"+"plots/" + name_out + "_nogrid")

    pyplot.figure(figsize=(6, 7), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.yscale("symlog")
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.grid(color='#95a5a6', linestyle='--', linewidth=1.5, axis='y', alpha=0.7)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_grid")


def generate_pie(data, data_labels, name_out, strategia, scenario):
    pyplot.figure(figsize=(10, 7), dpi=120)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=colors_palette)
    pyplot.legend()
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", "") + "_noexplode")

    pyplot.figure(figsize=(10, 7), dpi=120)
    myexplode = []
    for i in range(0, len(data)):
        myexplode.append(0.1)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=colors_palette, explode=myexplode)
    pyplot.legend()
    pyplot.axis("equal")
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/"  + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", "") + "_noshadow")

    pyplot.figure(figsize=(10, 7), dpi=120)
    myexplode = []
    for i in range(0, len(data)):
        myexplode.append(0.1)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=True, colors=colors_palette, explode=myexplode)
    pyplot.legend()
    pyplot.axis("equal")
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", "") + "_shadow")


def main():
    list_vec = get_vehicle_from_xml()
    read_csv_stopinfo("dynamic_area", "100%")
    read_csv_statistics("dynamic_area", "100%")


if __name__ == "__main__":
    main()
