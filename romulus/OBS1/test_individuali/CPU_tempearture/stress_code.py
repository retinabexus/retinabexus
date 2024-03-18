import random
import numpy
from time import sleep


while True :
    a = numpy.random.random((10000, 10000))
    b = numpy.random.random((10000, 10000))
    c = numpy.matmul(a,b)
    d= numpy.linalg.det(c)

    





