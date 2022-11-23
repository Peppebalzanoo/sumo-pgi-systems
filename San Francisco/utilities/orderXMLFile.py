import xml.etree.ElementTree as ElementTree


def read():
    tree = ElementTree.parse('test.rou.xml')
    root = tree.getroot()
    # print(root.tag)
    # print(root.attrib)

    # Lista di lista di tuple
    list_of_list_tuple = []
    for child in root:
        list_of_list_tuple.append(list(child.items()))
    # print(list_of_list_tuple)

    temp_list_tuple = []
    for idx in range(0, len(list_of_list_tuple)):
        temp_tupla = list_of_list_tuple[idx][0]
        temp_list_tuple.append(temp_tupla)
    # print(temp_list_tuple)

    temp_list_tuple.sort(key=lambda elem: int(elem[1]))

    new_root = ElementTree.Element(root.tag)
    for tupla in temp_list_tuple:
        print(tupla)
        for child in root:
            if tupla[1] == child.attrib.get("id"):
                child.attrib.pop("arrival")
                child.attrib["depart"] = "0.00"
                new_root.append(child)
                break
    new_tree = ElementTree.ElementTree(new_root)
    new_tree.write("out.xml", encoding="utf-8", xml_declaration=True)


def main():
    read()


if __name__ == "__main__":
    main()
