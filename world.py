import math
import operator
import time
import messages

""" D&D 5e Combat Simulator battle grid ============================ """

occupied = []

def get_dist(A, B):
    """ Return distance between coordinates A and B in ft.
    this is the exact movement cost from A to B """
    return round(math.sqrt(sum([(s - d) ** 2 for s, d, in zip(A, B)]))) * 5

def get_path(A, B):
    """ Rerturn all coordinates between two points in three-dimensional
    cartesian coordinates. Creatures always use the shortest path.
    :param A      current position as (x, y, z)
    :param B      destination as (x, y, z)
    :type A       (int, int, int)
    Positive z coordinates use flying speed.
    Negative z coordinates use burrowing speed. """

    def make_path(s, d, j):
        return [i for i in range(s, d + j, j)]

    x0, y0, z0 = A
    x1, y1, z1 = B

    """ Build path vector for each dimension """
    j = 1
    if x0 > x1:
        j = -1
    pathx = make_path(x0, x1, j)#[i for i in range(x0, x1 + j, j)]

    j = 1
    if y0 > y1:
        j = -1
    pathy = make_path(y0, y1, j)#[i for i in range(y0, y1 + j, j)]

    j = 1
    if z0 > z1:
        j = -1
    pathz = make_path(z0, z1, j)#[i for i in range(z0, z1 + j, j)]

    """ Find longest path vector """
    lx, ly, lz = len(pathx), len(pathy), len(pathz)
    longest = max([lx, ly, lz])

    """ Stretch path vectors according to the longest path """
    if longest == lx:
        jy = ly / lx
        jz = lz / lx
        pathy = [pathy[int(i * jy)] for i in range(0, lx)]
        pathz = [pathz[int(i * jz)] for i in range(0, lx)]
    elif longest == ly:
        jx = lx / ly
        jz = lz / ly
        pathx = [pathx[int(i * jx)] for i in range(0, ly)]
        pathz = [pathz[int(i * jz)] for i in range(0, ly)]
    elif longest == lz:
        jx = lx / lz
        jy = ly / lz
        pathx = [pathx[int(i * jx)] for i in range(0, lz)]
        pathy = [pathy[int(i * jy)] for i in range(0, lz)]

    """ Combine path vectors into path of coordinates """
    # return {get_dist(A, d):d for d in zip(pathx, pathy, pathz)}
    return [i for i in zip(pathx, pathy, pathz)]

def is_adjacent(A, B):
    """ Return True if A is adjacent (or overlapping) to B """
    x0, y0, z0 = A
    x1, y1, z1 = B

    diff_x = abs(x0-x1) in [1, 0]
    diff_y = abs(y0-y1) in [1, 0]
    diff_z = abs(z0-z1) in [1, 0]

    return all([diff_x, diff_y, diff_z])

def get_opposite(A, B, creature):
    """ Return path to the most distant coordinate to B
    creature in A can reach with given speed. Ignore
     z-axis as it is irrelevant """

    f = math.floor(2 * creature.speed['ground'] / 5)

    if A == B:
        return get_path(A, A)

    x0, y0, z0 = A
    x1, y1, z1 = B

    jx = x0 - x1
    jy = y0 - y1

    if abs(jx) >= abs(jy):
        ix = jx / abs(jx)
        iy = jy / abs(jx)
    elif abs(jx) <= abs(jy):
        ix = jx / abs(jy)
        iy = jy / abs(jy)

    return get_path(A, (x0 + round(f*ix), y0 + round(f*iy), 0))

def close_distance(creature, path, reach, run=False):

    """ Store start position """
    sx, sy, sz = creature.position

    """ Set speed multiplier if running """
    if run:
        multi = 2
        moves = "runs"
    else:
        multi = 1
        moves = "moves"

    for coordinates in reversed(path[:-1]):
        x, y, z = coordinates
        d = get_dist(creature.position, coordinates) - reach
        #print(creature.speed['ground'] * multi, d)
        if creature.speed['ground'] * multi >= d:
            occupied.append([coordinates, creature])
            creature.position = coordinates
            creature.speed['ground'] -= d
            msg = "%s %s %i ft. from (%i, %i, %i) to (%i, %i, %i)" \
                  % (creature.name, moves, d, sx, sy, sz, x,y,z)
            messages.IO.printmsg(msg, level=3, indent=True, print_turn=True)
            return d, coordinates


def keep_distance(creature, enemy, path, reach):

    """ Store start position """
    sx, sy, sz = creature.position
    A = creature.position
    B = enemy.position

    for coordinates in reversed(path):
        x, y, z = coordinates
        d = get_dist(A, coordinates)
        de = get_dist(B, coordinates)
        if creature.speed['ground'] >= d and reach >= de:
            occupied.append([coordinates, creature])
            creature.position = coordinates
            creature.speed['ground'] -= d
            msg = "%s moves %i ft. from (%i, %i, %i) to (%i, %i, %i)" \
                      % (creature.name, d, sx, sy, sz, x,y,z)
            messages.IO.printmsg(msg, level=2, indent=True, print_turn=True)
            return d, coordinates
    print('KEEP DISTANCE ERROR')

'''
A = (0,0,0)
B = (0,4,0)
speed = {'ground': 40, 'fly': 50}
reach = 5

path = get_opposite(A, B, speed)

d, c = move_to_farthest(A, path, speed, reach)
print(d, c)
'''

A = (19, 8, 0)
B = (-20, -7, -0)
print(is_adjacent(A,B))