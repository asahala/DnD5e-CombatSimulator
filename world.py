import math
import operator
import time
import messages

""" D&D 5e Combat Simulator battle grid ============================ """

""" Team names """

TEAM_A = 'Team North'
TEAM_B = 'Team South'

symbols = {TEAM_A: ' ° ', TEAM_B: ' * '}

class Map:

    statics = {}       # Container for static objects such as corpses
    paths = {}
    occupied = {}

    @classmethod
    def remove(cls, creature):
        try:
            cls.occupied.pop(creature.position)
        except:
            pass

    @classmethod
    def update(cls, creature):
        """ Update world map with creature positions and mark
        restricted coordinates. Corpses do not restrict movement. """
        if creature.is_dead:
            cls.statics[creature.position] = ' † '
            cls.remove(creature)
        else:
            #Map.occupied[creature.position] = creature.party
            #symbol = creature.name
            cls.occupied[creature.position] = creature
        #Map.coords.setdefault(creature.position, []).append(symbol)

    @classmethod
    def reset_paths(cls):
        cls.paths = {}

    @classmethod
    def reset_map(cls):
        cls.statics = {}
        cls.occupied = {}
        cls.paths = {}

    @classmethod
    def get_penalty(cls, creature, coordinates):
        """ Check if coordinates on path are blocked. Double movement
        if ally, quadruple if enemy (assume that going around the
         occupied enemy position consumes 15 ft of movement) """
        occupied_by = cls.occupied.get(coordinates, None)
        if occupied_by is None:
            return 0
        elif occupied_by.party == creature.party:
            return 5
        else:
            return 10

def get_dist(A, B):
    """ Return distance between coordinates A and B in ft.
    this is the exact movement cost from A to B """
    return round(math.sqrt(sum([(s - d) ** 2 for s, d, in zip(A, B)]))) * 5

def get_adjacent(coords):
    x, y, z = coords
    for dx in [-1,1,0]:
        for dy in [-1,1,0]:
            nx = x + dx
            ny = y + dy
            npos = (nx, ny, z)
            if not npos in Map.occupied and npos != coords:
            #if Map.occupied.get((nx,ny,z), None) is None:
                yield nx, ny, z
    return coords

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

    """ Check if destination is obstructed, try to find closest
     square adjacent to the destination """
    if B in Map.occupied:
        adjacent = list(get_adjacent(B))
        """ Return False if all adjacent cells are occupied """
        # TODO: Make creature target someone else
        if not adjacent:
            return False
        B = min(sorted([(get_dist(A, x), x) for x in adjacent]))[-1]

    x0, y0, z0 = A
    x1, y1, z1 = B

    """ Build path vector for each dimension """
    j = 1
    if x0 > x1:
        j = -1
    pathx = make_path(x0, x1, j)

    j = 1
    if y0 > y1:
        j = -1
    pathy = make_path(y0, y1, j)

    j = 1
    if z0 > z1:
        j = -1
    pathz = make_path(z0, z1, j)

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
    return [i for i in zip(pathx, pathy, pathz)]

def is_adjacent(A, B):
    """ Return True if A is adjacent (or overlapping) to B """
    x0, y0, z0 = A
    x1, y1, z1 = B

    diff_x = abs(x0-x1) in [1, 0]
    diff_y = abs(y0-y1) in [1, 0]
    diff_z = abs(z0-z1) in [1, 0]

    return all([diff_x, diff_y, diff_z])

def any_is_adjacent(A, B: list) -> bool:
    """ Return True if any position listed in B is adjacent to A """
    return any(is_adjacent(A, b) for b in B)

def get_opposite(A, B, speed):
    """ Return path to the most distant coordinate to B
    creature A can reach with given speed. Ignore
     z-axis as it is irrelevant """

    f = math.floor(speed / 5)

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

def force_move(source, target, path, reason):
    """ Force move creature, e.g. knockback """
    sx, sy, sz = target.position
    Map.remove(target)

    """ Check if path is free; if obstructed take three damage
     per tile """
    damage = 0
    for pos in reversed(path):
        if pos not in Map.occupied:
            end_position = pos
            break
        else:
            damage += 3

    if damage:
        target.take_damage(source, damage, 'bludgeoning', 1)
    target.position = end_position
    Map.update(target)
    x, y, z = target.position
    msg = "-> %s forced from (%i, %i, %i) to (%i, %i, %i) by %s" % (target.name, sx, sy, sz, x, y, z, reason)
    messages.IO.printmsg(msg, level=3, indent=True, print_turn=False)

def close_distance(creature, path, reach, run=False):
    """ Store start position and update map position"""
    sx, sy, sz = creature.position

    """ Set speed multiplier if running """
    if run:
        move_points = creature.speed['ground'] * 2
        moves = "runs"
    else:
        move_points = creature.speed['ground']
        moves = "moves"

    """ Disallow moving if moving points are depleted """
    if move_points < 5 or not path:
        return 0, creature.position

    """ Get enemy positions in the map that are not in the path """
    enemy_pos = [pos for pos, party in Map.occupied.items()
                if party != creature.party and pos not in path]

    penalty = 0
    distance = 0
    coordinates = creature.position
    for coordinates in path:

        Map.paths[coordinates] = symbols[creature.party]

        """ Check if enemies are occupying coordinates next to the
        current position, add 5 ft penalty for each """
        if enemy_pos:
            adjacent = [is_adjacent(coordinates, B) for B in enemy_pos]
            penalty += sum(adjacent) * 5

        """ Check if creatures are blocking the path. Add 15 ft penalty
        for enemies and 5 ft for allies """
        base_cost = get_dist(creature.position, coordinates)
        penalty += Map.get_penalty(creature, coordinates)
        distance = base_cost + penalty

        if move_points == distance:
            break


    creature.speed['ground'] = creature.speed['ground'] - distance
    creature.position = coordinates
    creature.distance = base_cost

    x, y, z = coordinates
    msg = "%s %s %i ft. from (%i, %i, %i) to (%i, %i, %i)" \
          % (creature.name, moves, base_cost, sx, sy, sz, x, y, z)
    messages.IO.printmsg(msg, level=3, indent=True, print_turn=True)


    return distance, coordinates


def keep_distance(creature, enemy, path, reach, run=False):

    ## TODO: Merge function with close_distance()

    """ Store start position """
    sx, sy, sz = creature.position
    A = creature.position
    #B = enemy.position

    """ Set speed multiplier if running """
    if run:
        move_points = creature.speed['ground'] * 2
        moves = "runs"
    else:
        move_points = creature.speed['ground']
        moves = "moves"

    """ Disallow moving if moving points are depleted """
    if move_points < 5 or not path:
        return 0, creature.position

    """ Get enemy positions in the map that are not in the path """
    enemy_pos = (pos for pos, party in Map.occupied.items()
                if party != creature.party and pos not in path)

    penalty = 0
    coordinates = creature.position
    for coordinates in path:

        Map.paths[coordinates] = symbols[creature.party]

        """ Check if enemies are occupying coordinates next to the
        current position, add 5 ft penalty for each """
        #if enemy_pos:
        #    adjacent = [is_adjacent(coordinates, B) for B in enemy_pos]
        #   penalty += sum(adjacent) * 5

        """ Check if creatures are blocking the path. Add 15 ft penalty
        for enemies and 5 ft for allies """
        distance = get_dist(creature.position, coordinates)
        #penalty += Map.get_penalty(creature, coordinates)
        #distance = base_cost + penalty

        """ Stop if running out of reach or at destination """
        if reach == get_dist(coordinates, enemy.position) \
                and move_points >= distance:
            break
        if move_points <= distance:
            break

    creature.speed['ground'] = creature.speed['ground'] - distance
    creature.position = coordinates

    x, y, z = coordinates
    msg = "%s %s %i ft. from (%i, %i, %i) to (%i, %i, %i)" \
          % (creature.name, moves, distance, sx, sy, sz, x, y, z)
    messages.IO.printmsg(msg, level=3, indent=True, print_turn=True)

    return distance, coordinates


last_vecs = {}

def print_coords(size=15):

    global last_vecs

    def format(c):
        c = str(c)
        if len(c) == 3:
            return c
        if len(c) == 2:
            return c + " "
        else:
            return " " + c + " "

    if messages.VERBOSE_LEVEL == 4:
        """ Calculate the center point of action. If all creatures die
        freeze map to the last position """
        vecs = {'x': 0, 'y': 0, 'z': 0}
        if len(Map.occupied) > 0:
            for i, dim in enumerate(vecs):
                vecs[dim] = round(sum(p[i] for p in Map.occupied) / len(Map.occupied))
                last_vecs = vecs
        else:
            vecs = last_vecs

        x_axis = [i+vecs['x'] for i in range(-size, 0)] +\
                 [i+vecs['x'] for i in range(0, size+1)]
        y_axis = [i+vecs['y'] for i in range(size, 0, -1)] +\
                 [i+vecs['y'] for i in range(0, -size+1, -1)]

        """ Print header """
        print('   ' + "".join([format(x) for x in x_axis]))
        rows = []
        for y in y_axis:
            cols = []
            for x in x_axis:
                pos = (x, y, 0)
                symbol = Map.statics.get(pos, Map.paths.get(pos, " · "))
                override = Map.occupied.get(pos, None)
                if override is not None:
                    if override.party == TEAM_A:
                        symbol = override.name[0:2] + override.name[-1]
                    else:
                        symbol = override.name[0:2].lower() + override.name[-1].lower()

                cols.append(symbol)
            rows.append(cols)

        i = 0
        for r in rows:
            print(format(y_axis[i]) + ''.join(r))
            i += 1


#print_coords()
'''
A = (0,0,0)
B = (0,4,0)
speed = {'ground': 40, 'fly': 50}
reach = 5
path = get_opposite(A, B, speed)
d, c = move_to_farthest(A, path, speed, reach)
print(d, c)
'''

#print(is_adjacent(A,B))

#A = (0,0,0)

#for x in get_adjacent(A):
#    print(x)
