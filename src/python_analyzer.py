from redbaron import RedBaron

if __name__ == "__main__":
    with open ("../data/foo.py") as py_file:
        py_code = py_file.read()

    ast = RedBaron(py_code)
    for i in range(len(ast)):
        print(ast[i].help())
