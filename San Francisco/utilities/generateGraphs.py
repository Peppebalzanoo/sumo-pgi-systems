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

def read_csv_trip_and_stop_info(strategia, scenario):
    count_between_0_and_5min = count_between_5_and_10min = count_plus_10min = 0

    with open("../output/"+strategia+"/"+scenario+"/csv/tripinfo.csv", "r") as csv_file_tripinfo, open("../output/"+strategia+"/"+scenario+"/csv/stopinfo.csv", "r") as csv_file_stopinfo:

        next(csv_file_tripinfo)  # Skippo la prima riga di csv_file_tripinfo
        csv_reader_tripinfo = csv.reader(csv_file_tripinfo, delimiter=",")

        next(csv_file_stopinfo)  # Skippo la prima riga di csv_file_stopinfo
        csv_reader_stopinfo = csv.reader(csv_file_stopinfo, delimiter=",")

        list_val = []
        for temp_list_stop in csv_reader_stopinfo:
            temp_vecID = temp_list_stop[0]
            temp_start_stop = float(temp_list_stop[2])
            for temp_list_trip in csv_reader_tripinfo:
                if temp_vecID == temp_list_trip[0]:
                    temp_depart = float(temp_list_trip[1])
                    list_val.append(temp_start_stop - temp_depart)
                    break

        for val in list_val:
            if 0.0 <= val <= 300.0:
                count_between_0_and_5min += 1
            elif 300.0 <= val <= 600.0:
                count_between_5_and_10min += 1
            else:
                count_plus_10min += 1

        print("count_between_0_and_5min:", count_between_0_and_5min)
        print("count_between_5_and_10min:", count_between_5_and_10min)
        print("count_plus_10min:", count_plus_10min)

        data = [count_between_0_and_5min, count_between_5_and_10min, count_plus_10min]
        lables_data_pie = ["between_0_and_5min", "between_5_and_10min", "plus_10min"]
        lables_data_bar = ["0_and_5min", "5_and_10min", "plus_10min"]
        generate_bar(data, lables_data_bar, "counter", strategia, scenario, None)
        generate_pie(data, lables_data_pie, "counter", strategia, scenario)

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

        average_emissions_CO = float(temp_emissions_CO/num_vec)
        average_emissions_CO2 = float(temp_emissions_CO2/num_vec)
        average_emissions_HC = float(temp_emissions_HC/num_vec)
        average_fuel_consumed = float(temp_fuel_consumed/num_vec)

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

        print("Lunghezza media:", avg_route_length)
        print("Duarata media:", avg_duration)
        print("Velocità media:", avg_speed)

def read_csv_stopinfo(strategia, scenario):
    with open("../output/"+strategia+"/"+scenario+"/csv/stopinfo.csv", "r") as csv_file:
        next(csv_file)  # Skippo la prima riga
        csv_reader = csv.reader(csv_file, delimiter=",")

        number_vec = len(get_vehicle_from_xml())
        counter_parked = 0
        for temp_list in csv_reader:
            counter_parked += 1

        counter_not_parked = number_vec - counter_parked

        print("SU UN TOTALE DI", number_vec, "VEICOLO, HANNO PARCHEGGIATO:", counter_parked, ", NON HANNO PARCHEGGIATO:", counter_not_parked)

        # counter_parked : number_vec = X : 100 ---> X = (counter_parked * 100)/number_vec
        percentuale_parked = (counter_parked * 100)/number_vec

        # counter_notparked : number_vec = X : 100 ---> X = (counter_notparked * 100)/number_vec
        percentuale_notparked = (counter_not_parked * 100)/number_vec

        data_percentage = [percentuale_parked, percentuale_notparked]
        labels_percentage = ["Trovato %", "Non Trovato %"]

        generate_bar(data_percentage, labels_percentage, "stopinfo_%_", strategia, scenario, None)
        generate_pie(data_percentage, labels_percentage, "stopinfo_%_", strategia, scenario)

def generate_bar(data, data_labels, name_out, strategia, scenario, xy_lables):
    pyplot.figure(figsize=(6, 7), dpi=120)
    pyplot.title(strategia+" "+scenario)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia+"/"+scenario+"/"+"plots/" + name_out + "_bar_" + "_nogrid")
    pyplot.close()

    pyplot.figure(figsize=(6, 7), dpi=120)
    pyplot.title(strategia+" "+scenario)
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
    pyplot.title(strategia+" "+scenario)
    if xy_lables is not None:
        pyplot.xlabel(xy_lables[0])
        pyplot.ylabel(xy_lables[1])
    pyplot.yscale("symlog")
    pyplot.xticks(range(0, len(data)), data_labels)
    pyplot.bar(range(0, len(data)), height=data, width=0.5, color=colors_palette[0])
    pyplot.savefig("../output/" + strategia+"/"+scenario+"/"+"plots/" + name_out + "_nogrid")
    pyplot.close()


    pyplot.figure(figsize=(6, 7), dpi=120)
    pyplot.title(strategia+" "+scenario)
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
    pyplot.title(strategia+" "+scenario)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=colors_palette)
    pyplot.legend()
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", "") + "_noexplode")
    pyplot.close()

    pyplot.figure(figsize=(10, 7), dpi=120)
    pyplot.title(strategia+" "+scenario)
    myexplode = []
    for i in range(0, len(data)):
        myexplode.append(0.1)
    pyplot.pie(data, labels=data_labels, autopct='%1.1f%%', startangle=0, shadow=False, colors=colors_palette, explode=myexplode)
    pyplot.legend()
    pyplot.axis("equal")
    pyplot.savefig("../output/" + strategia + "/"+scenario+"/"+"plots/" + name_out + "_pie_" + data_labels[0].lower().replace(" ", "") + "_" + data_labels[1].lower().replace(" ", ""))
    pyplot.close()

def main():
    list_vec = get_vehicle_from_xml()

    # STRATEGIA: strategia1, SCENARIO: 100%
    # print("# STRATEGIA: strategia1, SCENARIO: 100% #")
    # read_csv_stopinfo("strategia1", "100%")
    # read_csv_statistics("strategia1", "100%")
    # read_csv_emmissions("strategia1", "100%", len(list_vec))
    # read_csv_trip_and_stop_info("strategia1", "100%")

    # # STRATEGIA: strategia1, SCENARIO: 75%
    # print("\n# STRATEGIA: strategia1, SCENARIO: 75% #")
    # read_csv_stopinfo("strategia1", "75%")
    # read_csv_statistics("strategia1", "75%")
    # read_csv_emmissions("strategia1", "75%", len(list_vec))
    # read_csv_trip_and_stop_info("strategia1", "75%")

    # # STRATEGIA: strategia1, SCENARIO: 50%
    # # print("\n# STRATEGIA: strategia1, SCENARIO: 50% #")
    # read_csv_stopinfo("strategia1", "50%")
    # read_csv_statistics("strategia1", "50%")
    # read_csv_emmissions("strategia1", "50%", len(list_vec))
    # read_csv_trip_and_stop_info("strategia1", "50%")

# * ********************************************************************************************************************************************************************* * #

    # STRATEGIA: strategia2, SCENARIO: 100%
    # print("\n# STRATEGIA: strategia2, SCENARIO: 100% #")
    # read_csv_stopinfo("strategia2", "100%")
    # read_csv_statistics("strategia2", "100%")
    # read_csv_emmissions("strategia2", "100%", len(list_vec))
    # read_csv_trip_and_stop_info("strategia2", "100%")

    # STRATEGIA: strategia2, SCENARIO: 50%
    print("\n# STRATEGIA: strategia2, SCENARIO: 50% #")
    read_csv_stopinfo("strategia2", "50%")
    read_csv_statistics("strategia2", "50%")
    read_csv_emmissions("strategia2", "50%", len(list_vec))
    read_csv_trip_and_stop_info("strategia2", "50%")


# * ********************************************************************************************************************************************************************* * #


    # STRATEGIA: strategia3, SCENARIO: 100%
    # print("\n# STRATEGIA: strategia3, SCENARIO: 100% #")
    # read_csv_stopinfo("strategia3", "100%")
    # read_csv_statistics("strategia3", "100%")
    # read_csv_emmissions("strategia3", "100%", len(list_vec))
    # read_csv_trip_and_stop_info("strategia3", "100%")

    # STRATEGIA: strategia3, SCENARIO: 50%
    print("\n# STRATEGIA: strategia3, SCENARIO: 50% #")
    read_csv_stopinfo("strategia3", "50%")
    read_csv_statistics("strategia3", "50%")
    read_csv_emmissions("strategia3", "50%", len(list_vec))
    read_csv_trip_and_stop_info("strategia3", "50%")


# * ********************************************************************************************************************************************************************* * #


if __name__ == "__main__":
    main()
