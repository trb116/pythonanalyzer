from os import listdir

import sys
sys.path.insert(0, "../src")

from python_analyzer import process_code

if __name__ == "__main__":
    # ensures the program correctly counts the number of basic function calls,
    # chained function calls and print function calls

    _, simple_calls, chained_calls, print_calls, = \
                        process_code(open('input/chained func calls.py').read())
    assert simple_calls == 3
    assert chained_calls == 1
    assert print_calls == 2

    print("All tests successfully passed")
