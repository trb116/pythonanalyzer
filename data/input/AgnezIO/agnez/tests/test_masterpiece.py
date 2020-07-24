import os
import numpy

from agnez import Mainpiece
from agnez.weight import Grid2D


def test_mainpiece():
    W = numpy.random.normal(size=(100, 100))
    model = (W,)
    artists = [Grid2D, ]
    mp = Mainpiece(artists=artists, model=model)
    mp.expose('test')
    file_path = os.path.dirname(os.path.realpath(__file__))
    assert os.path.exists(os.path.join(file_path, 'test.ipynb'))
