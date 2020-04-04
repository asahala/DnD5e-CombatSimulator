import messages
import world
from collections import Counter, defaultdict
from creature import Party
from definitions import *

class Encounter:

    def __init__(self, party1, party2):
        self.party1 = party1
        self.party2 = party2
        self.order_of_action = party1.combine_and_sort_by(party2, "initiative")

    def fight(self):

        DIVIDER = "=" * 70

        """ Simulate combat encounter until either of the parties has
        been killed """

        messages.IO.printmsg(self.party1.__repr__(), 1)
        messages.IO.printmsg(self.party2.__repr__(), 1)

        world.print_coords()

        round = 1
        while self.party1.is_alive and self.party2.is_alive:
            """ Reset path maps """
            world.Map.reset_paths()

            """ Begin round """
            turn = 1
            messages.IO.printmsg("\nROUND %i %s\n" % (round, DIVIDER), level=1, indent=False)
            for creature in self.order_of_action:
                messages.IO.turn = "%i (%s)" % (turn, creature.party)
                """ Get allies and enemies for the creature """
                allies, enemies = self.party1.get_teams(self.party2, creature)

                """ Allow only living creatures to act """
                if self.party1.is_alive and self.party2.is_alive:
                    # creature.perform_action(allies, enemies)
                    creature.act(allies, enemies)

                """ Count turns only for living creatures """
                if not creature.is_dead:
                    turn += 1
            world.print_coords()
            round += 1

            """ Interrupt fight at 100 rounds (e.g. if two creatures
            are left and they cannot kill each other """
            if round == 100:
                break

        world.Map.reset_map()

        if self.party1.is_alive and self.party2.is_alive:
            messages.IO.printmsg("\nDraw!", level=1)
            return "No-one"

        elif self.party1.is_alive:
            messages.IO.printmsg("\n%s wins!" % self.party1.name, level=1)
            return self.party1.name
        else:
            messages.IO.printmsg("\n%s wins!" % self.party2.name, level=1)
            return self.party2.name


#for name, value in sorted(globals().copy().items()):
#    if isinstance(value, BaseCreature):
#        print(name)

matches = 1

i = 0
results = []
messages.VERBOSE_LEVEL = 4

statisticsA = defaultdict(list)
statisticsB = defaultdict(list)

stat_order = ['avg. lifetime', 'avg. dmg', 'kills', 'deaths', 'suicides', 'hits', 'misses']

while i < matches:
    if i in range(0, matches, max(int(matches/10), 1)):
        print("Match %i" % i)

    team1 = Party(name='Team A')
    team1.add(copy.deepcopy(tarrasque))

    team1.set_formation((0, 3, 0))

    team2 = Party(name='Team B')
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))
    team2.add(copy.deepcopy(ogno))

    team2.set_formation((0, -3, 0))

    x = Encounter(team1, team2)

    results.append(x.fight())

    for character in team1.members:
        statisticsA[character.name].append([character.turns_alive,
                                            character.damage_dealt,
                                            character.kills,
                                            character.deaths,
                                            character.suicides,
                                            character.hits,
                                            character.misses])
    for character in team2.members:
        statisticsB[character.name].append([character.turns_alive,
                                            character.damage_dealt,
                                            character.kills,
                                            character.deaths,
                                            character.suicides,
                                            character.hits,
                                            character.misses])

    i += 1

print('\n')
x = dict(Counter(results).items())
for k, v in Counter(results).items():
    print(k, " wins:", x[k] / matches)

def tabulate(header, data, creatures):
    """ Code c"""
    row_format = "{:>15}" * (len(header) + 1)
    print(row_format.format("", *header))
    for creature, row in zip(creatures, data):
        print(row_format.format(creature, *row))
    print('\n')

print('\n')

for statistics in [statisticsA, statisticsB]:
    table = []
    keys = []
    for k, v in sorted(statistics.items()):
        printout = []
        keys.append(k)
        for i, stat in enumerate(stat_order):
            value = sum(j[i] for j in v)
            if stat.startswith('avg'):
                value = value / matches
                printout.append("%.2f" % value)
            else:
                printout.append("%i" % value)
        table.append(printout)
    tabulate(stat_order, table, keys)