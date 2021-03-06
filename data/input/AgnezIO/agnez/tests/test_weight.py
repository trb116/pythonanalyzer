import numpy as np
from agnez import grid2d


def test_grid2d():
    W = np.random.normal(size=(100, 28*28))
    A = grid2d(W)
    assert A.shape == (291, 291)
