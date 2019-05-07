import redbaron
import matplotlib.pyplot as plt

simple_calls, chained_calls, print_calls = 0, 0, 0

# method that returns a string containing the new
def process_code(py_code):
    # create the ast
    ast = redbaron.RedBaron(py_code)

    global simple_calls, chained_calls, print_calls

    # replaces all traditional function calls
    for node in ast.find_all("atomtrailers"):
        # every CallNode is preceded by a NameNode that contains the name of
        # the function
        for i in range(len(node.value)):
            if isinstance(node.value[i], redbaron.nodes.CallNode):
                # we replace the NameNode value
                node.value[i - 1].replace("foo")

                # i < 3 means there is no trainwreck of object accesses and
                # func calls, like z.y().x()
                if i < 3:
                    simple_calls += 1
                else:
                    chained_calls += 1

    # replaces (almost) all print function calls
    for node in ast.find_all("print"):
        parent = node.parent

        # reassigning top-level nodes doesn't work at the moment
        # todo: replace top-level prints as well
        if(isinstance(parent, redbaron.redbaron.RedBaron)):
            break

        # looks for the node in the parent's children, such that it can get
        # reassigned to a foo function call node, while keeping the same
        # parameters
        for i in range(len(parent.value)):
            if (parent.value[i] == node):
                if isinstance(node.value[0], \
                        redbaron.nodes.AssociativeParenthesisNode):
                    # handle new python print("abcd") syntax
                    parent.value[i] = redbaron.RedBaron("foo" + \
                                                str(node.value[0]))
                else:
                    # handle old python print "abcd" syntax
                    parent.value[i] = redbaron.RedBaron("foo(" + \
                                                str(node.value[0]) + ")")
        print_calls += 1
    # unparses the AST and returns the code
    return ast.dumps()

# helper function that takes all python files from input_path and stores them
# under output_path for a side by side comparison
def process_py_file(input_path, output_path, file_id):
    try:
        with open(input_path) as py_input:
            original_code = py_input.read()
            processed_code = process_code(original_code)

            output_path += str(file_id) + "_"
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
        print(e, " occuring at ", input_path)

def plot_stats():
    labels = 'Simple calls', 'Chained function calls', 'Print calls'

    sizes = [simple_calls, chained_calls, print_calls]
    explode = (0, 0.1, 0) #explode the chained function calls == bad practice

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')

    print('Saving function calls stats at ../data/call_stats.png')
    plt.savefig('../data/call_stats.png')

if __name__ == "__main__":
    # uncomment code for easy debugging
    #with open("../test/input/chained func calls.py") as f:
    #    print(process_code(f.read()))
    #    print(simple_calls, chained_calls, print_calls)
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

    plot_stats()

# below is code for changing all the path entries to match our naming scheme
    # newf = open("../data/paths2.txt", "w")
    # if line[14] == 'a' or line[14] == 'A':
    #    newf.write("../data/input" + line[13:])
