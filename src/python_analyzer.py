from redbaron import RedBaron

def process_code(py_code):
    ast = RedBaron(py_code)

    for node in ast.find_all("atomtrailers"):
        node.value[0].replace("foo")

    return ast.dumps()

def process_py_file(input_path, cnt):
    try:
        with open(input_path) as py_input:
            original_code = py_input.read()
            processed_code = process_code(original_code)

            output_path = "../data/output/" + str(cnt) + "_"
            output_path_original = output_path + "original"
            output_path_processed = output_path + "processed"

            with open(output_path_original, "w") as py_output:
                py_output.write(original_code)
                py_output.close()

            with open(output_path_processed, "w") as py_output:
                py_output.write(processed_code)
                py_output.close()

            py_input.close()
    except:
        pass

if __name__ == "__main__":
    with open("paths.txt") as paths_file:
        cnt = 0
        for line in paths_file:
            if cnt == 1000:
                # stop at 1000 files
                break
            # :-1 is to remove the newline
            process_py_file(line[:-1], cnt)
            cnt += 1

# below is code for changing all the path entries to match our naming scheme
    # newf = open("../data/paths2.txt", "w")
    # if line[14] == 'a' or line[14] == 'A':
    #    newf.write("../data/input" + line[13:])
