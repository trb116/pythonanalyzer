import redbaron

def process_code(py_code):
    ast = redbaron.RedBaron(py_code)

    for node in ast.find_all("atomtrailers"):
        #print(node.help())
        for i in range(len(node.value)):
            if isinstance(node.value[i], redbaron.nodes.CallNode):
                node.value[i - 1].replace("foo")

    for node in ast.find_all("print"):
        parent = node.parent
        if(isinstance(parent, redbaron.redbaron.RedBaron)):
            break
        for i in range(len(parent.value)):
            if (parent.value[i] == node):
                if isinstance(node.value[0], redbaron.nodes.AssociativeParenthesisNode):
                    parent.value[i] = redbaron.RedBaron("foo" + \
                                                str(node.value[0]))
                else:
                    parent.value[i] = redbaron.RedBaron("foo(" + \
                                                str(node.value[0]) + ")")

    return ast.dumps()

def process_py_file(input_path, output_path, cnt):
    try:
        with open(input_path) as py_input:
            original_code = py_input.read()
            processed_code = process_code(original_code)

            output_path += str(cnt) + "_"
            output_path_original = output_path + "original"
            output_path_processed = output_path + "processed"

            with open(output_path_original, "w") as py_output:
                py_output.write(original_code)
                py_output.close()

            with open(output_path_processed, "w") as py_output:
                py_output.write(processed_code)
                py_output.close()

            py_input.close()
    except Exception as e:
        print(input_path)
        print(e)
        #pass

if __name__ == "__main__":
    #with open("../data/input/Akagi201/learning-python/template/mako/hello_world/hello4.py") as f:
    #    print(process_code(f.read()))
    #    exit()

    with open("paths.txt") as paths_file:
        cnt = 0
        for line in paths_file:
            if cnt == 1000:
                # stop at 1000 files
                break
            # :-1 is to remove the newline
            process_py_file(line[:-1], "../data/output/", cnt)
            cnt += 1

# below is code for changing all the path entries to match our naming scheme
    # newf = open("../data/paths2.txt", "w")
    # if line[14] == 'a' or line[14] == 'A':
    #    newf.write("../data/input" + line[13:])
