#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import operator
import dice
import math
import copy
from collections import Counter
from mechanics import Ruleset as R

VERBOSE_LEVEL = 2
DIVIDER = "=" * 56
INDENT = " " * 4

class IO:

    turn = 0

    @staticmethod
    def center_and_pad(string, padding=":"):
        times = int( (72 - len(string) + 2) / 2 )
        return "{padding} {string} {padding}".format(padding=padding*times,
                                                     string=string)

    @staticmethod
    def printmsg(message, level, indent=False, print_turn=False):
        if indent:
            tab = INDENT
        else:
            tab = ""

        """ Add punctuation """
        if message[-1].isalpha():
            message += "."

        """ Set if turn number is shown in action log """
        if print_turn:
            turn = "Turn %i: " % IO.turn
        else:
            turn = ""

        if VERBOSE_LEVEL >= level:
            print(tab + turn + message)

class Actions:

    """ Base class for special creature actions and abilities """

    def __init__(self, name, dc, save, to_hit, recharge=0, **kwargs):
        self.name = name
        self.dc = dc
        self.save = save
        self.to_hit = to_hit
        self.recharge = recharge
        self.available = True
        super().__init__(**kwargs)

    def __repr__(self):
        return "%s (DC: %i) " % (self.name, self.dc)

    def check_and_recharge(self):
        if not self.available:
            if dice.roll(1, 6, 0) >= self.recharge:
                self.available = True


class Restrain(Actions):

    def use(self, creature, enemy):
        if creature.roll_hit(self.to_hit, enemy.ac):
            enemy.set_restrain(True, self.dc, self.save)
        self.available = False


class Gore(Actions):

    def __init__(self, damage, damage_type, **kwargs):
        super().__init__(**kwargs)
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type

    def use(self, creature, enemy):
        if creature.roll_hit(self.to_hit, enemy.ac):
            #self.apply_damage(self.damage, self.damage_type, enemy)
            enemy.set_prone(True)


spider_web = Restrain(name="Web", dc=11, save='str', to_hit=5, recharge=5)
minotaur_gore = Gore(name="Gore", dc=14, save='str', to_hit=6, damage=["4d8+4"], damage_type=["piercing"])


class Weapon(object):

    def __init__(self, name, damage, damage_type,
                 reach, to_hit, number_of_targets=1):
        self.name = name
        self.damage_print = damage
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type
        self.reach = reach
        self.to_hit = to_hit
        self.number_of_targets = number_of_targets

    def __repr__(self):
        dmg = []
        for i in range(0, len(self.damage)):
            dmg.append(self.damage_print[i] \
                  + " (%s)" % self.damage_type[i] \
                  + " %i ft. reach" % self.reach)
        return "{name}: {dmg}".format(name=self.name.capitalize(),
                                     dmg=", ".join(dmg))

    def use(self, source, target):
        hit, crit_multiplier, hitroll, message \
            = R.roll_hit(source, target, self.to_hit, self.name)
        
        """ Iterate all different damage types in weapon if hit """
        total_damage = []
        if hit:
            for i in range(len(self.damage)):
                dmg = self.damage[i]
                dmg_type = self.damage_type[i]
                """ Store total damage """
                total_damage.append(
                    R.roll_damage(source,target, dmg, dmg_type, crit_multiplier))


            if target.hp <= -target.max_hp:
                source.kills += 1
                msg = ". Target turns into bloody pulp!"
            elif target.hp <= 0:
                source.kills += 1
                msg = ". Target dies!"
            else:
                msg = "."

            message += ": does " + " and ".join(total_damage) \
                       + " damage" + msg + " (%i HP remaining)." % target.hp

        IO.printmsg(message, 2, indent=True, print_turn=True)

wolf_bite = Weapon('bite', ["2d4+2"], ["piercing"], 5, 4)
owlbear_beak = Weapon('beak', ["1d10+5"], ["piercing"], 5, 7)
owlbear_claws = Weapon('claws', ["2d8+5"], ["slashing"], 5, 7)
minotaur_greataxe = Weapon('greataxe', ["2d12+4"], ["slashing"], 5, 6)
spider_bite = Weapon('bite', ["1d10+2", "4d8"], ["piercing", "poison(DC:con:0.5:11)"], 5, 4)
nightmare_hooves = Weapon('hooves', ["2d8+4", "2d6"], ["bludgeoning", "fire"], 5, 6)
greatclub = Weapon('greatclub', ["3d8+6"], ["bludgeoning"], 15, 9)


class Basecreature(object):

    def __init__(self, name, cr, ac, hp, speed, scores, attacks, actions,
                 resistances=[], immunities=[]):
        self.name = name.upper()         # Enumerated name, e.g. ´wolf 3´
        self.type = name                 # Creature base-type, e.g. ´wolf´
        self.cr = cr
        self.ac = ac
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.original_scores = scores    # Save original ability scores
        self.scores = scores
        self.attacks = attacks
        self.actions = actions
        self.resistances = resistances
        self.immunities = immunities

        self.ac_bonus = 0
        self.to_hit_bonus = 0

        self.movement_points = speed
        self.initiative = int()

        self.focused_enemy = None          # Focused enemy (object)
        self.party = None                  # Belongs to this party

        self.restrained = {"state": False, "dc": 0, "save": "str"}
        self.prone = False
        self.poisoned = False

        self.damage_dealt = 0
        self.kills = 0

        self.reset_advantage()

    def __repr__(self):
        CR = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}
        indentation = " " * (20 - len(self.name))
        #scores = ' | '.join(["%s %i" % (k.upper(), v) for k, v in self.scores.items()])
        #attacks = "\n{x}".format(x=20*" ").join([x.__repr__() for x in self.attacks])
        return "%s%sAC %i | HP %i | Init %i | CR %s | Speed %i" \
               % (self.name, indentation, self.ac, self.hp,
                  self.initiative, CR.get(self.cr, str(self.cr)), self.speed)

    @property
    def is_dead(self):
        """ Creature is dead if its HP is 0 or it has any negative
        ability scores """
        #if min([i for i in self.scores.values()]) <= 0:
        #    return True
        return self.hp <= 0

    @property
    def is_restrained(self):
        return self.restrained["state"]

    @property
    def is_prone(self):
        return self.prone

    @property
    def is_poisoned(self):
        return self.poisoned

    @property
    def has_disadvantage(self):
        return any([self.is_prone, self.is_restrained, self.is_poisoned])

    def has_advantage_against(self, other):
        """ Return True if enemy is given advantage on hit rolls against
        the creature """
        return any([other.is_prone, other.is_restrained, other.is_poisoned])

    @staticmethod
    def parse_damage_type(damage_type):
        return re.sub('.*\((.+)\).*',  r'\1', damage_type).split(':')

    def get_modifier(self, ability):
        return math.floor((self.scores[ability] - 10) / 2)

    def begin_turn(self):
        """ At the beginning of each turn, perform a list of free actions
        such as standing up if prone, recharging abilities etc. """
        self.movement_points = self.speed

        """ Stand up if prone """
        if self.is_prone:
            self.set_prone(False)
            self.movement_points = math.floor(self.speed / 2)

        """ Recharge abilities """
        if self.actions:
            for action in self.actions:
                action.check_and_recharge()

    def set_restrain(self, state, dc, save):
        self.restrained["state"] = state
        self.restrained["dc"] = dc
        self.restrained["save"] = save

    def set_prone(self, state):
        self.prone = state

    def set_poison(self, state):
        self.poisoned = state

    def set_advantage(self):
        self.advantage = True
        self.disadvantage = False

    def set_disadvantage(self):
        self.disadvantage = False
        self.disadvantage = True

    def reset_advantage(self):
        self.advantage = False
        self.disadvantage = False

    def _roll_hit(self, bonus, target_ac):
        return self.roll_d20(bonus) > target_ac

    def roll_d20(self, bonus):
        return dice.roll(times=1, sides=20, bonus=bonus)

    def roll_initiative(self):
        """ Roll initiative for the creature, add decimals based
        on dexterity score and challenge rating to resolve same
        initiatives; if still same, pick random """
        dex = self.scores['dex'] / 100
        cr = self.cr / 1000
        dex_mod = self.get_modifier('dex')
        self.initiative = self.roll_d20(dex_mod) + dex + cr

    def _roll_damage(self, damage):
        times, sides, bonus = damage
        return dice.roll(times, sides, bonus)

    def check_resistances(self, damage_type, damage):
        """ Strip save DC info from damage_type """
        damage_type = re.sub('\(.+?\)', '', damage_type)
        if damage_type in self.resistances:
            damage = math.floor(damage / 2)
        if damage_type in self.immunities:
            damage = 0
        return damage

    def roll_save(self, ability):
        return self.roll_d20(self.get_modifier(ability))

    def take_ability_score_damage(self, ability_score, damage):
        self.scores[ability_score] -= damage
        ## TODO: Adjust AC, damage and hit

    def _take_damage(self, source, source_party, damage_type, damage):
        original_dmg = damage

        """ Check if applicable against save """
        if 'DC' in damage_type:
            _, ability, multiplier, dc = self.parse_damage_type(damage_type)
            if self.roll_save(ability) >= int(dc):
                damage = float(multiplier) * damage
            else:
                if damage_type.startswith('poison'):
                    self.set_disadvantage()

        damage = self.check_resistances(damage_type, damage)
        resisted = original_dmg - damage
        if resisted > 0:
            line = "(resisted %i of %i total damage)" % (resisted, original_dmg)
        else:
            line = ""

        IO.printmsg("%s (%s) does %i %s damage to %s %s" % (source.upper(), source_party, damage, damage_type, self.name.upper(), line))
        self.hp -= damage

        if self.hp <= -self.max_hp:
            IO.printmsg("%s (%s) explodes into bloody pulp" % (self.name.upper(), self.party))
        elif self.hp <= 0:
            IO.printmsg("%s (%s) dies" % (self.name.upper(), self.party))

    def set_focus(self, enemies):
        """ Set focus to some enemy and keep it unless the target dies """
        if self.focused_enemy is None:
            self.focused_enemy = enemies.get_weakest()
        elif self.focused_enemy.is_dead:
            self.focused_enemy = enemies.get_weakest()

    def perform_action(self, allies, enemies):
        """ General method for performing actions """
        if not self.is_dead:
            self.begin_turn()
            self.attack(enemies)

    def attack(self, enemies):
        """ Set focus on enemy and attack it """
        for attack in self.attacks:
            self.set_focus(enemies)
            """ Do not attack if there is no enemies left """
            if self.focused_enemy is not None:
                attack.use(self, self.focused_enemy)

        """
        for attack in self.attacks:
            enemy = Party.sort_by_value(enemies, 'hp')[0]

            hitroll = self.roll_d20(attack.to_hit)
            #line1 = "%s (%s) attacks %s with %s" % (self.name.upper(), self.party, enemy.name.upper(), attack.name)
            if hitroll > enemy.ac:
                line2 = "Hit"#"Hit: %i vs. AC %i" % (hitroll, enemy.ac)
                for i in range(len(attack.damage)):
                    enemy.take_damage(self.name,
                                      self.party,
                                      attack.damage_type[i],
                                      self.roll_damage(attack.damage[i]))
            else:
                line2 = "Miss"

                IO.printmsg(line2)"""




wolf_ = Basecreature(name='wolf', cr=0.25, ac=13, hp=11, speed=40,
                    scores={'str': 12, 'dex': 15, 'con': 12,
                               'int': 3, 'wis': 12, 'cha': 7},
                    attacks=[wolf_bite],
                    actions=[])

spider_ = Basecreature(name='spider', cr=0, ac=13, hp=11, speed=40,
                    scores={'str': 12, 'dex': 15, 'con': 12,
                               'int': 3, 'wis': 12, 'cha': 7},
                    attacks=[spider_bite],
                    actions=[spider_web])

owlbear_ = Basecreature(name='owlbear', cr=3, ac=13, hp=59, speed=40,
                    scores={'str': 20, 'dex': 12, 'con': 17,
                               'int': 3, 'wis': 12, 'cha': 7},
                    attacks=[copy.copy(owlbear_claws),
                             copy.copy(owlbear_beak)],
                    actions=[])

minotaur_ = Basecreature(name='minotaur', cr=3, ac=14, hp=76, speed=40,
                    scores={'str': 18, 'dex': 11, 'con': 16,
                               'int': 6, 'wis': 16, 'cha': 9},
                    attacks=[minotaur_greataxe],
                    actions=[minotaur_gore])

nightmare_ = Basecreature(name='nightmare', cr=3, ac=13, hp=68, speed=60,
                    scores={'str': 18, 'dex': 15, 'con': 16,
                               'int': 10, 'wis': 13, 'cha': 15},
                    immunities=['fire'],
                    attacks=[nightmare_hooves],
                    actions=[])

stone_giant_ = Basecreature(name='stone giant', cr=7, ac=17, hp=126, speed=40,
                    scores={'str': 23, 'dex': 15, 'con': 20,
                               'int': 10, 'wis': 12, 'cha': 9},
                    attacks=[copy.copy(greatclub), copy.copy(greatclub)],
                    actions=[])


class Party:

    def __init__(self, name):
        self.name = name
        self.members = []

    def add(self, creature):
        """ Add party members and roll initiatives, the party is
         ordered by initiative """
        creature.roll_initiative()
        creature.party = self.name

        """ Add number after creature name if the party has already 
        similar creature types """
        count = len([c.type for c in self.members if c.type == creature.type])
        if count > 0: creature.name = "%s %i" % (creature.name, count+1)
        self.members.append(creature)
        self.sort_by('initiative')

    def __repr__(self):
        return IO.center_and_pad(self.name) + '\n' \
               + '\n'.join([c.__repr__() for c in self.members]) + '\n'

    def __add__(self, other):
        return self.members + other.members

    @property
    def hp(self):
        """ Party's total hitpoints """
        return [c.hp for c in self.members]

    @property
    def is_alive(self):
        """ Return True if any party member is alive """
        return False in [c.is_dead for c in self.members]

    @staticmethod
    def remove_dead(party):
        return [c for c in party if not c.is_dead]

    def get_weakest(self):
        weakest = sorted(self.remove_dead(self.members),
                    key=operator.attrgetter('hp'),
                    reverse=False)
        if not weakest:
            return None
        else:
            return weakest[0]

    def get_teams(self, other, creature):
        """ Return two Party objects comprising allies and enemies
        of a given creature.
            :type other Party
            :type creature Basecreature """
        if creature in self.members:
            return self, other
        else:
            return other, self

    def combine_and_sort_by(self, other, value="name", strongest_first=True):
        """ Reorder party by given creature variable """
        all_creatures = self.members + other.members
        return sorted(all_creatures,
                      key=operator.attrgetter(value),
                      reverse=strongest_first)

    def sort_by(self, value="name", strongest_first=True):
        """ Reorder party by given creature variable """
        self.members.sort(key=operator.attrgetter(value),
                          reverse=strongest_first)

class Encounter:

    def __init__(self, party1, party2):
        self.party1 = party1
        self.party2 = party2
        self.order_of_action = party1.combine_and_sort_by(party2, "initiative")

    def fight(self):

        """ Simulate combat encounter until either of the parties has
        been killed """

        IO.printmsg(self.party1.__repr__(), 1)
        IO.printmsg(self.party2.__repr__(), 1)

        round = 1
        while self.party1.is_alive and self.party2.is_alive:
            turn = 1
            IO.printmsg("ROUND %i %s" % (round, DIVIDER), level=1)
            for creature in self.order_of_action:
                IO.turn = turn
                """ Get allies and enemies for the creature """
                allies, enemies = self.party1.get_teams(self.party2, creature)

                """ Allow only living creatures to act """
                if self.party1.is_alive and self.party2.is_alive:
                    creature.perform_action(allies, enemies)

                """ Count turns only for living creatures """
                if not creature.is_dead:
                    turn += 1
            round += 1

        if self.party1.is_alive:
            IO.printmsg("\n%s wins!" % self.party1.name, level=1)
            self.party1.sort_by('damage_dealt')
            return self.party1.name
        else:
            IO.printmsg("\n%s wins!" % self.party2.name, level=1)
            return self.party2.name

i = 0
results = []
VERBOSE_LEVEL = 2
while i < 1:
    print("Match %i" % i)
    team1 = Party(name='Team A')
    team1.add(copy.copy(wolf_))

    team2 = Party(name='Team B')
    team2.add(copy.copy(stone_giant_))

    x = Encounter(team1, team2)
    results.append(x.fight())
    i += 1

print(Counter(results).items())



"""
print('\ntoinen kuollut')
test = Party(name="testi")
test.add(copy.copy(wolf_))
print(test.is_alive)
test.add(copy.copy(dead_))
print(test.is_alive)

print('\nkumpikin kuollut')
test2 = Party(name="testi")
test2.add(copy.copy(dead_))
print(test.is_alive)
test2.add(copy.copy(dead_))
print(test2.is_alive)

print('\nkumpikin elossa')
test3 = Party(name="testi")
test3.add(copy.copy(wolf_))
print(test.is_alive)
test3.add(copy.copy(wolf_))
print(test3.is_alive)
print('\n')
print(test.is_alive and test2.is_alive, 'toinen kuollut ja kumpikin kuollut')
print(test.is_alive and test3.is_alive, 'toinen kuollut ja kumpikin elossa')
print(test.is_alive and test.is_alive, 'toinen kuollut ja toinen kuollut')
print(test3.is_alive and  test3.is_alive, 'kumpikin elossa ja kumpikin elossa')
print(test2.is_alive and test2.is_alive, 'kumpikin kuollut ja kumpikin kuollut')
print(test2.is_alive and test3.is_alive, 'kumpikin kuollut ja kumpikin elossa')

"""


'''
dwolf = 0
dowlbear = 0

i = 0
while i < 1000:

    wolf = copy.copy(minotaur_)
    owlbear = copy.copy(owlbear_)

    init_w = wolf.roll_initiative()
    init_o = owlbear.roll_initiative()

    if init_w > init_o:
        while owlbear.is_alive and wolf.is_alive:
            wolf.attack(owlbear)
            owlbear.attack(wolf)
    else:
        while owlbear.is_alive and wolf.is_alive:
            wolf.attack(owlbear)
            owlbear.attack(wolf)

    if wolf.hp <= 0:
        dowlbear += 1
    if owlbear.hp <= 0:
        dwolf += 1
    i += 1

print(dwolf, dowlbear)
'''