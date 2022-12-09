import subprocess


def main():
    command_start_strategia1 = ["python", "./strategia1.py"]
    print("Esecuzione di strategia1.py in corso...")
    sub_start_strategia1 = subprocess.run(command_start_strategia1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)

    print("Esecuzione di converXmlToCsv...")
    command_convert_strategia1 = ["python", "./utilities/convertXmlToCsv.py"]
    sub_convert_strategia1 = subprocess.run(command_convert_strategia1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)

    print("Esecuzione di generateGraphs...")
    command_genplot_strategia1 = ["python", "./utilities/generateGraphs.py"]
    sub_genplot_strategia1 = subprocess.run(command_genplot_strategia1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)

if __name__ == "__main__":
    main()
