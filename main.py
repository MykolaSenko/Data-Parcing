from script.script import parse_data

if __name__ == "__main__":
    INPUT_FILE = "source_data/Input_File_01.txt"
    OUTPUT_FILE = "output_data/output.csv"
    parse_data(INPUT_FILE, OUTPUT_FILE)