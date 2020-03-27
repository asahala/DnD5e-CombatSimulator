#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import operator
import dice
import math
import random
import copy
import world
import messages
from collections import Counter
from weapons import Weapon
from abilities import *
from mechanics import DnDRuleset as R


class Basecreature(object):

    def __init__(self, name, size, category, cr, ac, hp, speed,
                 scores, melee_attacks, multi_attacks=[], ranged_attacks=[], actions=[],
                 speed_fly = 0,
                 saves=None,
                 passives=[],
                 resistances=[],
                 immunities=[],
                 vulnerabilities=[]):
        self.name = name.upper()  # Enumerated name, e.g. ´wolf 3´
        self.type = name  # Creature base-type, e.g. ´wolf´
        self.category = category
        self.size = size
        self.cr = cr
        self.ac = ac
        self.max_hp = hp
        self.hp = hp
        self.max_speed = {'ground': speed, 'fly': speed_fly}
        self.speed = {'ground': speed, 'fly': speed_fly}
        self.original_scores = scores
        self.scores = scores

        self.melee_attacks = melee_attacks
        self.ranged_attacks = ranged_attacks
        self.multi_attacks = multi_attacks

        self.actions = actions
        self.passives = passives

        self.resistances = resistances
        self.immunities = immunities
        self.vulnerabilities = vulnerabilities

        self.ac_bonus = 0
        self.to_hit_bonus = 0

        self.initiative = int()

        self.focused_enemy = None  # Focused enemy (object)
        self.party = None  # Belongs to this party

        self.restrained = {"state": False, "dc": 0, "save": "str"}
        self.prone = False
        self.poisoned = {"state": False, "dc": 0, "save": "con"}
        self.paralyzed = {"state": False, "dc": 0, "save": "con"}

        self.damage_dealt = 0
        self.kills = 0

        """ Assign attack types into dictionaries """
        '''
        self.attacks = {}
        if attacks:
            for index, attack in enumerate(attacks):
                if isinstance(attack, Weapon):
                    ats = [attack]
                else:
                    ats = attack
                if True in [a.ranged for a in ats]:
                    self.attacks.setdefault('ranged', []).append(attack)
                else:
                    self.attacks.setdefault('melee', []).append(attack)'''

        """ If creature is grappled, mark who's grappling """
        self.grappled = {"state": False, "dc": 0, "save": "str", "by": None}

        """ Set advantage or disadvantage to hit, ability checks or 
        saves tied to certain ability scores """
        self.advantage = {'hit': 0, 'ability': 0,
                          'str': 0, 'dex': 0, 'con': 0,
                          'int': 0, 'wis': 0, 'cha': 0}

        """ Set saving throws. Override if listed in MM """
        self.saves = saves
        self.update_saves()

        """ X, Y, Z Coordinates """
        self.position = (0,0,0)

        #TODO movement
        self.distance = 0

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
                  self.speed['ground'])

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
    def is_incapacitated(self):
        """ Conditions that prevent all actions except end turn
        saves """
        if self.paralyzed['state']:
            return True
        return False

    @property
    def is_poisoned(self):
        return self.poisoned

    @property
    def is_paralyzed(self):
        return self.paralyzed["state"]

    @property
    def has_disadvantage(self):
        return any([self.is_prone,
                    self.is_restrained,
                    self.is_poisoned])

    @property
    def gives_advantage_to_attacker(self):
        return any([self.is_prone,
                    self.is_restrained,
                    self.is_paralyzed])

    def ___has_advantage_against(self, other):
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
        """ At the beginning of each turn, perform a list of
        actions such as standing up, recharging abilities etc.

        Return True if creature did not use its action """
        self.distance = 0
        self.speed = self.max_speed.copy()

        """ Recharge abilities """
        if self.actions:
            for action in self.actions:
                action.check_and_recharge()

        """ Stand up if prone """
        if self.is_prone:
            self.set_prone(False)
            self.speed['fly'] = math.floor(self.speed['fly'] / 2)
            self.speed['ground'] = math.floor(self.speed['ground'] / 2)

        """ Free from grapple if grappler has died """
        if self.grappled["state"]:
            self.speed['fly'] = 0
            self.speed['ground'] = 0
            if self.grappled["by"].is_dead:
                self.set_grapple(state=False, dc=0, save='str', source=None)

        if self.paralyzed["state"]:
            self.speed['fly'] = 0
            self.speed['ground'] = 0

        if self.restrained["state"]:
            self.speed['fly'] = 0
            self.speed['ground'] = 0
            dc = self.restrained["dc"]
            ability = self.restrained['save']
            if R.roll_save(self, ability, dc):
                self.set_restrain(False, dc=0, save=None)
                return False

        return True

    def end_turn(self):
        """ Reroll save against paralysis  """
        if self.is_paralyzed:
            dc = self.paralyzed["dc"]
            ability = self.paralyzed['save']
            if R.roll_save(self, ability, dc):
                self.set_paralysis(False, dc=0, save=None)

    def take_damage(self, source, damage, dmg_type, crit_multiplier):

        """ Check if creature has vulnerability, resistance or immunity
            to the given damage type """
        damage = self.check_resistances(dmg_type, damage)
        damage = self.check_vulnerabilities(dmg_type, damage)

        """ Store damage statistics """
        source.damage_dealt += damage

        self.hp -= damage

        messages.IO.total_damage.setdefault(dmg_type, 0)
        messages.IO.total_damage[dmg_type] += damage
        messages.IO.hp = self.hp
        messages.IO.target_name = self.name
        messages.IO.printlog()
        """ Check if creature can drop to 1 HP instead of 0 """
        if self.hp <= 0 and self.passives:
            for passive in self.passives:
                if passive.type == 'avoid_death':
                    self.hp = passive.use(self, damage, dmg_type, crit_multiplier)

        if self.is_dead:
            messages.IO.printmsg("-> %s is dead. " % self.name, 2, True, False)

    def set_grapple(self, state, dc=0, save='str', source=None):
        if state:
            messages.IO.printmsg("-> %s is restrained. " % self.name, 2, True, False)
            self.set_advantage('hit', -1)
            self.set_advantage('dex', -1)
            self.speed['fly'] = 0
            self.speed['ground'] = 0
        else:
            messages.IO.printmsg("%s frees from restrain. " % self.name, 2, True, False)
            self.set_advantage('hit', 0)
            self.set_advantage('dex', 0)
            self.speed = self.max_speed.copy()
        self.grappled["state"] = state
        self.grappled["dc"] = dc
        self.grappled["save"] = save
        self.grappled["by"] = source

    def set_restrain(self, state, dc=0, save='str'):
        if state:
            messages.IO.printmsg("-> %s is restrained. " % self.name, 2, True, False)
            self.set_advantage('hit', -1)
            self.set_advantage('dex', -1)
            self.speed['ground'] = 0
            self.speed['fly'] = 0
        else:
            messages.IO.printmsg("%s frees from restrain. " % self.name, 2, True, False)
            self.set_advantage('hit', 0)
            self.set_advantage('dex', 0)
            self.speed = self.max_speed.copy()
        self.restrained["state"] = state
        self.restrained["dc"] = dc
        self.restrained["save"] = save

    def set_paralysis(self, state, dc=0, save='str'):
        if not "paralysis" in self.immunities:
            if state:
                messages.IO.printmsg("-> %s is paralyzed. " % self.name, 2, True, False)
                self.speed['ground'] = 0
                self.speed['fly'] = 0
            else:
                messages.IO.printmsg("%s recovers from paralysis. " % self.name, 2, True, True)
                self.speed = self.max_speed.copy()
            self.paralyzed["state"] = state
            self.paralyzed["dc"] = dc
            self.paralyzed["save"] = save

    def set_prone(self, state):
        if state:
            #messages.IO.conditions.append("-> %s falls prone. " % self.name)
            messages.IO.printmsg("-> %s falls prone. " % self.name, 2, True, False)
            self.set_advantage('hit', -1)
        else:
            #messages.IO.conditions.append("%s stands up. " % self.name)
            messages.IO.printmsg("%s stands up. " % self.name, 2, True, True)
            self.set_advantage('hit', 0)

        self.prone = state

    def set_poison(self, state, dc=0, save='con'):
        if not 'poison' in self.immunities:
            if state:
                messages.IO.printmsg("-> %s is poisoned. " % self.name, 2, True, False)
                self.set_advantage('hit', -1)
            else:
                self.set_advantage('hit', 0)
                messages.IO.printmsg("%s recovers from poison. " % self.name, 2, True, True)
            self.poisoned["state"] = state
            self.poisoned["dc"] = dc
            self.poisoned["save"] = save

    def set_advantage(self, category, state):
        """ Give advantage or disadvantage to a certain category
        :param category    hit, save, ability
        :param state       -1, 0, 1 """

        if state == -1:
            self.advantage[category] =\
                max(self.advantage[category] + state, state)
        elif state == 1:
            self.advantage[category] =\
                min(self.advantage[category] + state, state)
        else:
            self.advantage[category] = 0

    def roll_initiative(self):
        """ Roll initiative for the creature, add decimals based
        on dexterity score and challenge rating to resolve equal rolls """
        dex = self.scores['dex'] / 100
        cr = self.cr / 1000
        dex_mod = self.get_modifier('dex')
        self.initiative = dice.roll(1, 20, dex_mod) + dex + cr

    def check_resistances(self, damage_type, damage):
        """ Strip save DC info from damage_type """
        damage_type = re.sub('\(.+?\)', '', damage_type)
        if damage_type in self.resistances:
            damage = math.floor(damage / 2)
        if damage_type in self.immunities:
            damage = 0

        return damage

    def check_vulnerabilities(self, damage_type, damage):
        """ Strip save DC info from damage_type """
        damage_type = re.sub('\(.+?\)', '', damage_type)
        if damage_type in self.vulnerabilities:
            return damage * 2
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
                if passive.type == 'on_start':
                    passive.use(self, allies, enemies)

    def move(self, enemy, weapon):
        A = self.position
        B = enemy.position
        distance = world.get_dist(A, B)

        if distance > weapon.reach:
            """ If not at reach, close distance """
            path = world.get_path(A, B)
            #print(distance, weapon.reach)
            #print(self.name, A, '::::', enemy.name, B)
            #print(path)
            if distance > self.speed['ground'] + weapon.reach:
                """ Run if can't get to range by moving regularly. 
                Return False as action points spent on moving  """
                points, new_pos = world.close_distance(self, path, weapon.reach, run=True)
                return False
            else:
                points, new_pos = world.close_distance(self, path, weapon.reach)
        elif distance < weapon.reach and weapon.ranged:
            """ If using ranged weapon, keep distance """
            path = world.get_opposite(A, B, self)
            points, new_pos = world.keep_distance(self, enemy, path, weapon.reach)

        if world.get_dist(self.position, B) <= weapon.reach:
            return True
        else:
            return False

    def select_weapon(self, enemies):

        def pick():
            attacks = []
            min_distance = 0
            for weapon in self.melee_attacks:
                if isinstance(weapon, list):
                    for subweapon in weapon:
                        if subweapon.special:
                            attacks = [weapon]
                            min_distance = weapon.min_distance
                else:
                    if weapon.special:
                        attacks = [weapon]
                        min_distance = weapon.min_distance
            return attacks, min_distance

        """ Priority 1: Use a weapon with special ability """
        attacks, min_distance = pick()

        """ Override priority: If ranged weapon is available, use it """
        if self.ranged_attacks:
            opts = [a for a in self.ranged_attacks if a.ammo > 0]
            if opts:
                attacks = opts
            else:
                attacks = self.melee_attacks

        """ If not chosen yet, pick one melee attack """
        if not attacks:
            attacks = self.melee_attacks

        """ Override choice if next to enemy """
        for e in enemies.members:
            if world.is_adjacent(self.position, e.position):
                if isinstance(attacks[0], list):
                    pass
                else:
                    attacks = [x for x in self.melee_attacks if x.min_distance <= 5]
                break

        return random.choice(attacks)

    def perform_action(self, allies, enemies):
        """ General method for performing actions """
        if not self.is_dead:
            if not self.is_incapacitated:
                may_act = self.begin_turn()
                self.check_passives(allies, enemies)
                self.attack(enemies)
            self.end_turn()

    def attack(self, enemies):
        """ Set focus on enemy and attack it """
        if self.melee_attacks or self.ranged_attacks:
            attacks = self.select_weapon(enemies)
            if isinstance(attacks, Weapon):
                attacks = [attacks]
            for attack in attacks:
                """ Always set new focus in case the enemy dies """
                self.set_focus(enemies)
                if self.focused_enemy is not None:
                    """ Do not attack or move if there are no enemies left """
                    at_range = self.move(self.focused_enemy, attack)
                    if at_range:
                        attack.use(self, self.focused_enemy)
                        attack.ammo -= 1


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

    def set_formation(self, position):
        """ Sets party in formation near given coordinates """
        x, y, z = position
        i = 1
        for creature in self.members:
            j = dice.roll(1,2,-1)
            if i % 2 == 0:
                k = -i
            else:
                k = i
            creature.position = (x+k, y+j, z)
            world.occupied.append([creature.position, creature.name])
            i += 1

spider_web = Restrain(name="Web", dc=11, save='str', to_hit=5, recharge=5)
#minotaur_gore = Gore(name="Gore", dc=14, save='str', to_hit=6, damage=["4d8+4"], damage_type=["piercing"])
pack_tactics = PackTactics

wolf_bite = Weapon(name='bite',
                   damage=["2d4+2"],
                   damage_type=["piercing"],
                   reach=5,
                   to_hit=7,
                   special=[Knockdown(name="bite",
                                      dc=11,
                                      save='str')])

giant_spider_bite = Weapon(name='bite', damage=["1d8+3"],
                           damage_type=["piercing"],
                           reach=5,
                           to_hit=5,
                           special=[Poison(name='bite',
                                           dc=11,
                                           save='con',
                                           damage=['2d8'],
                                           success=0.5,
                                           damage_type=['poison'])])

dire_wolf_bite = Weapon(name='bite',
                        damage=["2d6+3"],
                        damage_type=["piercing"],
                        reach=5,
                        to_hit=5,
                        special=[Knockdown(name="bite",
                                           dc=13,
                                           save='str')])

crocodile_bite = Weapon(name='bite',
                        damage=["1d10+2"],
                        damage_type=["piercing"],
                        reach=5,
                        to_hit=4,
                        special=[Grapple(name='bite', dc=15, save='str')])

lion_bite = Weapon(name='bite',
                   damage=["1d8+3"],
                   damage_type=["piercing"],
                   reach=5,
                   to_hit=5)

lion_claw = Weapon(name='claw',
                   damage=["1d6+3"],
                   damage_type=["slashing"],
                   reach=5,
                   to_hit=5)

lion_pounce = Weapon(name='pounce',
                     damage=["1d6+3"],
                     damage_type=["slashing"],
                     reach=5,
                     min_distance=20,
                     to_hit=5,
                     special=[Knockdown(name="pounce", dc=13, save='str',
                                        charge_distance=20,
                                        bonus_action=lion_bite)])

mammoth_trample = Weapon(name='trample',
                         damage=["4d10+7"],
                         damage_type=["bludgeoning"],
                         reach=5,
                         to_hit=10)

mammoth_gore = Weapon(name='gore',
                      damage=["4d8+7"],
                      damage_type=["piercing"],
                      reach=10,
                      to_hit=10,
                      special=[Knockdown(name="trampling charge", dc=18, save='str',
                                         charge_distance=20,
                                         bonus_action=mammoth_trample)])

ghoul_bite = Weapon(name='bite',
                    damage=["2d6+2"],
                    damage_type=["piercing"],
                    reach=5,
                    to_hit=2)

ghoul_claw = Weapon(name='claws',
                    damage=["2d4+2"],
                    damage_type=["slashing"],
                    reach=5,
                    to_hit=4,
                    special=[Paralysis(name='claws', dc=10, save='con')])

owlbear_beak = Weapon('beak', ["1d10+5"], ["piercing"], 5, 7)
owlbear_claws = Weapon('claws', ["2d8+5"], ["slashing"], 5, 7)
minotaur_greataxe = Weapon('greataxe', ["2d12+4"], ["slashing"], 5, 6)
nightmare_hooves = Weapon('hooves', ["2d8+4", "2d6"], ["bludgeoning", "fire"], 5, 6)
greatclub = Weapon('greatclub', ["3d8+6"], ["bludgeoning"], 15, 9)

bat = Basecreature(name='bat', cr=0, ac=12, hp=1, speed=30,
                   size='tiny',
                   category="beast",
                   scores={'str': 2, 'dex': 15, 'con': 8,
                           'int': 2, 'wis': 12, 'cha': 4},
                   melee_attacks=[Weapon(name='bite',
                                   damage=["1d1"],
                                   damage_type=["piercing"],
                                   reach=5,
                                   to_hit=0)])

black_bear = Basecreature(name='black bear', cr=0.5, ac=11, hp=19, speed=40,
                          size='medium',
                          category="beast",
                          scores={'str': 15, 'dex': 10, 'con': 14,
                                  'int': 2, 'wis': 12, 'cha': 7},
                          melee_attacks=[[Weapon(name='bite', damage=["1d6+2"], damage_type=["piercing"], reach=5, to_hit=3),
                                    Weapon(name='claws', damage=["2d4+2"], damage_type=["slashing"], reach=5,
                                           to_hit=3)]])

brown_bear = Basecreature(name='brown bear', cr=1, ac=11, hp=34, speed=40,
                          size='large',
                          category="beast",
                          scores={'str': 19, 'dex': 10, 'con': 16,
                                  'int': 2, 'wis': 13, 'cha': 7},
                          melee_attacks=[
                              [Weapon(name='bite',
                                      damage=["1d8+4"],
                                      damage_type=["piercing"],
                                      reach=5,
                                      to_hit=5),
                               Weapon(name='claws',
                                      damage=["2d6+4"],
                                      damage_type=["slashing"],
                                      reach=5,
                                      to_hit=5)]
                          ])

crocodile = Basecreature(name='crocodile', cr=0.5, ac=12, hp=19, speed=20,
                         size='large',
                         category="beast",
                         scores={'str': 15, 'dex': 10, 'con': 13,
                                 'int': 2, 'wis': 10, 'cha': 5},
                         melee_attacks=[crocodile_bite])

dire_wolf = Basecreature(name='dire wolf', cr=1, ac=14, hp=37, speed=50,
                         size='large',
                         category="beast",
                         scores={'str': 17, 'dex': 15, 'con': 15,
                                 'int': 3, 'wis': 12, 'cha': 7},
                         melee_attacks=[dire_wolf_bite])

wolf = Basecreature(name='wolf', cr=0.25, ac=13, hp=11, speed=40,
                    size='medium',
                    category="beast",
                    scores={'str': 12, 'dex': 15, 'con': 12,
                            'int': 3, 'wis': 12, 'cha': 7},
                    melee_attacks=[wolf_bite],
                    actions=[],
                    passives=[pack_tactics])

lion = Basecreature(name='lion', cr=1, ac=12, hp=26, speed=50,
                    size='large',
                    category="beast",
                    scores={'str': 17, 'dex': 15, 'con': 13,
                            'int': 3, 'wis': 12, 'cha': 8},
                    melee_attacks=[lion_pounce, lion_bite, lion_claw],
                    passives=[pack_tactics])

mammoth = Basecreature(name='mammoth', cr=6, ac=13, hp=126, speed=40,
                       size='huge',
                       category="beast",
                       scores={'str': 24, 'dex': 9, 'con': 21,
                               'int': 3, 'wis': 11, 'cha': 6},
                       melee_attacks=[mammoth_gore])

skeleton = Basecreature(name='skeleton', cr=0.25, ac=13, hp=13, speed=30,
                        size='medium',
                        category="undead",
                        scores={'str': 10, 'dex': 14, 'con': 15,
                                'int': 6, 'wis': 8, 'cha': 5},
                        immunities=['poison', 'paralysis'],
                        vulnerabilities=['bludgeoning'],
                        melee_attacks=[
                            Weapon(name='shortsword', damage=["1d6+2"],
                                   damage_type=["slashing"], reach=5, to_hit=4)],
                        ranged_attacks=[
                            Weapon(name='shortbow', damage=["1d6+2"],
                            damage_type=["piercing"], ammo=20, ranged=True, reach=80, to_hit=4)
                        ])

zombie = Basecreature(name='zombie', cr=0.25, ac=8, hp=22, speed=20,
                      size='medium',
                      category="undead",
                      scores={'str': 13, 'dex': 6, 'con': 16,
                              'int': 3, 'wis': 6, 'cha': 5},
                      saves={'wis': 0},
                      immunities=['poison', 'paralysis'],
                      melee_attacks=[Weapon(name='slam',
                                      damage=["1d6+1"],
                                      damage_type=["bludgeoning"],
                                      reach=5,
                                      to_hit=3)],
                      passives=[AvoidDeath(name="Undead Fortitude",
                                           save='con',
                                           minimum_hp=1)])

ghoul = Basecreature(name='ghoul', cr=1, ac=12, hp=22, speed=30,
                     size='medium',
                     category="undead",
                     scores={'str': 13, 'dex': 15, 'con': 10,
                             'int': 7, 'wis': 10, 'cha': 6},
                     immunities=['poison', 'paralysis'],
                     melee_attacks=[ghoul_bite, ghoul_claw])

giant_spider = Basecreature(name='giant spider', cr=1, ac=14, hp=26, speed=30,
                            size='large',
                            category='beast',
                            scores={'str': 14, 'dex': 16, 'con': 12,
                                    'int': 2, 'wis': 11, 'cha': 4},
                            melee_attacks=[giant_spider_bite],
                            actions=[])

owlbear = Basecreature(name='owlbear', cr=3, ac=13, hp=59, speed=40,
                       size='medium',
                       category="beast",
                       scores={'str': 20, 'dex': 12, 'con': 17,
                               'int': 3, 'wis': 12, 'cha': 7},
                       melee_attacks=[[owlbear_claws, owlbear_beak]],
                       actions=[])

minotaur = Basecreature(name='minotaur', cr=3, ac=14, hp=76, speed=40,
                        size='medium',
                        category="beast",
                        scores={'str': 18, 'dex': 11, 'con': 16,
                                'int': 6, 'wis': 16, 'cha': 9},
                        melee_attacks=[minotaur_greataxe])

nightmare = Basecreature(name='nightmare', cr=3, ac=13, hp=68, speed=60,
                         size='medium',
                         category="beast",
                         scores={'str': 18, 'dex': 15, 'con': 16,
                                 'int': 10, 'wis': 13, 'cha': 15},
                         immunities=['fire'],
                         melee_attacks=[nightmare_hooves],
                         actions=[])

stone_giant = Basecreature(name='stone giant', cr=7, ac=17, hp=126, speed=40,
                           size='medium',
                           category='???',
                           scores={'str': 23, 'dex': 15, 'con': 20,
                                   'int': 10, 'wis': 12, 'cha': 9},
                           saves={'str': 10},
                           melee_attacks=[copy.copy(greatclub), copy.copy(greatclub)],
                           actions=[])

dummy = Basecreature(name='dummy', cr=7, ac=10, hp=126, speed=40,
                     size='medium',
                     category='dummy',
                     scores={'str': 11, 'dex': 15, 'con': 11,
                             'int': 10, 'wis': 12, 'cha': 9},
                     saves={'str': 0},
                     melee_attacks=[])


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
        world.occupied = []

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
                    world.occupied.append([creature.position, creature.name])
                else:
                    world.occupied.append([creature.position, ' † '])

            world.print_coords()
            world.occupied = []

            round += 1

        if self.party1.is_alive:
            messages.IO.printmsg("\n%s wins!" % self.party1.name, level=1)
            self.party1.sort_by('damage_dealt')
            return self.party1.name
        else:
            messages.IO.printmsg("\n%s wins!" % self.party2.name, level=1)
            return self.party2.name

        # TODO better: draw end state
        for creature in self.order_of_action:
            if not creature.is_dead:
                world.occupied.append([creature.position, creature.name])
            else:
                world.occupied.append([creature.position, ' † '])

        world.print_coords()
        world.occupied = []

i = 0
results = []
messages.VERBOSE_LEVEL = 3
while i < 1:
    print("Match %i" % i)
    team1 = Party(name='Team A')
    team1.add(copy.deepcopy(black_bear))
    team1.add(copy.deepcopy(brown_bear))
    team1.set_formation((0,3,0))


    team2 = Party(name='Team B')
    team2.add(copy.deepcopy(minotaur))
    team2.set_formation((0,-3,0))


    x = Encounter(team1, team2)

    results.append(x.fight())
    i += 1

print(Counter(results).items())
