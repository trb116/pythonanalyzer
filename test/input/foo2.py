class A:

    def __init__(self):
        self.x = 3

class B:

    def __init__(self, A):
        self.y = A

if __name__ == "__main__":
  z = B(A())
  print(z.y.x)
