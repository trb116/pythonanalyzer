class A:

    def __init__(self):
        self.x = 3

    def funcA(self):
        print("func A")

class B:

    def __init__(self, A):
        self.y = A

    def funcB(self):
        return self.y

if __name__ == "__main__":
  z = foo(foo())
  print(z.foo().foo())
