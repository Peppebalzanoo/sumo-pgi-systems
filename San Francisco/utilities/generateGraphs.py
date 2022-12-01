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


def read_csv_emmissions(strategia, scenario, num_vec):
    temp_emissions_CO = temp_emissions_CO2 = temp_emissions_HC = temp_emissions_PM = temp_emissions_NO = temp_fuel_consumed = 0.0

    with open("../output/"+strategia+"/"+scenario+"/csv/emissions.csv", "r") as csv_file:
        next(csv_file)  # Skippo la prima riga
        csv_reader = csv.reader(csv_file, delimiter=",")

        for temp_list in csv_reader:
            temp_emissions_CO += float(temp_list[0])
            temp_emissions_CO2 += float(temp_list[1])
            temp_emissions_HC += float(temp_list[2])
            temp_fuel_consumed += float(temp_list[3])

        average_emissions_CO = temp_emissions_CO/num_vec
        average_emissions_CO2 = temp_emissions_CO2/num_vec
        average_emissions_HC = temp_emissions_HC/num_vec
        average_fuel_consumed = temp_fuel_consumed/num_vec

        data_emissions = [average_emissions_CO, average_emissions_CO2, average_fuel_consumed]
        labels_data_emissions = ["CO", "CO2", "Fuel"]

        generate_bar_yscale(data_emissions, labels_data_emissions, "emissions", strategia, scenario, None)
        generate_pie(data_emissions, labels_data_emissions, "emissions", strategia, scenario)


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
        generate_bar(data_statistic, lables_data_statistic, "statistics", strategia, scenario, None)



def read_csv_stopinfo(strategia, scenario):
    with open("../output/"+strategia+"/"+scenario+"/csv/stopinfo.csv", "r") as csv_file:
        next(csv_file)  # Skippo la prima riga
        csv_reader = csv.reader(csv_file, delimiter=",")

        number_vec = len(get_vehicle_from_xml())
        counter_parked = 0
        for temp_list in csv_reader:
            counter_parked += 1

        counter_not_parked = number_vec - counter_parked

        # counter_parked : number_vec = X : 100 ---> X = (counter_parked * 100)/number_vec
        percentuale_parked = (counter_parked * 100)/number_vec
        # counter_notparked : number_vec = X : 100 ---> X = (counter_notparked * 100)/number_vec
        percentuale_notparked = (counter_not_parked * 100)/number_vec

        data_percentage = [percentuale_parked, percentuale_notparked]
        labels_percentage = ["Trovato %", "Non Trovato %"]

        generate_bar(data_percentage, labels_percentage, "stopinfo_%_", strategia, scenario, None)
        generate_pie(data_percentage, labels_percentage, "stopinfo_%_", strategia, scenario)


def generate_bar(data, data_labels, name_out, strategia, scenario, xy_lables):
    pyplot.figure(figsize=(5, 6), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia+"/"+scenario+"/"+"plots/" + name_out + "_bar_" + "_nogrid")
    pyplot.close()

    pyplot.figure(figsize=(5, 6), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.grid(color='#95a5a6', linestyle='--', linewidth=1.5, axis='y', alpha=0.7)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_grid")
    pyplot.close()

def generate_bar_yscale(data, data_labels, name_out, strategia, scenario, xy_lables):
    pyplot.figure(figsize=(6, 7), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.yscale("symlog")
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia+"/"+scenario+"/"+"plots/" + name_out + "_nogrid")
    pyplot.close()


    pyplot.figure(figsize=(6, 7), dpi=120)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.yscale("symlog")
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.grid(color='#95a5a6', linestyle='--', linewidth=1.5, axis='y', alpha=0.7)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_grid")
    pyplot.close()



def generate_pie(data, data_labels, name_out, strategia, scenario):
    pyplot.figure(figsize=(10, 7), dpi=120)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=colors_palette)
    pyplot.legend()
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", "") + "_noexplode")
    pyplot.close()

    pyplot.figure(figsize=(10, 7), dpi=120)
    myexplode = []
    for i in range(0, len(data)):
        myexplode.append(0.1)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=colors_palette, explode=myexplode)
    pyplot.legend()
    pyplot.axis("equal")
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/"  + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", ""))
    pyplot.close()


def main():
    list_vec = get_vehicle_from_xml()

    # STRATEGIA: dynamic_area, SCENARIO: 100%
    read_csv_stopinfo("dynamic_area", "100%")
    read_csv_statistics("dynamic_area", "100%")
    read_csv_emmissions("dynamic_area", "100%", len(list_vec))

    # STRATEGIA: dynamic_area, SCENARIO: 70%
    read_csv_stopinfo("dynamic_area", "70%")
    read_csv_statistics("dynamic_area", "70%")
    read_csv_emmissions("dynamic_area", "70%", len(list_vec))

    # STRATEGIA: dynamic_area, SCENARIO: 50%
    read_csv_stopinfo("dynamic_area", "50%")
    read_csv_statistics("dynamic_area", "50%")
    read_csv_emmissions("dynamic_area", "50%", len(list_vec))




if __name__ == "__main__":
    main()
