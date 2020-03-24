import math
import operator
import time

def get_dist(A, B):
    """ Return distance between coordinates A and B in ft.
    this is the exact movement cost from A to B """
    return round(math.sqrt(sum([(s-d)**2 for s, d, in zip(A, B)]))) * 5

def get_path(A, B):
    """ Rerturn all coordinates between two points in three-dimensional
    cartesian coordinates. Creatures always use the shortest path.

    :param A      current position as (x, y, z)
    :param B      destination as (x, y, z)
    :type A       (int, int, int)

    Positive z coordinates use flying speed.
    Negative z coordinates use burrowing speed. """

    x0, y0, z0 = A
    x1, y1, z1 = B

    """ Build path vector for each dimension """
    j = 1
    if x0 > x1:
        j = -1
    pathx = [i for i in range(x0, x1+j, j)]
    
    j = 1
    if y0 > y1:
        j = -1    
    pathy = [i for i in range(y0, y1+j, j)]

    j = 1
    if z0 > z1:
        j = -1    
    pathz = [i for i in range(z0, z1+j, j)]

    """ Find longest path vector (for some reason max()
    without operator.itemgetter() is 50% slower """
    lx, ly, lz = len(pathx), len(pathy), len(pathz)
    longest = max([('lx', lx), ('ly', ly), ('lz', lz)],
                  key=operator.itemgetter(1))[0]
    
    """ Stretch path vectors according to the longest path """
    if longest == lx:
        jy = ly / lx
        jz = lz / lx
        pathy = [pathy[int(i*jy)] for i in range(0, lx)]
        pathz = [pathz[int(i*jz)] for i in range(0, lx)]
    elif longest == ly:
        jx = lx / ly
        jz = lz / ly
        pathx = [pathx[int(i*jx)] for i in range(0, ly)]
        pathz = [pathz[int(i*jz)] for i in range(0, ly)]
    elif longest == lz:
        jx = lx / lz
        jy = ly / lz
        pathx = [pathx[int(i*jx)] for i in range(0, lz)]
        pathy = [pathy[int(i*jy)] for i in range(0, lz)]

    """ Combine path vectors into path of coordinates """
    #return {get_dist(A, d):d for d in zip(pathx, pathy, pathz)}
    return [i for i in zip(pathx, pathy, pathz)]

st = time.time()
i = 0
while i < 1:
    A = (0,0,0)
    B = (41,11,0)
    r = get_path(A,B)
    for k in r:
        pass
    i += 1

print(time.time() - st)

class World:

    def __init__(self, size=200):
        self.max = int(size/2)
        self.min = -int(size/2)
        self.occupied = {}

    def move_to(self)
    

w = World(200)
