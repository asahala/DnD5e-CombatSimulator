#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import operator
import dice
import math
import random
import copy
import messages
from collections import Counter
from weapons import Weapon
from abilities import *

class Basecreature(object):

    def __init__(self, name, size, cr, ac, hp, speed,
                 scores, attacks, actions,
                 saves=None,
                 passives=[],
                 resistances=[],
                 immunities=[]):
        self.name = name.upper()  # Enumerated name, e.g. ´wolf 3´
        self.type = name  # Creature base-type, e.g. ´wolf´
        self.size = size
        self.cr = cr
        self.ac = ac
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.original_scores = scores
        self.scores = scores
        self.attacks = attacks
        self.actions = actions
        self.passives = passives

        self.resistances = resistances
        self.immunities = immunities

        self.ac_bonus = 0
        self.to_hit_bonus = 0

        self.movement_points = speed
        self.initiative = int()

        self.focused_enemy = None  # Focused enemy (object)
        self.party = None  # Belongs to this party

        self.restrained = {"state": False, "dc": 0, "save": "str"}
        self.prone = False
        self.poisoned = {"state": False, "dc": 0, "save": "con"}

        self.damage_dealt = 0
        self.kills = 0

        """ Set advantage or disadvantage to hit, ability checks or 
        saves tied to certain ability scores """
        self.advantage = {'hit': 0, 'ability': 0,
                          'str': 0, 'dex': 0, 'con': 0,
                          'int': 0, 'wis': 0, 'cha': 0}

        """ Set saving throws. Override if listed in MM """
        self.saves = saves
        self.update_saves()

        """ X, Y Coordinates """
        self.position = []

    def __repr__(self):
        CR = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}
        indentation = " " * (20 - len(self.name))
        # scores = ' | '.join(["%s %i" % (k.upper(), v) for k, v in self.scores.items()])
        # attacks = "\n{x}".format(x=20*" ").join([x.__repr__() for x in self.attacks])
        return "%s%sAC %i | HP %i | Init %i | CR %s | Speed %i" \
               % (self.name,
                  indentation,
                  self.ac,
                  self.hp,
                  self.initiative,
                  CR.get(self.cr, str(self.cr)),
                  self.speed)

    def update_saves(self):
        """ Replace ability score based saving throws with fixed
         values given in Monster Manual"""
        if self.saves is None:
            self.saves = {k: self.get_modifier(v)
                          for k, v in self.scores.items()}
        else:
            for k, v in self.scores.items():
                v2 = self.saves.get(k, 0)
                self.saves[k] = max(self.get_modifier(v), v2)

    # ==================================================================
    # Creature conditions
    # ==================================================================

    @property
    def is_dead(self):
        """ Creature is dead if its HP is 0 or it has any negative
        ability scores """
        # if min([i for i in self.scores.values()]) <= 0:
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
        return any([self.is_prone,
                    self.is_restrained,
                    self.is_poisoned])

    def has_advantage_against(self, other):
        """ Return True if enemy is given advantage on hit rolls against
        the creature """
        return any([other.is_prone,
                    other.is_restrained,
                    other.is_poisoned])

    # ==================================================================
    #
    # ==================================================================

    def get_modifier(self, ability):
        if isinstance(ability, int):
            return math.floor((ability - 10) / 2)
        return math.floor((self.scores[ability] - 10) / 2)

    def begin_turn(self):
        """ At the beginning of each turn, perform a list of free
        actions such as standing up, recharging abilities etc. """
        self.movement_points = self.speed

        """ Stand up if prone """
        if self.is_prone:
            self.set_prone(False)
            self.movement_points = math.floor(self.speed / 2)

        """ Recharge abilities """
        if self.actions:
            for action in self.actions:
                action.check_and_recharge()

    def set_restrain(self, state, dc=0, save='str'):
        if state:
            self.set_advantage('hit', 0)
            self.set_advantage('dex', 0)
        else:
            self.set_advantage('hit', -1)
            self.set_advantage('dex', -1)
        self.restrained["state"] = state
        self.restrained["dc"] = dc
        self.restrained["save"] = save

    def set_prone(self, state):
        if state:
            messages.IO.printmsg("-> %s falls prone. " % self.name, 2, True, False)
        else:
            messages.IO.printmsg("%s stands up. " % self.name, 2, True, True)
        self.set_advantage('hit', -1)
        self.prone = state

    def set_poison(self, state, dc=0, save='con'):
        if state:
            messages.IO.printmsg("-> %s is poisoned. " % self.name, 2, True, False)
            self.set_advantage('hit', 0)
        else:
            self.set_advantage('hit', -1)
            messages.IO.printmsg("%s recovers from poison. " % self.name, 2, True, True)
        self.poisoned["state"] = state
        self.poisoned["dc"] = dc
        self.poisoned["save"] = save

    def set_advantage(self, category, state):
        """ Give advantage or disadvantage on a certain category
        :param category    hit, save, ability
        :param state       -1, 0, 1
        """
        if state == -1:
            self.advantage[category] = \
                max(self.advantage[category] + state, -1)
        elif state == 1:
            self.advantage[category] = \
                min(self.advantage[category] + state, 1)
        else:
            self.advantage[category] = 0

    def roll_initiative(self):
        """ Roll initiative for the creature, add decimals based
        on dexterity score and challenge rating to resolve same
        initiatives; if still same, pick random """
        dex = self.scores['dex'] / 100
        cr = self.cr / 1000
        dex_mod = self.get_modifier('dex')
        self.initiative = dice.roll(times=1, sides=20, bonus=dex_mod) + dex + cr

    def check_resistances(self, damage_type, damage):
        """ Strip save DC info from damage_type """
        damage_type = re.sub('\(.+?\)', '', damage_type)
        if damage_type in self.resistances:
            damage = math.floor(damage / 2)
        if damage_type in self.immunities:
            damage = 0
        return damage

    def take_ability_score_damage(self, ability_score, damage):
        self.scores[ability_score] -= damage
        ## TODO: Adjust AC, damage and hit

    def set_focus(self, enemies):
        """ Set focus to some enemy and keep it unless the target dies """
        if self.focused_enemy is None:
            self.focused_enemy = enemies.get_weakest()
        elif self.focused_enemy.is_dead:
            self.focused_enemy = enemies.get_weakest()

    def check_passives(self, allies, enemies):
        """ Check passive skills """
        if self.passives:
            for passive in self.passives:
                passive.use(self, allies, enemies)

    def perform_action(self, allies, enemies):
        """ General method for performing actions; reset action
         log at the beginning of creature's turn """
        if not self.is_dead:
            self.begin_turn()
            self.check_passives(allies, enemies)
            self.attack(enemies)

    def attack(self, enemies):
        """ Set focus on enemy and attack it """
        if self.attacks:
            attacks = random.choice(self.attacks)
            if isinstance(attacks, Weapon):
                attacks = [attacks]
            for attack in attacks:
                self.set_focus(enemies)
                """ Do not attack if there is no enemies left """
                if self.focused_enemy is not None:
                    attack.use(self, self.focused_enemy)



spider_web = Restrain(name="Web", dc=11, save='str', to_hit=5, recharge=5)
minotaur_gore = Gore(name="Gore", dc=14, save='str', to_hit=6, damage=["4d8+4"], damage_type=["piercing"])
pack_tactics = PackTactics

wolf_bite = Weapon(name='bite',
                   damage=["2d4+2"],
                   damage_type=["piercing"],
                   reach=5,
                   to_hit=7,
                   special=[Knockdown(name="bite",
                                      dc=11,
                                      save='str')])

spider_bite = Weapon(name='bite', damage=["1d10+2"],
                     damage_type=["piercing"],
                     reach=5,
                     to_hit=4,
                     special=[Poison(name='bite',
                                     dc=11,
                                     save='con',
                                     damage=['4d8'],
                                     success=0.5,
                                     damage_type=['poison'])])

owlbear_beak = Weapon('beak', ["1d10+5"], ["piercing"], 5, 7)
owlbear_claws = Weapon('claws', ["2d8+5"], ["slashing"], 5, 7)
minotaur_greataxe = Weapon('greataxe', ["2d12+4"], ["slashing"], 5, 6)
nightmare_hooves = Weapon('hooves', ["2d8+4", "2d6"], ["bludgeoning", "fire"], 5, 6)
greatclub = Weapon('greatclub', ["3d8+6"], ["bludgeoning"], 15, 9)

wolf_ = Basecreature(name='wolf', cr=0.25, ac=13, hp=11, speed=40,
                     size='medium',
                     scores={'str': 12, 'dex': 15, 'con': 12,
                             'int': 3, 'wis': 12, 'cha': 7},
                     attacks=[wolf_bite],
                     actions=[],
                     passives=[pack_tactics])

spider_ = Basecreature(name='spider', cr=0.25, ac=13, hp=11, speed=40,
                       size='medium',
                       scores={'str': 12, 'dex': 15, 'con': 12,
                               'int': 3, 'wis': 12, 'cha': 7},
                       attacks=[spider_bite],
                       actions=[])

owlbear_ = Basecreature(name='owlbear', cr=3, ac=13, hp=59, speed=40,
                        size='medium',
                        scores={'str': 20, 'dex': 12, 'con': 17,
                                'int': 3, 'wis': 12, 'cha': 7},
                        attacks=[[owlbear_claws, owlbear_beak]],
                        actions=[])

minotaur_ = Basecreature(name='minotaur', cr=3, ac=14, hp=76, speed=40,
                         size='medium',
                         scores={'str': 18, 'dex': 11, 'con': 16,
                                 'int': 6, 'wis': 16, 'cha': 9},
                         attacks=[minotaur_greataxe],
                         actions=[minotaur_gore])

nightmare_ = Basecreature(name='nightmare', cr=3, ac=13, hp=68, speed=60,
                          size='medium',
                          scores={'str': 18, 'dex': 15, 'con': 16,
                                  'int': 10, 'wis': 13, 'cha': 15},
                          immunities=['fire'],
                          attacks=[nightmare_hooves],
                          actions=[])

stone_giant_ = Basecreature(name='stone giant', cr=7, ac=17, hp=126, speed=40,
                            size='medium',
                            scores={'str': 23, 'dex': 15, 'con': 20,
                                    'int': 10, 'wis': 12, 'cha': 9},
                            saves={'str': 10},
                            attacks=[copy.copy(greatclub), copy.copy(greatclub)],
                            actions=[])

dummy_ = Basecreature(name='dummy', cr=7, ac=10, hp=126, speed=40,
                      size='medium',
                      scores={'str': 11, 'dex': 15, 'con': 11,
                              'int': 10, 'wis': 12, 'cha': 9},
                      saves={'str': 0},
                      attacks=[],
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
        if count > 0: creature.name = "%s %i" % (creature.name, count + 1)
        self.members.append(creature)
        self.sort_by('initiative')

    def __repr__(self):
        return messages.IO.center_and_pad(self.name) + '\n' \
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

        DIVIDER = "=" * 70

        """ Simulate combat encounter until either of the parties has
        been killed """

        messages.IO.printmsg(self.party1.__repr__(), 1)
        messages.IO.printmsg(self.party2.__repr__(), 1)

        round = 1
        while self.party1.is_alive and self.party2.is_alive:
            turn = 1
            messages.IO.printmsg("\nROUND %i %s\n" % (round, DIVIDER), level=1, indent=False)
            for creature in self.order_of_action:
                messages.IO.turn = "%i (%s)" % (turn, creature.party)
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
            messages.IO.printmsg("\n%s wins!" % self.party1.name, level=1)
            self.party1.sort_by('damage_dealt')
            return self.party1.name
        else:
            messages.IO.printmsg("\n%s wins!" % self.party2.name, level=1)
            return self.party2.name


i = 0
results = []
messages.VERBOSE_LEVEL = 2
while i < 1:
    print("Match %i" % i)
    team1 = Party(name='Team A')
    team1.add(copy.copy(owlbear_))

    team2 = Party(name='Team B')
    team2.add(copy.copy(wolf_))
    team2.add(copy.copy(wolf_))
    team2.add(copy.copy(wolf_))
    team2.add(copy.copy(spider_))

    x = Encounter(team1, team2)
    results.append(x.fight())
    i += 1

print(Counter(results).items())
