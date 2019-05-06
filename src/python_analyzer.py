from redbaron import RedBaron

if __name__ == "__main__":
    with open ("../data/foo.py") as py_file:
        py_code = py_file.read()

    ast = RedBaron(py_code)

    for node in ast.find_all("atomtrailers"):
        node.value[0].replace("foo")

    print(ast.dumps())
