import xml.etree.ElementTree as ElementTree


def reduce_to(percentage):
    tree = ElementTree.parse('../on_parking_100%.add.xml')
    root = tree.getroot()
    new_root = ElementTree.Element(root.tag)
    for elem in root.findall(".//parkingArea"):
        temp_attr_dictionary = elem.attrib
        
        # old_capacitiy : 100% = X : percentage% ---> X = (old_capacity * percentage)/100
        old_capacity = int(elem.attrib["roadsideCapacity"])
        new_capacity = int((old_capacity * percentage)/100)

        temp_attr_dictionary["roadsideCapacity"] = str(new_capacity)
        new_root.append(elem)

    new_tree = ElementTree.ElementTree(new_root)
    new_tree.write("../on_parking_"+str(percentage)+"%.add.xml", encoding="utf-8", xml_declaration=True)


    tree = ElementTree.parse('../off_parking_100%.add.xml')
    root = tree.getroot()
    new_root = ElementTree.Element(root.tag)
    for elem in root.findall(".//parkingArea"):
        temp_attr_dictionary = elem.attrib

        # old_capacitiy : 100% = X : percentage% ---> X = (old_capacity * percentage)/100
        old_capacity = int(elem.attrib["roadsideCapacity"])
        new_capacity = int((old_capacity * percentage)/100)

        temp_attr_dictionary["roadsideCapacity"] = str(new_capacity)
        new_root.append(elem)

    new_tree = ElementTree.ElementTree(new_root)
    new_tree.write("../off_parking_"+str(percentage)+"%.add.xml", encoding="utf-8", xml_declaration=True)


def main():
    reduce_to(70)
    reduce_to(50)

if __name__ == "__main__":
    main()
