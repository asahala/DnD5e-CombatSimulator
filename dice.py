import random
import re

def roll(times, sides, bonus):
    return sum([random.randint(1, sides) for n in range(0, times)]) + bonus

def roll_advantage(times, sides, bonus):
    return max(roll(times, sides, bonus), roll(times, sides, bonus))

def roll_disadvantage(times, sides, bonus):
    return min(roll(times, sides, bonus), roll(times, sides, bonus))


def parse_damage(damage):

    if not damage:
        return [[0,0,0]]

    def parse(damage):
        if isinstance(damage,str):
            damage = [damage]
        for dmg in damage:
            if '+' in dmg:
                yield [int(i) for i in re.split("d|\+", dmg)]
            else:
                yield [int(i) for i in dmg.split('d') + [0]]
    return list(parse(damage))