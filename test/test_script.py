from os import listdir

import sys
sys.path.insert(0, "../src")

import python_analyzer

if __name__ == "__main__":
    # compares the processed outputs of the python source files under "input/"
    # to the expected outputs under "expected_output"
    for file_path in listdir("input"):
        input_f = open("input/" + file_path)
        input_code = input_f.read()

        expected_output_f = open("expected_output/" + file_path)
        expected_output = expected_output_f.read()

        if expected_output != python_analyzer.process_code(input_code):
            raise Exception("Comparison failed for " + file_path + "!")
